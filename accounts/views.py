# accounts/views.py

from collections import Counter
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core import signing
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
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

from .forms import AdminProfileImageForm, StudentRegistrationForm, EmployerRegistrationForm
from .models import User


logger = logging.getLogger(__name__)

REGISTRATION_VERIFY_SALT = "accounts.registration.verify"
REGISTRATION_VERIFY_MAX_AGE = 60 * 60 * 24 * 7


def is_mobile_device(request):
    user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
    mobile_keywords = [
        "mobile",
        "android",
        "iphone",
        "ipad",
        "ipod",
        "blackberry",
        "windows phone",
        "samsung",
        "xiaomi",
        "huawei",
        "oppo",
        "tecno",
        "infinix",
    ]
    return any(keyword in user_agent for keyword in mobile_keywords)


def clean_login_value(value, is_password=False):
    if value is None:
        return ""

    value = str(value)

    for char in ["\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"]:
        value = value.replace(char, "")

    if not is_password:
        value = value.strip()

    return value


def get_username_from_identifier(identifier):
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
    return StudentProfile.objects.filter(user=user).exists()


def has_employer_profile(user):
    return EmployerProfile.objects.filter(user=user).exists()


def is_admin_user(user):
    return (
        getattr(user, "role", "") == "admin"
        or user.is_staff
        or user.is_superuser
    )


def build_public_url(path):
    public_site_url = getattr(
        settings,
        "PUBLIC_SITE_URL",
        "https://ai-attachment-system-1.onrender.com",
    ).rstrip("/")

    return f"{public_site_url}{path}"


def build_absolute_url(request, view_name, *args):
    path = reverse(view_name, args=args)
    return build_public_url(path)


def get_safe_next_url(request, fallback="dashboard"):
    next_url = request.POST.get("next") or request.GET.get("next")

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return fallback


def send_registration_received_notification(user):
    token = signing.dumps(
        {"user_id": user.id},
        salt=REGISTRATION_VERIFY_SALT,
    )

    verification_url = build_public_url(
        reverse("verify_registration_email", args=[token])
    )

    return send_system_email(
        subject="Verify Your Registration",
        message=(
            f"Hello {user.username},\n\n"
            f"Thank you for registering. Please verify your email address.\n\n"
            f"Verification link:\n{verification_url}\n\n"
            f"This link expires in 7 days."
        ),
        recipient_list=[user.email],
        button_text="Verify Email",
        button_url=verification_url,
    )


def get_admin_notification_users():
    return User.objects.filter(
        Q(role="admin") | Q(is_staff=True) | Q(is_superuser=True),
        is_active=True,
    ).distinct()


def create_admin_notification(message):
    admin_users = get_admin_notification_users()

    for admin_user in admin_users:
        Notification.objects.create(
            user=admin_user,
            message=message,
        )

    return admin_users.count()


def notify_admin_new_registration(request, user, user_notified=False):
    role = getattr(user, "role", "user")
    role_label = role.title()

    if role == "employer":
        email_status = "Admin approval required before employer can log in."
    else:
        email_status = "Verification email sent." if user_notified else (
            "Verification email delivery needs admin attention."
        )
    dashboard_message = (
        f"New {role_label.lower()} registration: "
        f"{user.username} ({user.email}). {email_status}"
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
        logger.exception("Could not save email failure log.")


def send_registration_verification_safely(request, user):
    notice_success = False
    notice_message = ""

    try:
        notice_success, notice_message = send_registration_received_notification(user)
    except Exception as error:
        logger.exception(
            "Verification email failed for user_id=%s email=%s",
            user.id,
            user.email,
        )

        notice_success = False
        notice_message = str(error)

        log_registration_failure(
            recipient=user.email,
            subject="Verify Your Registration",
            message="Verification email failed.",
            error=error,
        )

    try:
        notify_admin_new_registration(request, user, notice_success)

    except Exception as error:
        logger.exception("Admin notification failed.")

        log_registration_failure(
            recipient=user.email,
            subject="Admin Notification Failed",
            message="Admin notification failed during registration.",
            error=error,
        )

    return notice_success, notice_message


def home(request):
    context = {
        "total_students": StudentProfile.objects.count(),
        "total_employers": EmployerProfile.objects.count(),
        "total_opportunities": InternshipOpportunity.objects.count(),
        "total_applications": Application.objects.count(),
        "mobile_device": is_mobile_device(request),
    }

    return render(request, "home.html", context)


def account_start(request):
    return render(
        request,
        "accounts/account_start.html",
        {
            "mobile_device": is_mobile_device(request),
        },
    )


@sensitive_post_parameters("password")
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def user_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    mobile_device = is_mobile_device(request)

    if request.method == "POST":
        is_json_request = request.content_type and request.content_type.startswith(
            "application/json"
        )

        if is_json_request:
            try:
                data = json.loads(request.body.decode("utf-8"))
                raw_identifier = data.get("username", "")
                password = data.get("password", "")
            except json.JSONDecodeError:
                return JsonResponse(
                    {"error": "Invalid request data."},
                    status=400,
                )
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

            return render(
                request,
                "accounts/login.html",
                {
                    "form": AuthenticationForm(),
                    "mobile_device": mobile_device,
                },
            )

        user = authenticate(
            request,
            username=auth_username,
            password=password,
        )

        if user is not None:
            if not user.is_active:
                error_message = "Account is inactive. Please contact admin."

                if is_json_request:
                    return JsonResponse({"error": error_message}, status=403)

                messages.error(request, error_message)

                return render(
                    request,
                    "accounts/login.html",
                    {
                        "form": AuthenticationForm(),
                        "mobile_device": mobile_device,
                    },
                )

            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend",
            )

            request.session.set_expiry(1209600)
            request.session.modified = True

            if not getattr(user, "is_email_verified", False):
                messages.warning(
                    request,
                    "Your email is not verified yet. You can continue, but please verify it later.",
                )

            next_url = get_safe_next_url(request, fallback="dashboard")

            if is_json_request:
                try:
                    redirect_url = reverse(next_url)
                except Exception:
                    redirect_url = next_url

                return JsonResponse(
                    {
                        "success": True,
                        "redirect_url": redirect_url,
                    }
                )

            messages.success(request, f"Welcome back, {user.username}!")

            return redirect(next_url)

        error_message = "Invalid username/email or password."

        if is_json_request:
            return JsonResponse({"error": error_message}, status=401)

        messages.error(request, error_message)

    return render(
        request,
        "accounts/login.html",
        {
            "form": AuthenticationForm(),
            "mobile_device": mobile_device,
        },
    )


@login_required
def dashboard(request):
    user_role = getattr(request.user, "role", "")

    if user_role == "student":
        if not has_student_profile(request.user):
            messages.info(request, "Please complete your profile to continue.")
            return redirect("create_student_profile")

        return redirect("student_dashboard")

    if user_role == "employer":
        if not has_employer_profile(request.user):
            messages.info(request, "Please complete your company profile to continue.")
            return redirect("create_employer_profile")

        return redirect("employer_profile")

    if not is_admin_user(request.user):
        messages.error(request, "Your account role is not recognized. Please contact admin.")
        return redirect("login")

    total_students = StudentProfile.objects.count()
    total_employers = EmployerProfile.objects.count()
    total_opportunities = InternshipOpportunity.objects.count()

    registered_accounts = User.objects.filter(
        role__in=["student", "employer"]
    )

    total_registered_accounts = registered_accounts.count()

    pending_registration_count = registered_accounts.filter(
        Q(is_approved=False) | Q(is_email_verified=False)
    ).count()

    verified_registration_count = registered_accounts.filter(
        is_approved=True,
        is_email_verified=True,
    ).count()

    open_opportunities = InternshipOpportunity.objects.filter(
        status="open"
    ).count()

    closed_opportunities = InternshipOpportunity.objects.filter(
        status="closed"
    ).count()

    total_applications = Application.objects.count()
    accepted_count = Application.objects.filter(status="accepted").count()
    rejected_count = Application.objects.filter(status="rejected").count()
    shortlisted_count = Application.objects.filter(status="shortlisted").count()
    pending_count = Application.objects.filter(status="pending").count()

    placement_rate = 0

    if total_applications > 0:
        placement_rate = round(
            (accepted_count / total_applications) * 100,
            1,
        )

    recent_applications = Application.objects.select_related(
        "student",
        "opportunity",
    ).order_by("-applied_at")[:10]

    email_config = get_active_email_config()
    recent_email_logs = EmailLog.objects.order_by("-created_at")[:8]

    all_required_skills = InternshipOpportunity.objects.values_list(
        "required_skills",
        flat=True,
    )

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

    pending_users = registered_accounts.filter(
        Q(is_approved=False) | Q(is_email_verified=False)
    ).order_by("-date_joined")

    users = registered_accounts.order_by("-date_joined")
    recent_registered_users = users[:10]

    all_users_data = []

    for user in users:
        profile_name = "Profile not created"
        profile_status = "Missing"

        if user.role == "student":
            profile = StudentProfile.objects.filter(user=user).first()

            if profile:
                profile_name = getattr(profile, "full_name", "") or user.username
                profile_status = "Exists"

        elif user.role == "employer":
            profile = EmployerProfile.objects.filter(user=user).first()

            if profile:
                profile_name = getattr(profile, "company_name", "") or user.username
                profile_status = "Exists"

        all_users_data.append(
            {
                "user": user,
                "profile_name": profile_name,
                "profile_status": profile_status,
            }
        )

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
        "placement_rate": placement_rate,
        "recent_applications": recent_applications,
        "email_delivery_ready": email_config is not None,
        "email_sender_label": getattr(email_config, "email_host_user", "") if email_config else "",
        "recent_email_logs": recent_email_logs,
        "top_skill_labels": top_skill_labels,
        "top_skill_counts": top_skill_counts,
        "pending_users": pending_users,
        "recent_registered_users": recent_registered_users,
        "all_users_data": all_users_data,
        "mobile_device": is_mobile_device(request),
    }

    return render(
        request,
        "accounts/admin_dashboard.html",
        context,
    )



@login_required
def admin_profile_settings(request):
    if not is_admin_user(request.user):
        messages.error(request, "Only admin users can update the admin profile image.")
        return redirect("dashboard")

    if request.method == "POST":
        form = AdminProfileImageForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Admin profile image updated successfully.")
            return redirect("admin_profile_settings")
    else:
        form = AdminProfileImageForm(instance=request.user)

    return render(
        request,
        "accounts/admin_profile_settings.html",
        {
            "form": form,
        },
    )


def student_register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    mobile_device = is_mobile_device(request)

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            try:
                user = form.save(commit=False)

                user.role = "student"
                user.is_active = False
                user.is_approved = False

                if hasattr(user, "is_email_verified"):
                    user.is_email_verified = False

                user.save()

                notice_success, notice_message = send_registration_verification_safely(
                    request,
                    user,
                )
                request.session["registration_email_status"] = (
                    "sent" if notice_success else "failed"
                )
                request.session["registration_email_message"] = notice_message
                request.session.pop("registration_review_message", None)

                messages.success(
                    request,
                    "Account created successfully. Please verify your email.",
                )

                return redirect("pending_approval")

            except IntegrityError:
                messages.error(
                    request,
                    "This email or username is already registered.",
                )

            except Exception as error:
                logger.exception("Student registration failed.")

                messages.error(
                    request,
                    f"Registration failed: {error}",
                )

        else:
            messages.error(request, "Please correct the form errors below.")

    else:
        form = StudentRegistrationForm()

    return render(
        request,
        "accounts/student_register.html",
        {
            "form": form,
            "mobile_device": mobile_device,
        },
    )


def employer_register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    mobile_device = is_mobile_device(request)

    if request.method == "POST":
        form = EmployerRegistrationForm(request.POST)

        if form.is_valid():
            try:
                user = form.save(commit=False)

                user.role = "employer"
                user.is_active = False
                user.is_approved = False

                if hasattr(user, "is_email_verified"):
                    user.is_email_verified = True

                user.save()

                admin_notice_success, admin_notice_message = notify_admin_new_registration(
                    request,
                    user,
                    user_notified=True,
                )
                request.session["registration_email_status"] = (
                    "sent" if admin_notice_success else "failed"
                )
                request.session["registration_email_message"] = admin_notice_message
                request.session["registration_review_message"] = (
                    "Employer account created successfully. Admin must approve it before login."
                )

                messages.success(
                    request,
                    "Employer account created successfully. Admin will review and approve it.",
                )

                return redirect("pending_approval")

            except IntegrityError:
                messages.error(
                    request,
                    "This email or username is already registered.",
                )

            except Exception as error:
                logger.exception("Employer registration failed.")

                messages.error(
                    request,
                    f"Registration failed: {error}",
                )

        else:
            messages.error(request, "Please correct the form errors below.")

    else:
        form = EmployerRegistrationForm()

    return render(
        request,
        "accounts/employer_register.html",
        {
            "form": form,
            "mobile_device": mobile_device,
        },
    )


def verify_registration_email(request, token):
    try:
        payload = signing.loads(
            token,
            salt=REGISTRATION_VERIFY_SALT,
            max_age=REGISTRATION_VERIFY_MAX_AGE,
        )

    except signing.SignatureExpired:
        messages.error(
            request,
            "This verification link has expired. Please contact admin.",
        )
        return redirect("login")

    except signing.BadSignature:
        messages.error(request, "This verification link is invalid.")
        return redirect("login")

    user = get_object_or_404(
        User,
        id=payload.get("user_id"),
    )

    if hasattr(user, "is_email_verified"):
        user.is_email_verified = True

    if user.role == "employer":
        user.is_approved = False
        user.is_active = False
        user.save()

        request.session["registration_review_message"] = (
            "Employer email verified. Admin must approve the account before login."
        )
        request.session["registration_email_status"] = "sent"
        request.session["registration_email_message"] = "Employer is waiting for admin approval."

        try:
            notify_admin_new_registration(request, user, user_notified=True)
        except Exception as error:
            logger.exception("Admin notification failed after employer verification.")
            log_registration_failure(
                recipient=user.email,
                subject="Admin Notification Failed",
                message="Employer verified email but admin notification failed.",
                error=error,
            )

        messages.info(request, "Email verified. Admin must approve your employer account before login.")
        return redirect("pending_approval")

    user.is_approved = True
    user.is_active = True
    user.save()

    login(
        request,
        user,
        backend="django.contrib.auth.backends.ModelBackend",
    )

    messages.success(
        request,
        "Email verified successfully.",
    )

    if user.role == "student":
        if has_student_profile(user):
            return redirect("student_dashboard")
        return redirect("create_student_profile")

    return redirect("dashboard")


def pending_approval(request):
    return render(
        request,
        "accounts/pending_approval.html",
        {
            "email_delivery_ready": get_active_email_config() is not None,
            "registration_email_status": request.session.get("registration_email_status"),
            "registration_email_message": request.session.get("registration_email_message"),
            "registration_review_message": request.session.get("registration_review_message"),
            "mobile_device": is_mobile_device(request),
        },
    )


@login_required
def create_student_profile(request):
    if getattr(request.user, "role", "") != "student" and not is_admin_user(request.user):
        messages.error(request, "Only student accounts can create a student profile.")
        return redirect("dashboard")

    if has_student_profile(request.user):
        return redirect("student_dashboard")

    if request.method == "POST":
        form = StudentProfileForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            messages.success(
                request,
                "Profile created successfully.",
            )

            return redirect("student_dashboard")

        messages.error(request, "Please correct the form errors below.")

    else:
        form = StudentProfileForm()

    return render(
        request,
        "accounts/create_student_profile.html",
        {
            "form": form,
            "user": request.user,
            "mobile_device": is_mobile_device(request),
        },
    )


@login_required
def create_employer_profile(request):
    if getattr(request.user, "role", "") != "employer" and not is_admin_user(request.user):
        messages.error(request, "Only employer accounts can create a company profile.")
        return redirect("dashboard")

    if has_employer_profile(request.user):
        return redirect("employer_profile")

    if request.method == "POST":
        form = EmployerProfileForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            messages.success(
                request,
                "Company profile created successfully.",
            )

            return redirect("employer_profile")

        messages.error(request, "Please correct the form errors below.")

    else:
        form = EmployerProfileForm()

    return render(
        request,
        "employers/create_profile.html",
        {
            "form": form,
            "user": request.user,
            "mobile_device": is_mobile_device(request),
        },
    )


@login_required
def logout_user(request):
    logout(request)
    messages.success(request, "You have logged out successfully.")
    return redirect("login")


@login_required
def approve_user(request, user_id):
    if not is_admin_user(request.user):
        messages.error(request, "Only administrators can approve users.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)

    user.is_approved = True
    user.is_active = True
    user.save()

    messages.success(
        request,
        f"{user.username} approved successfully.",
    )

    return redirect("dashboard")


@login_required
def reject_user(request, user_id):
    if not is_admin_user(request.user):
        messages.error(request, "Only administrators can reject users.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)
    username = user.username

    user.delete()

    messages.warning(
        request,
        f"{username} has been rejected and removed.",
    )

    return redirect("dashboard")


@login_required
def delete_user_account(request, user_id):
    if not is_admin_user(request.user):
        messages.error(request, "Only admin can delete users.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, "You cannot delete your own account while logged in.")
        return redirect("dashboard")

    username = user.username
    user_role = user.role

    user.delete()

    messages.success(
        request,
        f"{username} ({user_role}) deleted successfully.",
    )

    return redirect("dashboard")


@login_required
def admin_verify_user(request, user_id):
    if not is_admin_user(request.user):
        messages.error(request, "Only administrators can verify users.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)

    if hasattr(user, "is_email_verified"):
        user.is_email_verified = True

    user.is_approved = True
    user.is_active = True
    user.save()

    messages.success(
        request,
        f"{user.username} verified successfully.",
    )

    return redirect("dashboard")


@login_required
def admin_reset_user_password(request, user_id):
    if not is_admin_user(request.user):
        messages.error(
            request,
            "Only administrators can reset passwords.",
        )
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)

    temporary_password = "TempPass123!"

    user.set_password(temporary_password)
    user.save()

    messages.success(
        request,
        f"Password for {user.username} reset to: {temporary_password}",
    )

    return redirect("dashboard")


@login_required
def delete_old_pending_accounts(request):
    if not is_admin_user(request.user):
        messages.error(
            request,
            "Only administrators can perform this action.",
        )
        return redirect("dashboard")

    old_accounts = User.objects.filter(
        role__in=["student", "employer"],
    ).filter(
        Q(is_active=False) | Q(is_email_verified=False) | Q(is_approved=False)
    )

    deleted_count = old_accounts.count()
    old_accounts.delete()

    messages.success(
        request,
        f"Deleted {deleted_count} old pending/unverified accounts.",
    )

    return redirect("dashboard")

# ==================== PASSWORD RESET VIEWS ====================

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail


def password_reset_request(request):
    """Request a password reset and report real email delivery failures."""
    if request.method == 'POST':
        email = clean_login_value(request.POST.get('email'))

        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'accounts/password_reset.html', {'email_value': email})

        user = User.objects.filter(email__iexact=email).first()

        if not user:
            messages.success(
                request,
                'If an account exists with that email, a password reset link has been sent.',
            )
            return redirect('password_reset_done')

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = build_public_url(f'/reset-password/{uid}/{token}/')

        sent, delivery_message = send_system_email(
            subject='Password Reset Request - AI Internship',
            message=(
                f'Hello {user.username or user.email},\n\n'
                'You requested a password reset for your AI Internship account.\n\n'
                f'Reset link:\n{reset_link}\n\n'
                'This link can be used once. If you did not request this, you can ignore this email.'
            ),
            recipient_list=[user.email],
            button_text='Reset Password',
            button_url=reset_link,
        )

        if sent:
            messages.success(
                request,
                'Password reset email sent. Check your inbox and spam folder.',
            )
        else:
            messages.error(
                request,
                f'Password reset email was not sent: {delivery_message}',
            )

        return redirect('password_reset_done')

    return render(request, 'accounts/password_reset.html')

def password_reset_done(request):
    """Step 2: After email is sent, show confirmation page"""
    return render(request, 'accounts/password_reset_done.html')


def password_reset_confirm(request, uidb64, token):
    """Step 3: User clicks reset link, verify token and show reset form"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = (
                request.POST.get('new_password')
                or request.POST.get('new_password1')
            )
            confirm_password = (
                request.POST.get('confirm_password')
                or request.POST.get('new_password2')
            )
            
            if new_password == confirm_password and len(new_password) >= 6:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password reset successful! Please login with your new password.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match or password is too short (min 6 characters).')
        
        return render(request, 'accounts/password_reset_confirm.html', {'valid': True, 'validlink': True})
    else:
        return render(request, 'accounts/password_reset_confirm.html', {'valid': False, 'validlink': False})


def password_reset_complete(request):
    """Step 4: After password reset success"""
    return render(request, 'accounts/password_reset_complete.html')