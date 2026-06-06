# accounts/views.py

from collections import Counter
from datetime import timedelta
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
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

from internships.models import (
    InternshipOpportunity,
    Application,
)

from notifications.models import Notification, EmailLog
from notifications.email_service import (
    get_active_email_config,
    send_system_email,
)
from notifications.sms_service import send_registration_otp_sms
from notifications.whatsapp_service import send_registration_otp_whatsapp

from .forms import (
    StudentRegistrationForm,
    EmployerRegistrationForm,
    OTPVerificationForm,
)
from .auth_flow import (
    authenticate_identifier,
    clean_login_value,
    dashboard_redirect_name,
)

from .models import User


def is_mobile_device(request):
    """
    Detect if the request comes from a mobile device.
    """
    user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
    mobile_keywords = [
        "mobile",
        "android",
        "iphone",
        "ipad",
        "ipod",
        "blackberry",
        "windows phone",
    ]
    return any(keyword in user_agent for keyword in mobile_keywords)


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
    """
    Login view fixed for desktop and mobile.

    Fixes:
    - username OR email login
    - case-insensitive username/email lookup
    - removes accidental spaces from phone keyboard
    - keeps one consistent session flow
    """

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
                return JsonResponse(
                    {"error": "Invalid request data."},
                    status=400,
                )
        else:
            raw_identifier = request.POST.get("username", "")
            password = request.POST.get("password", "")

        identifier = clean_login_value(raw_identifier)
        password = clean_login_value(password)

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
                    "site_key": getattr(settings, "RECAPTCHA_SITE_KEY", None),
                    "mobile_device": mobile_device,
                },
            )

        login_result = authenticate_identifier(request, identifier, password)
        user = login_result.user

        if user is not None:
            if not getattr(user, "is_email_verified", False):
                request.session["pending_verification_user_id"] = user.id
                request.session.save()

                if is_json_request:
                    return JsonResponse(
                        {
                            "error": "Please verify your email first. Check your inbox for the OTP code.",
                            "redirect_url": reverse("verify_otp", args=[user.id]),
                        },
                        status=403,
                    )

                messages.warning(request, "Please verify your email first. Check your inbox for the OTP code.")
                return redirect("verify_otp", user.id)

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
                        "site_key": getattr(settings, "RECAPTCHA_SITE_KEY", None),
                        "mobile_device": mobile_device,
                    },
                )

            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            request.session.set_expiry(1209600)
            request.session.modified = True
            request.session.save()

            next_url = request.POST.get("next") or request.GET.get("next")

            if not next_url:
                next_url = dashboard_redirect_name(user)

            if is_json_request:
                try:
                    redirect_url = reverse(next_url)
                except Exception:
                    redirect_url = next_url

                return JsonResponse(
                    {
                        "success": True,
                        "redirect_url": redirect_url,
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "role": user.role,
                        },
                    }
                )

            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(next_url)

        error_message = (
            "Enter the correct username/email and password. "
            "Check that your phone keyboard did not add spaces or capital letters."
        )

        if is_json_request:
            return JsonResponse({"error": error_message}, status=401)

        messages.error(request, error_message)

    form = AuthenticationForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "site_key": getattr(settings, "RECAPTCHA_SITE_KEY", None),
            "mobile_device": mobile_device,
        },
    )


@login_required
def dashboard(request):
    if request.user.role == "student":
        if not request.user.is_approved:
            messages.warning(request, "Your account is pending admin approval.")
            return redirect("pending_approval")

        if not hasattr(request.user, "student_profile"):
            messages.info(request, "Please complete your profile to continue.")
            return redirect("create_student_profile")

        return redirect("student_dashboard")

    if request.user.role == "employer":
        if not hasattr(request.user, "employer_profile"):
            messages.info(request, "Please complete your company profile to continue.")
            return redirect("create_employer_profile")

        return redirect("employer_profile")

    total_students = StudentProfile.objects.count()
    total_employers = EmployerProfile.objects.count()
    total_opportunities = InternshipOpportunity.objects.count()

    registered_accounts = User.objects.filter(role__in=["student", "employer"])
    total_registered_accounts = registered_accounts.count()

    pending_registration_count = registered_accounts.filter(
        Q(is_approved=False) | Q(is_email_verified=False)
    ).count()

    verified_registration_count = registered_accounts.filter(
        is_approved=True,
        is_email_verified=True,
    ).count()

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
        Q(is_approved=False)
        | Q(is_email_verified=False)
        | Q(is_active=False)
        | Q(otp_code__isnull=False)
    ).order_by("-date_joined")

    latest_registration_otps = pending_users[:10]

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
        "interview_scheduled_count": interview_scheduled_count,
        "placement_rate": placement_rate,
        "recent_applications": recent_applications,
        "email_delivery_ready": email_config is not None,
        "email_sender_label": getattr(email_config, "email_host_user", "") if email_config is not None else "",
        "recent_email_logs": recent_email_logs,
        "top_skill_labels": top_skill_labels,
        "top_skill_counts": top_skill_counts,
        "pending_users": pending_users,
        "latest_registration_otps": latest_registration_otps,
        "recent_registered_users": recent_registered_users,
        "all_users_data": all_users_data,
    }

    return render(request, "accounts/admin_dashboard.html", context)


def build_absolute_url(request, view_name, *args):
    path = reverse(view_name, args=args)
    public_site_url = getattr(settings, "PUBLIC_SITE_URL", "").rstrip("/")

    if public_site_url:
        return f"{public_site_url}{path}"

    return request.build_absolute_uri(path)


def build_public_url(path):
    public_site_url = getattr(
        settings,
        "PUBLIC_SITE_URL",
        "https://ai-attachment-system.onrender.com",
    ).rstrip("/")

    return f"{public_site_url}{path}"


def send_otp_email(request, user):
    otp = user.generate_otp()

    success, message = send_system_email(
        subject="Verify Your Email Address",
        message=(
            f"Hello {user.username},\n\n"
            f"Your verification code is: {otp}\n\n"
            f"Enter this code on the verification page to confirm that this email belongs to you.\n"
            f"This code expires in 15 minutes.\n\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"AI Internship & Attachment Matching System"
        ),
        recipient_list=[user.email],
        button_text="Verify Email",
        button_url=build_public_url(reverse("verify_otp", args=[user.id])),
    )

    return success, message


def send_registration_whatsapp_otp(user):
    if not user.phone_number:
        return False, "User has no phone number."

    return send_registration_otp_whatsapp(user, user.otp_code)


def send_registration_sms_otp(user):
    return send_registration_otp_sms(user, user.otp_code)


def get_admin_notification_users():
    return User.objects.filter(
        Q(role="admin") | Q(is_staff=True) | Q(is_superuser=True),
        is_active=True,
    ).distinct()


def create_admin_notification(message):
    admin_users = get_admin_notification_users()

    for admin_user in admin_users:
        Notification.objects.create(user=admin_user, message=message)

    return admin_users.count()


def notify_admin_new_registration(request, user, otp_sent=False):
    role_label = user.role.title()
    otp_label = user.otp_code or "No OTP generated"

    if otp_sent:
        dashboard_message = (
            f"New {role_label.lower()} registration created. Automatic OTP sent; awaiting user verification: "
            f"{user.username} ({user.email}). OTP: {otp_label}."
        )
        admin_instruction = "The system has sent the first email verification code automatically."
        resend_instruction = (
            "Open the admin dashboard to monitor verification. "
            "Use Email Code, WhatsApp Code, or SMS Code only if the user needs a new code."
        )
    else:
        dashboard_message = (
            f"New {role_label.lower()} registration created, but automatic OTP delivery needs admin attention: "
            f"{user.username} ({user.email}). OTP: {otp_label}."
        )
        admin_instruction = (
            "The system tried to send the first verification code automatically, "
            "but delivery was not confirmed."
        )
        resend_instruction = "Open the admin dashboard and resend the code by Email, WhatsApp, or SMS."

    notified_admins = create_admin_notification(dashboard_message)

    if notified_admins == 0:
        return False, "No active admin account found to receive the dashboard notification."

    config = get_active_email_config()

    if config is None:
        return True, "Dashboard notification created. No active email configuration found for email alert."

    return send_system_email(
        subject=f"New {role_label} Registration - Verification Required",
        message=(
            f"A new {role_label.lower()} has registered. {admin_instruction}\n\n"
            f"Username: {user.username}\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone_number}\n"
            f"OTP: {otp_label}\n"
            f"Role: {role_label}\n\n"
            f"Admin action:\n"
            f"{resend_instruction}\n\n"
            f"After the user enters the verification code successfully, "
            f"the system activates the account automatically."
        ),
        recipient_list=[config.admin_notification_email],
        button_text="Open Admin Dashboard",
        button_url=build_public_url("/dashboard/"),
    )


def notify_admin_user_verified(request, user):
    config = get_active_email_config()
    role_label = user.role.title()

    dashboard_message = (
        f"{role_label} account verified by OTP and activated: "
        f"{user.username} ({user.email})."
    )

    create_admin_notification(dashboard_message)

    if config is None:
        return False, "No active email configuration found."

    return send_system_email(
        subject=f"{role_label} Verified and Activated",
        message=(
            f"{user.username} has entered the verification code successfully.\n\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone_number}\n"
            f"Role: {role_label}\n\n"
            f"The account has been activated automatically and the user can now access their dashboard."
        ),
        recipient_list=[config.admin_notification_email],
        button_text="Open Admin Dashboard",
        button_url=build_public_url("/dashboard/"),
    )


def student_register(request):
    mobile_device = is_mobile_device(request)

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            try:
                user = form.save()

                otp_success, otp_message = send_otp_email(request, user)
                notify_admin_new_registration(request, user, otp_success)

                if otp_success:
                    messages.success(
                        request,
                        "Account created. A verification code has been sent to your email.",
                    )
                else:
                    messages.warning(
                        request,
                        "Account created, but the verification code could not be sent. "
                        "Admin has been notified. You can enter the code here after admin resends it.",
                    )

                return redirect("verify_otp", user.id)

            except IntegrityError:
                messages.error(
                    request,
                    "This email is already registered. Please log in or use another email.",
                )
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
    mobile_device = is_mobile_device(request)

    if request.method == "POST":
        form = EmployerRegistrationForm(request.POST)

        if form.is_valid():
            try:
                user = form.save()

                otp_success, otp_message = send_otp_email(request, user)
                notify_admin_new_registration(request, user, otp_success)

                if otp_success:
                    messages.success(
                        request,
                        "Employer account created. A verification code has been sent to your email.",
                    )
                else:
                    messages.warning(
                        request,
                        "Employer account created, but the verification code could not be sent. "
                        "Admin has been notified. You can enter the code here after admin resends it.",
                    )

                return redirect("verify_otp", user.id)

            except IntegrityError:
                messages.error(
                    request,
                    "This email is already registered. Please log in or use another email.",
                )
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


def verify_otp(request, user_id):
    user = get_object_or_404(User, id=user_id)
    mobile_device = is_mobile_device(request)

    if request.method == "POST":
        form = OTPVerificationForm(request.POST)

        if form.is_valid():
            entered_otp = form.cleaned_data["otp_code"]

            otp_has_expired = (
                user.otp_created_at
                and timezone.now() > user.otp_created_at + timedelta(minutes=15)
            )

            if otp_has_expired:
                messages.error(
                    request,
                    "This code has expired. Please ask the admin to send a new verification code.",
                )

            elif entered_otp == user.otp_code:
                user.is_email_verified = True
                user.is_approved = True
                user.is_active = True
                user.otp_code = None
                user.otp_created_at = None
                user.save()

                notify_admin_user_verified(request, user)

                login(request, user, backend="django.contrib.auth.backends.ModelBackend")

                request.session.set_expiry(1209600)
                request.session.modified = True
                request.session.save()

                messages.success(
                    request,
                    "Verification successful! Please complete your profile.",
                )

                if user.role == "student":
                    return redirect("create_student_profile")

                if user.role == "employer":
                    return redirect("create_employer_profile")

                return redirect("dashboard")

            else:
                messages.error(request, "Invalid verification code.")
    else:
        form = OTPVerificationForm()

    return render(
        request,
        "accounts/verify_otp.html",
        {
            "form": form,
            "user_obj": user,
            "email_delivery_ready": get_active_email_config() is not None,
            "mobile_device": mobile_device,
        },
    )


@login_required
def create_student_profile(request):
    if hasattr(request.user, "student_profile"):
        return redirect("student_dashboard")

    if request.method == "POST":
        form = StudentProfileForm(request.POST, request.FILES)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            messages.success(
                request,
                "Profile created successfully! Welcome to your dashboard.",
            )

            return redirect("student_dashboard")
    else:
        form = StudentProfileForm()

    return render(
        request,
        "accounts/create_student_profile.html",
        {
            "form": form,
            "user": request.user,
        },
    )


@login_required
def create_employer_profile(request):
    if hasattr(request.user, "employer_profile"):
        return redirect("employer_profile")

    if request.method == "POST":
        form = EmployerProfileForm(request.POST, request.FILES)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            messages.success(
                request,
                "Company profile created successfully! Welcome to your dashboard.",
            )

            return redirect("employer_profile")
    else:
        form = EmployerProfileForm()

    return render(
        request,
        "accounts/create_employer_profile.html",
        {
            "form": form,
            "user": request.user,
        },
    )


def pending_approval(request):
    mobile_device = is_mobile_device(request)

    return render(
        request,
        "accounts/pending_approval.html",
        {
            "email_delivery_ready": get_active_email_config() is not None,
            "mobile_device": mobile_device,
        },
    )


@login_required
def send_user_verification_code(request, user_id, channel="email"):
    if request.user.role != "admin":
        messages.error(request, "Only administrators can send verification codes.")
        return redirect("dashboard")

    user = get_object_or_404(
        User,
        id=user_id,
        role__in=["student", "employer"],
        is_approved=False,
    )

    if user.is_email_verified:
        messages.info(
            request,
            f"{user.username} is already verified and can now be approved.",
        )
        return redirect("dashboard")

    valid_channels = ["email", "whatsapp", "sms"]

    if channel not in valid_channels:
        messages.error(request, "Invalid verification channel.")
        return redirect("dashboard")

    delivery_results = []
    delivery_failed = False
    successful_deliveries = 0

    if channel in ["email"]:
        email_success, email_message = send_otp_email(request, user)
        delivery_results.append(f"Email: {email_message}")

        if not email_success:
            delivery_failed = True
        else:
            successful_deliveries += 1
    else:
        user.generate_otp()

    if channel in ["whatsapp"]:
        whatsapp_success, whatsapp_message = send_registration_whatsapp_otp(user)
        delivery_results.append(f"WhatsApp: {whatsapp_message}")

        if not whatsapp_success:
            delivery_failed = True
        else:
            successful_deliveries += 1

    if channel == "sms":
        sms_success, sms_message = send_registration_sms_otp(user)
        delivery_results.append(f"SMS: {sms_message}")

        if not sms_success:
            delivery_failed = True
        else:
            successful_deliveries += 1

    result_message = " ".join(delivery_results)

    if successful_deliveries == 0:
        user.otp_code = None
        user.otp_created_at = None
        user.save()

        messages.error(
            request,
            f"No verification code was delivered to {user.username}. {result_message}",
        )
        return redirect("dashboard")

    if delivery_failed:
        messages.warning(
            request,
            f"Verification code process completed for {user.username}, "
            f"but one channel failed. {result_message}",
        )
    else:
        messages.success(
            request,
            f"Verification code sent to {user.username}. {result_message}",
        )

    return redirect("dashboard")


@login_required
def approve_user(request, user_id):
    if request.user.role != "admin":
        messages.error(request, "Only administrators can approve users.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)

    if not user.is_email_verified:
        messages.error(
            request,
            "This user must enter the admin-generated verification code. "
            "Successful verification activates the account automatically.",
        )
        return redirect("dashboard")

    user.is_approved = True
    user.is_active = True
    user.save()

    role_label = user.role.title()

    Notification.objects.create(
        user=user,
        message="Your account has been approved. You can now login and access your dashboard.",
    )

    user_email_success, user_email_message = send_system_email(
        subject="Account Approved",
        message=(
            f"Hello {user.username},\n\n"
            f"Your account has been approved successfully.\n\n"
            f"You can now login and access your dashboard.\n\n"
            f"AI Internship & Attachment Matching System"
        ),
        recipient_list=[user.email],
        button_text="Login to Dashboard",
        button_url=build_public_url(reverse("login")),
    )

    create_admin_notification(
        f"{role_label} account approved by {request.user.username}: "
        f"{user.username} ({user.email})."
    )

    config = get_active_email_config()
    admin_email_success = True
    admin_email_message = "No admin email configuration found."

    if config is not None:
        admin_email_success, admin_email_message = send_system_email(
            subject=f"{role_label} Account Approved",
            message=(
                f"{request.user.username} approved {user.username}.\n\n"
                f"Email: {user.email}\n"
                f"Phone: {user.phone_number}\n"
                f"Role: {role_label}\n\n"
                f"The account is now active."
            ),
            recipient_list=[config.admin_notification_email],
            button_text="Open Admin Dashboard",
            button_url=build_public_url("/dashboard/"),
        )

    if not user_email_success or not admin_email_success:
        messages.warning(
            request,
            f"{user.username} approved successfully, but one email notification failed. "
            f"User email: {user_email_message} Admin email: {admin_email_message}",
        )
        return redirect("dashboard")

    messages.success(
        request,
        f"{user.username} approved successfully. User and admin notifications sent.",
    )

    return redirect("dashboard")


@login_required
def reject_user(request, user_id):
    if request.user.role != "admin":
        messages.error(request, "Only administrators can reject users.")
        return redirect("dashboard")

    user = User.objects.filter(id=user_id).first()

    if user is None:
        messages.error(request, "User does not exist.")
        return redirect("dashboard")

    if user.role == "admin":
        messages.error(request, "Admin account cannot be rejected here.")
        return redirect("dashboard")

    username = user.username
    user_email = user.email

    send_system_email(
        subject="Account Registration Rejected",
        message=(
            f"Hello {username},\n\n"
            f"Your account registration was not approved.\n\n"
            f"If you believe this was a mistake, please contact the system administrator.\n\n"
            f"AI Internship & Attachment Matching System"
        ),
        recipient_list=[user_email],
    )

    user.delete()

    messages.warning(
        request,
        f"{username} has been rejected and removed. Email notification sent.",
    )

    return redirect("dashboard")


@login_required
def delete_user_account(request, user_id):
    if request.user.role != "admin":
        messages.error(request, "Only admin can delete users.")
        return redirect("dashboard")

    user = User.objects.filter(id=user_id).first()

    if user is None:
        messages.error(request, "User does not exist.")
        return redirect("dashboard")

    if user.role == "admin":
        messages.error(request, "Admin account cannot be deleted here.")
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
def logout_user(request):
    logout(request)
    return redirect("login")
