# accounts/views.py

from collections import Counter
from datetime import timedelta
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core import signing
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from students.models import StudentProfile
from students.forms import StudentProfileForm
from employers.models import EmployerProfile
from employers.forms import EmployerProfileForm

from internships.models import InternshipOpportunity, Application

from notifications.models import Notification, EmailLog
from notifications.email_service import get_active_email_config, send_system_email
from notifications.sms_service import send_registration_otp_sms
from notifications.whatsapp_service import send_registration_otp_whatsapp

from .forms import StudentRegistrationForm, EmployerRegistrationForm, OTPVerificationForm
from .models import User


logger = logging.getLogger(__name__)

REGISTRATION_VERIFY_SALT = "accounts.registration.verify"
REGISTRATION_VERIFY_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def is_mobile_device(request):
    """Detect if the request comes from a mobile device"""
    user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
    mobile_keywords = ["mobile", "android", "iphone", "ipad", "ipod", "blackberry", "windows phone", "samsung", "xiaomi"]
    return any(keyword in user_agent for keyword in mobile_keywords)


def clean_login_value(value, is_password=False):
    """Cleans username/email from mobile keyboards"""
    if value is None:
        return ""

    value = str(value)
    for char in ["\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"]:
        value = value.replace(char, "")

    if not is_password:
        value = value.strip()

    return value


def get_username_from_identifier(identifier):
    """Get username from email or username input"""
    identifier = clean_login_value(identifier)
    if not identifier:
        return ""

    if "@" in identifier:
        user_obj = User.objects.filter(email__iexact=identifier).first()
    else:
        user_obj = User.objects.filter(username__iexact=identifier).first()

    if user_obj:
        return user_obj.get_username()
    return identifier


def has_student_profile(user):
    """Check if user has student profile"""
    return hasattr(user, 'studentprofile')


def has_employer_profile(user):
    """Check if user has employer profile"""
    return hasattr(user, 'employerprofile')


def get_dashboard_redirect_name(user):
    """Get redirect URL based on user role and profile status"""
    if user.role == "student":
        if not has_student_profile(user):
            return "create_student_profile"
        return "student_dashboard"

    if user.role == "employer":
        if not has_employer_profile(user):
            return "create_employer_profile"
        return "employer_profile"

    return "dashboard"


def build_public_url(path):
    """Build absolute URL for the site"""
    public_site_url = getattr(settings, "PUBLIC_SITE_URL", "https://ai-attachment-system.onrender.com").rstrip("/")
    return f"{public_site_url}{path}"


def build_absolute_url(request, view_name, *args):
    """Build absolute URL from request"""
    path = reverse(view_name, args=args)
    public_site_url = getattr(settings, "PUBLIC_SITE_URL", "").rstrip("/")
    if public_site_url:
        return f"{public_site_url}{path}"
    return request.build_absolute_uri(path)


def home(request):
    context = {
        "total_students": StudentProfile.objects.count(),
        "total_employers": EmployerProfile.objects.count(),
        "total_opportunities": InternshipOpportunity.objects.count(),
        "total_applications": Application.objects.count(),
    }
    return render(request, "home.html", context)


def account_start(request):
    return render(request, "accounts/account_start.html")


@sensitive_post_parameters("password")
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def user_login(request):
    """Login view that works on both desktop and mobile"""

    if request.user.is_authenticated:
        return redirect("dashboard")

    mobile_device = is_mobile_device(request)

    if request.method == "POST":
        is_json_request = request.content_type == "application/json"

        if is_json_request:
            try:
                data = json.loads(request.body)
                raw_identifier = data.get("username", "")
                password = data.get("password", "")
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid request data."}, status=400)
        else:
            raw_identifier = request.POST.get("username", "")
            password = request.POST.get("password", "")

        identifier = clean_login_value(raw_identifier)
        password = clean_login_value(password, is_password=True)
        auth_username = get_username_from_identifier(identifier)

        if not identifier or not password:
            error_message = "Username/email and password are required."
            if is_json_request:
                return JsonResponse({"error": error_message}, status=400)
            messages.error(request, error_message)
            return render(request, "accounts/login.html", {"form": AuthenticationForm(), "mobile_device": mobile_device})

        user = authenticate(request, username=auth_username, password=password)

        if user is not None:
            if not user.is_active:
                error_message = "Account is inactive. Please contact admin."
                if is_json_request:
                    return JsonResponse({"error": error_message}, status=403)
                messages.error(request, error_message)
                return render(request, "accounts/login.html", {"form": AuthenticationForm(), "mobile_device": mobile_device})

            if not user.is_email_verified:
                request.session["pending_verification_user_id"] = user.id
                request.session.save()
                warning_message = "Please verify your email first. Check your inbox for the verification link."
                if is_json_request:
                    return JsonResponse({"error": warning_message}, status=403)
                messages.warning(request, warning_message)
                return redirect("pending_approval")

            # Successful login
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            request.session.set_expiry(1209600)
            request.session.modified = True
            request.session.save()

            next_url = request.POST.get("next") or request.GET.get("next")
            if not next_url:
                next_url = get_dashboard_redirect_name(user)

            if is_json_request:
                try:
                    redirect_url = reverse(next_url)
                except Exception:
                    redirect_url = next_url
                return JsonResponse({"success": True, "redirect_url": redirect_url})

            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(next_url)

        error_message = "Invalid username/email or password. Please try again."
        if is_json_request:
            return JsonResponse({"error": error_message}, status=401)
        messages.error(request, error_message)

    form = AuthenticationForm()
    return render(request, "accounts/login.html", {
        "form": form,
        "mobile_device": mobile_device,
    })


@login_required
def dashboard(request):
    if request.user.role == "student":
        if not request.user.is_approved:
            messages.warning(request, "Your account is pending admin approval.")
            return redirect("pending_approval")
        if not has_student_profile(request.user):
            messages.info(request, "Please complete your profile to continue.")
            return redirect("create_student_profile")
        return redirect("student_dashboard")

    if request.user.role == "employer":
        if not has_employer_profile(request.user):
            messages.info(request, "Please complete your company profile to continue.")
            return redirect("create_employer_profile")
        return redirect("employer_profile")

    # Admin dashboard
    total_students = StudentProfile.objects.count()
    total_employers = EmployerProfile.objects.count()
    total_opportunities = InternshipOpportunity.objects.count()

    registered_accounts = User.objects.filter(role__in=["student", "employer"])
    total_registered_accounts = registered_accounts.count()
    pending_registration_count = registered_accounts.filter(Q(is_approved=False) | Q(is_email_verified=False)).count()
    verified_registration_count = registered_accounts.filter(is_approved=True, is_email_verified=True).count()

    open_opportunities = InternshipOpportunity.objects.filter(status="open").count()
    closed_opportunities = InternshipOpportunity.objects.filter(status="closed").count()

    total_applications = Application.objects.count()
    accepted_count = Application.objects.filter(status="accepted").count()
    rejected_count = Application.objects.filter(status="rejected").count()
    shortlisted_count = Application.objects.filter(status="shortlisted").count()
    pending_count = Application.objects.filter(status="pending").count()
    interview_scheduled_count = Application.objects.filter(status="interview_scheduled").count()

    placement_rate = 0
    if total_applications > 0:
        placement_rate = round((accepted_count / total_applications) * 100, 1)

    recent_applications = Application.objects.order_by("-applied_at")[:10]
    email_config = get_active_email_config()
    recent_email_logs = EmailLog.objects.order_by("-created_at")[:8]

    all_required_skills = InternshipOpportunity.objects.values_list("required_skills", flat=True)
    skill_counter = Counter()
    for skill_text in all_required_skills:
        if skill_text:
            cleaned_text = skill_text.replace("\n", ",").replace(";", ",")
            for skill in cleaned_text.split(","):
                skill = skill.strip().title()
                if skill:
                    skill_counter[skill] += 1

    top_skills = skill_counter.most_common(5)
    top_skill_labels = [item[0] for item in top_skills]
    top_skill_counts = [item[1] for item in top_skills]

    pending_users = registered_accounts.filter(Q(is_approved=False) | Q(is_email_verified=False)).order_by("-date_joined")

    all_users_data = []
    users = registered_accounts.order_by("-date_joined")
    recent_registered_users = users[:10]

    for user in users:
        profile_name = "Profile not created"
        profile_status = "Missing"
        if user.role == "student":
            profile = StudentProfile.objects.filter(user=user).first()
            if profile:
                profile_name = profile.full_name or user.username
                profile_status = "Exists"
        elif user.role == "employer":
            profile = EmployerProfile.objects.filter(user=user).first()
            if profile:
                profile_name = profile.company_name or user.username
                profile_status = "Exists"
        all_users_data.append({"user": user, "profile_name": profile_name, "profile_status": profile_status})

    context = {
        "total_students": total_students,
        "total_employers": total_employers,
        "total_opportunities": total_opportunities,
        "total_registered_accounts": total_registered_accounts,
        "pending_registration_count": pending_registration_count,
        "verified_registration_count": verified_registration_count,
        "open_opportunities": open_opportunities,
        "closed_opportunities": closed_opportunities,
        "total_applications": total_applications,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "shortlisted_count": shortlisted_count,
        "pending_count": pending_count,
        "interview_scheduled_count": interview_scheduled_count,
        "placement_rate": placement_rate,
        "recent_applications": recent_applications,
        "email_delivery_ready": email_config is not None,
        "email_sender_label": getattr(email_config, "email_host_user", "") if email_config is not None else "",
        "recent_email_logs": recent_email_logs,
        "top_skill_labels": top_skill_labels,
        "top_skill_counts": top_skill_counts,
        "pending_users": pending_users,
        "recent_registered_users": recent_registered_users,
        "all_users_data": all_users_data,
    }

    return render(request, "accounts/admin_dashboard.html", context)


def send_otp_email(request, user):
    """Send OTP email - kept for legacy compatibility"""
    token = signing.dumps({"user_id": user.id}, salt=REGISTRATION_VERIFY_SALT)
    verification_url = build_public_url(reverse("verify_registration_email", args=[token]))

    success, message = send_system_email(
        subject="Verify Your Email Address",
        message=(
            f"Hello {user.username},\n\n"
            f"Click the link below to verify your account:\n"
            f"{verification_url}\n\n"
            f"This link expires in 7 days."
        ),
        recipient_list=[user.email],
        button_text="Verify Email",
        button_url=verification_url,
    )
    return success, message


def send_registration_received_notification(user):
    """Send verification email with signed link"""
    token = signing.dumps({"user_id": user.id}, salt=REGISTRATION_VERIFY_SALT)
    verification_url = build_public_url(reverse("verify_registration_email", args=[token]))

    return send_system_email(
        subject="Verify Your Registration",
        message=(
            f"Hello {user.username},\n\n"
            f"Thank you for registering. Please verify your email address by clicking the button below.\n\n"
            f"If the button does not open, copy and paste this link into your browser:\n"
            f"{verification_url}\n\n"
            f"This link expires in 7 days.\n\n"
            f"If you did not register, please ignore this email."
        ),
        recipient_list=[user.email],
        button_text="Verify and Create Profile",
        button_url=verification_url,
    )


def get_admin_notification_users():
    """Get all admin users for notifications"""
    return User.objects.filter(Q(role="admin") | Q(is_staff=True) | Q(is_superuser=True), is_active=True).distinct()


def create_admin_notification(message):
    """Create notification for all admins"""
    admin_users = get_admin_notification_users()
    for admin_user in admin_users:
        Notification.objects.create(user=admin_user, message=message)
    return admin_users.count()


def notify_admin_new_registration(request, user, user_notified=False):
    """Notify admins about new registration"""
    role_label = user.role.title()
    if user_notified:
        dashboard_message = (
            f"New {role_label.lower()} registration: {user.username} ({user.email}). "
            f"Verification email sent."
        )
    else:
        dashboard_message = (
            f"New {role_label.lower()} registration: {user.username} ({user.email}). "
            f"Verification email delivery needs admin attention."
        )
    notified_admins = create_admin_notification(dashboard_message)

    if notified_admins == 0:
        return False, "No active admin account found."

    config = get_active_email_config()
    if config is None:
        return True, "Dashboard notification created."

    return send_system_email(
        subject=f"New {role_label} Registration",
        message=(
            f"A new {role_label.lower()} has registered.\n\n"
            f"Username: {user.username}\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone_number}\n"
            f"Role: {role_label}"
        ),
        recipient_list=[config.admin_notification_email],
        button_text="Open Admin Dashboard",
        button_url=build_public_url("/dashboard/"),
    )


def log_registration_failure(recipient, subject, message, error):
    try:
        EmailLog.objects.create(
            recipient=recipient,
            subject=subject,
            message=message,
            status="failed",
            error_message=str(error),
        )
    except Exception:
        logger.exception(
            "Could not save registration failure email log for recipient=%s",
            recipient,
        )


def send_registration_verification_safely(request, user):
    try:
        notice_success, notice_message = send_registration_received_notification(user)
    except Exception as error:
        logger.exception(
            "Registration verification email failed for user_id=%s email=%s",
            user.id,
            user.email,
        )
        notice_success = False
        notice_message = str(error)
        log_registration_failure(
            recipient=user.email,
            subject="Verify Your Registration",
            message="Registration verification email failed before delivery.",
            error=error,
        )

    try:
        notify_admin_new_registration(request, user, notice_success)
    except Exception as error:
        logger.exception(
            "Admin notification failed during registration for user_id=%s email=%s",
            user.id,
            user.email,
        )
        log_registration_failure(
            recipient=user.email,
            subject="New Registration Admin Notification",
            message="Admin notification failed during registration.",
            error=error,
        )

    return notice_success, notice_message


def student_register(request):
    mobile_device = is_mobile_device(request)

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        try:
            form_is_valid = form.is_valid()
        except Exception as error:
            email = request.POST.get("email", "")
            logger.exception("Student registration validation failed for email=%s", email)
            log_registration_failure(
                recipient=email,
                subject="Student Registration Validation Failed",
                message="Student registration failed while validating submitted form data.",
                error=error,
            )
            messages.error(request, "Registration could not be validated. Admin should check Email logs.")
            form_is_valid = False

        if form_is_valid:
            try:
                user = form.save()
                notice_success, notice_message = send_registration_verification_safely(request, user)
                request.session["registration_email_status"] = "sent" if notice_success else "failed"
                request.session["registration_email_message"] = notice_message

                if notice_success:
                    messages.success(
                        request,
                        "Account created! We sent you a verification email. Please check your inbox."
                    )
                else:
                    messages.warning(
                        request,
                        "Account created but verification email could not be sent. Admin has been notified."
                    )
                return redirect("pending_approval")
            except IntegrityError:
                messages.error(request, "This email is already registered. Please log in.")
            except Exception as error:
                email = form.cleaned_data.get("email", request.POST.get("email", ""))
                logger.exception("Student registration failed for email=%s", email)
                log_registration_failure(
                    recipient=email,
                    subject="Student Registration Failed",
                    message="Student registration failed before verification email delivery.",
                    error=error,
                )
                messages.error(request, "Registration could not be completed. Admin should check Email logs.")
    else:
        form = StudentRegistrationForm()

    return render(request, "accounts/student_register.html", {"form": form, "mobile_device": mobile_device})


def employer_register(request):
    mobile_device = is_mobile_device(request)

    if request.method == "POST":
        form = EmployerRegistrationForm(request.POST)
        try:
            form_is_valid = form.is_valid()
        except Exception as error:
            email = request.POST.get("email", "")
            logger.exception("Employer registration validation failed for email=%s", email)
            log_registration_failure(
                recipient=email,
                subject="Employer Registration Validation Failed",
                message="Employer registration failed while validating submitted form data.",
                error=error,
            )
            messages.error(request, "Registration could not be validated. Admin should check Email logs.")
            form_is_valid = False

        if form_is_valid:
            try:
                user = form.save()
                notice_success, notice_message = send_registration_verification_safely(request, user)
                request.session["registration_email_status"] = "sent" if notice_success else "failed"
                request.session["registration_email_message"] = notice_message

                if notice_success:
                    messages.success(
                        request,
                        "Employer account created! We sent you a verification email. Please check your inbox."
                    )
                else:
                    messages.warning(
                        request,
                        "Account created but verification email could not be sent. Admin has been notified."
                    )
                return redirect("pending_approval")
            except IntegrityError:
                messages.error(request, "This email is already registered. Please log in.")
            except Exception as error:
                email = form.cleaned_data.get("email", request.POST.get("email", ""))
                logger.exception("Employer registration failed for email=%s", email)
                log_registration_failure(
                    recipient=email,
                    subject="Employer Registration Failed",
                    message="Employer registration failed before verification email delivery.",
                    error=error,
                )
                messages.error(request, "Registration could not be completed. Admin should check Email logs.")
    else:
        form = EmployerRegistrationForm()

    return render(request, "accounts/employer_register.html", {"form": form, "mobile_device": mobile_device})


def verify_otp(request, user_id):
    """Legacy OTP verification - auto-verifies and redirects to profile"""
    user = get_object_or_404(User, id=user_id)

    # Activate the user
    user.is_email_verified = True
    user.is_approved = True
    user.is_active = True
    user.save()

    # Login the user
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.set_expiry(1209600)
    request.session.modified = True
    request.session.save()

    messages.success(request, "Account verified successfully! Please complete your profile.")

    if user.role == "student":
        return redirect("create_student_profile")
    elif user.role == "employer":
        return redirect("create_employer_profile")
    return redirect("dashboard")


def verify_registration_email(request, token):
    """Verify user via email link"""
    try:
        payload = signing.loads(token, salt=REGISTRATION_VERIFY_SALT, max_age=REGISTRATION_VERIFY_MAX_AGE)
    except signing.SignatureExpired:
        messages.error(request, "This verification link has expired. Please contact admin for assistance.")
        return redirect("login")
    except signing.BadSignature:
        messages.error(request, "This verification link is invalid.")
        return redirect("login")

    user = get_object_or_404(User, id=payload.get("user_id"))

    # Activate user
    user.is_email_verified = True
    user.is_approved = True
    user.is_active = True
    user.save()

    # Login the user
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.set_expiry(1209600)
    request.session.modified = True
    request.session.save()

    messages.success(request, "Email verified successfully! Please complete your profile.")

    if user.role == "student":
        return redirect("create_student_profile")
    elif user.role == "employer":
        return redirect("create_employer_profile")
    return redirect("dashboard")


def pending_approval(request):
    mobile_device = is_mobile_device(request)
    registration_email_status = request.session.get("registration_email_status")
    registration_email_message = request.session.get("registration_email_message", "")

    return render(request, "accounts/pending_approval.html", {
        "email_delivery_ready": get_active_email_config() is not None,
        "registration_email_status": registration_email_status,
        "registration_email_message": registration_email_message,
        "mobile_device": mobile_device,
    })


@login_required
def create_student_profile(request):
    if has_student_profile(request.user):
        return redirect("student_dashboard")

    if request.method == "POST":
        form = StudentProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Profile created successfully! Welcome to your dashboard.")
            return redirect("student_dashboard")
    else:
        form = StudentProfileForm()

    return render(request, "accounts/create_student_profile.html", {"form": form, "user": request.user})


@login_required
def create_employer_profile(request):
    if has_employer_profile(request.user):
        return redirect("employer_profile")

    if request.method == "POST":
        form = EmployerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Company profile created successfully! Welcome to your dashboard.")
            return redirect("employer_profile")
    else:
        form = EmployerProfileForm()

    return render(request, "employers/create_profile.html", {"form": form, "user": request.user})


@login_required
def logout_user(request):
    logout(request)
    return redirect("login")


@login_required
def approve_user(request, user_id):
    if request.user.role != "admin":
        messages.error(request, "Only administrators can approve users.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.is_active = True
    user.save()

    messages.success(request, f"{user.username} approved successfully.")
    return redirect("dashboard")


@login_required
def reject_user(request, user_id):
    if request.user.role != "admin":
        messages.error(request, "Only administrators can reject users.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()

    messages.warning(request, f"{username} has been rejected and removed.")
    return redirect("dashboard")


@login_required
def delete_user_account(request, user_id):
    if request.user.role != "admin":
        messages.error(request, "Only admin can delete users.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)
    username = user.username
    user_role = user.role
    user.delete()

    messages.success(request, f"{username} ({user_role}) deleted successfully.")
    return redirect("dashboard")


@login_required
def send_user_verification_code(request, user_id, channel="email"):
    """Admin function to send verification code"""
    if request.user.role != "admin":
        messages.error(request, "Only administrators can send verification codes.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)
    success, message = send_otp_email(request, user)

    if success:
        messages.success(request, f"Verification code sent to {user.username}")
    else:
        messages.error(request, f"Failed to send verification code: {message}")

    return redirect("dashboard")


@login_required
def admin_verify_user(request, user_id):
    """Admin function to manually verify a user"""
    if request.user.role != "admin":
        messages.error(request, "Only administrators can verify users.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)
    user.is_email_verified = True
    user.is_approved = True
    user.is_active = True
    user.save()

    messages.success(request, f"{user.username} has been verified successfully.")
    return redirect("dashboard")


@login_required
def admin_reset_user_password(request, user_id):
    """Admin function to reset user password"""
    if request.user.role != "admin":
        messages.error(request, "Only administrators can reset passwords.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)
    temporary_password = "TempPass123!"
    user.set_password(temporary_password)
    user.save()

    messages.success(request, f"Password for {user.username} has been reset to: {temporary_password}")
    return redirect("dashboard")


@login_required
def delete_old_pending_accounts(request):
    """Admin function to delete old pending accounts"""
    if request.user.role != "admin":
        messages.error(request, "Only administrators can perform this action.")
        return redirect("dashboard")

    old_accounts = User.objects.filter(role__in=["student", "employer"]).filter(Q(is_active=False) | Q(is_email_verified=False))
    deleted_count = old_accounts.count()
    old_accounts.delete()

    messages.success(request, f"Deleted {deleted_count} old pending/unverified accounts.")
    return redirect("dashboard")
