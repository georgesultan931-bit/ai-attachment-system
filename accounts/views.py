from collections import Counter
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from students.models import StudentProfile
from employers.models import EmployerProfile

from internships.models import (
    InternshipOpportunity,
    Application
)

from notifications.models import Notification, EmailConfiguration
from notifications.email_service import send_system_email
from notifications.sms_service import send_registration_otp_sms
from notifications.whatsapp_service import send_registration_otp_whatsapp

from .forms import (
    StudentRegistrationForm,
    EmployerRegistrationForm,
    OTPVerificationForm
)

from .models import User


def home(request):

    context = {
        'total_students': StudentProfile.objects.count(),
        'total_employers': EmployerProfile.objects.count(),
        'total_opportunities': InternshipOpportunity.objects.count(),
        'total_applications': Application.objects.count(),
    }

    return render(request, 'home.html', context)


@login_required
def dashboard(request):

    if request.user.role == 'student':

        if not request.user.is_approved:

            messages.warning(
                request,
                'Your account is pending admin approval.'
            )

            return redirect('pending_approval')

        return redirect('student_dashboard')

    if request.user.role == 'employer':

        return redirect('employer_profile')

    total_students = StudentProfile.objects.count()
    total_employers = EmployerProfile.objects.count()
    total_opportunities = InternshipOpportunity.objects.count()

    open_opportunities = InternshipOpportunity.objects.filter(
        status='open'
    ).count()

    closed_opportunities = InternshipOpportunity.objects.filter(
        status='closed'
    ).count()

    total_applications = Application.objects.count()

    accepted_count = Application.objects.filter(
        status='accepted'
    ).count()

    rejected_count = Application.objects.filter(
        status='rejected'
    ).count()

    shortlisted_count = Application.objects.filter(
        status='shortlisted'
    ).count()

    pending_count = Application.objects.filter(
        status='pending'
    ).count()

    interview_scheduled_count = Application.objects.filter(
        status='interview_scheduled'
    ).count()

    placement_rate = 0

    if total_applications > 0:

        placement_rate = round(
            (accepted_count / total_applications) * 100,
            1
        )

    recent_applications = Application.objects.order_by(
        '-applied_at'
    )[:10]

    all_required_skills = InternshipOpportunity.objects.values_list(
        'required_skills',
        flat=True
    )

    skill_counter = Counter()

    for skill_text in all_required_skills:

        if skill_text:

            cleaned_text = skill_text.replace(
                '\n',
                ','
            ).replace(
                ';',
                ','
            )

            for skill in cleaned_text.split(','):

                skill = skill.strip().title()

                if skill:
                    skill_counter[skill] += 1

    top_skills = skill_counter.most_common(5)

    top_skill_labels = [
        item[0]
        for item in top_skills
    ]

    top_skill_counts = [
        item[1]
        for item in top_skills
    ]

    pending_users = User.objects.filter(
        role__in=[
            'student',
            'employer'
        ],
        is_approved=False
    ).order_by('-date_joined')

    all_users_data = []

    users = User.objects.exclude(
        role='admin'
    ).order_by('-date_joined')

    for user in users:

        profile_name = 'Profile not created'
        profile_status = 'Missing'

        if user.role == 'student':

            profile = StudentProfile.objects.filter(
                user=user
            ).first()

            if profile:
                profile_name = profile.full_name or user.username
                profile_status = 'Exists'

        elif user.role == 'employer':

            profile = EmployerProfile.objects.filter(
                user=user
            ).first()

            if profile:
                profile_name = profile.company_name or user.username
                profile_status = 'Exists'

        all_users_data.append({
            'user': user,
            'profile_name': profile_name,
            'profile_status': profile_status,
        })

    context = {
        'total_students': total_students,
        'total_employers': total_employers,
        'total_opportunities': total_opportunities,

        'open_opportunities': open_opportunities,
        'closed_opportunities': closed_opportunities,

        'total_applications': total_applications,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
        'shortlisted_count': shortlisted_count,
        'pending_count': pending_count,
        'interview_scheduled_count': interview_scheduled_count,

        'placement_rate': placement_rate,
        'recent_applications': recent_applications,

        'top_skill_labels': top_skill_labels,
        'top_skill_counts': top_skill_counts,

        'pending_users': pending_users,
        'all_users_data': all_users_data,
    }

    return render(
        request,
        'accounts/admin_dashboard.html',
        context
    )


def build_absolute_url(request, view_name, *args):

    return request.build_absolute_uri(
        reverse(
            view_name,
            args=args
        )
    )


def send_otp_email(request, user):

    otp = user.generate_otp()

    success, message = send_system_email(
        subject='Verify Your Email Address',
        message=(
            f'Hello {user.username},\n\n'
            f'Your verification code is: {otp}\n\n'
            f'Enter this code on the verification page to confirm that this email belongs to you.\n'
            f'This code expires in 15 minutes.\n\n'
            f'AI Internship & Attachment Matching System'
        ),
        recipient_list=[
            user.email
        ],
        button_text='Verify Email',
        button_url=build_absolute_url(
            request,
            'verify_otp',
            user.id
        )
    )

    return success, message


def send_registration_whatsapp_otp(user):

    if not user.phone_number:

        return (
            False,
            'User has no phone number.'
        )

    return send_registration_otp_whatsapp(
        user,
        user.otp_code
    )


def send_registration_sms_otp(user):

    return send_registration_otp_sms(
        user,
        user.otp_code
    )


def notify_admin_new_registration(request, user):

    config = EmailConfiguration.objects.filter(
        is_active=True
    ).first()

    if config is None:

        return False, 'No active email configuration found.'

    role_label = user.role.title()

    dashboard_message = (
        f'New {role_label.lower()} registration awaiting verification code: '
        f'{user.username} ({user.email}).'
    )

    admin_users = User.objects.filter(
        role='admin',
        is_active=True
    )

    for admin_user in admin_users:
        Notification.objects.create(
            user=admin_user,
            message=dashboard_message
        )

    email_code_url = build_absolute_url(
        request,
        'send_user_verification_code_channel',
        user.id,
        'email'
    )

    whatsapp_code_url = build_absolute_url(
        request,
        'send_user_verification_code_channel',
        user.id,
        'whatsapp'
    )

    sms_code_url = build_absolute_url(
        request,
        'send_user_verification_code_channel',
        user.id,
        'sms'
    )

    return send_system_email(
        subject=f'New {role_label} Registration - Verification Required',
        message=(
            f'A new {role_label.lower()} has registered and is waiting for you to send a verification code.\n\n'
            f'Username: {user.username}\n'
            f'Email: {user.email}\n'
            f'Phone: {user.phone_number}\n'
            f'Role: {role_label}\n\n'
            f'Admin actions:\n'
            f'Send code by email: {email_code_url}\n'
            f'Send code by WhatsApp: {whatsapp_code_url}\n'
            f'Send code by SMS: {sms_code_url}\n\n'
            f'After the user enters the verification code successfully, the system activates the account automatically.'
        ),
        recipient_list=[
            config.admin_notification_email
        ],
        button_text='Open Admin Dashboard',
        button_url=build_absolute_url(
            request,
            'dashboard'
        )
    )


def notify_admin_user_verified(request, user):

    config = EmailConfiguration.objects.filter(
        is_active=True
    ).first()

    role_label = user.role.title()

    dashboard_message = (
        f'{role_label} account verified and activated: '
        f'{user.username} ({user.email}).'
    )

    admin_users = User.objects.filter(
        role='admin',
        is_active=True
    )

    for admin_user in admin_users:
        Notification.objects.create(
            user=admin_user,
            message=dashboard_message
        )

    if config is None:

        return False, 'No active email configuration found.'

    return send_system_email(
        subject=f'{role_label} Verified and Activated',
        message=(
            f'{user.username} has entered the verification code successfully.\n\n'
            f'Email: {user.email}\n'
            f'Phone: {user.phone_number}\n'
            f'Role: {role_label}\n\n'
            f'The account has been activated automatically and the user can now access their dashboard.'
        ),
        recipient_list=[
            config.admin_notification_email
        ],
        button_text='Open Admin Dashboard',
        button_url=build_absolute_url(
            request,
            'dashboard'
        )
    )


def student_register(request):

    if request.method == 'POST':

        form = StudentRegistrationForm(request.POST)

        if form.is_valid():

            try:

                user = form.save()

                notify_admin_new_registration(
                    request,
                    user
                )

                messages.success(
                    request,
                    'Account created. An admin will review your registration and send your verification code.'
                )

                return redirect('pending_approval')

            except IntegrityError:

                messages.error(
                    request,
                    'An account with this email already exists.'
                )

    else:

        form = StudentRegistrationForm()

    return render(
        request,
        'accounts/student_register.html',
        {
            'form': form
        }
    )


def employer_register(request):

    if request.method == 'POST':

        form = EmployerRegistrationForm(request.POST)

        if form.is_valid():

            try:

                user = form.save()

                notify_admin_new_registration(
                    request,
                    user
                )

                messages.success(
                    request,
                    'Employer account created. An admin will review your registration and send your verification code.'
                )

                return redirect('pending_approval')

            except IntegrityError:

                messages.error(
                    request,
                    'An account with this email already exists.'
                )

    else:

        form = EmployerRegistrationForm()

    return render(
        request,
        'accounts/employer_register.html',
        {
            'form': form
        }
    )


def verify_otp(request, user_id):

    user = get_object_or_404(
        User,
        id=user_id
    )

    if request.method == 'POST':

        form = OTPVerificationForm(request.POST)

        if form.is_valid():

            entered_otp = form.cleaned_data['otp_code']

            otp_has_expired = (
                user.otp_created_at
                and timezone.now() > user.otp_created_at + timedelta(minutes=15)
            )

            if otp_has_expired:

                messages.error(
                    request,
                    'This code has expired. Please ask the admin to send a new verification code.'
                )

            elif entered_otp == user.otp_code:

                user.is_email_verified = True
                user.is_approved = True
                user.is_active = True
                user.otp_code = None
                user.otp_created_at = None
                user.save()

                notify_admin_user_verified(
                    request,
                    user
                )

                messages.success(
                    request,
                    'Verification successful. You are now signed in.'
                )

                login(
                    request,
                    user,
                    backend='django.contrib.auth.backends.ModelBackend'
                )

                return redirect('dashboard')

            else:

                messages.error(
                    request,
                    'Invalid verification code.'
                )

    else:

        form = OTPVerificationForm()

    return render(
        request,
        'accounts/verify_otp.html',
        {
            'form': form,
            'user_obj': user
        }
    )


def pending_approval(request):

    return render(
        request,
        'accounts/pending_approval.html'
    )


@login_required
def send_user_verification_code(request, user_id, channel='email'):

    if request.user.role != 'admin':

        messages.error(
            request,
            'Only administrators can send verification codes.'
        )

        return redirect('dashboard')

    user = get_object_or_404(
        User,
        id=user_id,
        role__in=[
            'student',
            'employer'
        ],
        is_approved=False
    )

    if user.is_email_verified:

        messages.info(
            request,
            f'{user.username} is already verified and can now be approved.'
        )

        return redirect('dashboard')

    valid_channels = [
        'email',
        'whatsapp',
        'sms',
    ]

    if channel not in valid_channels:

        messages.error(
            request,
            'Invalid verification channel.'
        )

        return redirect('dashboard')

    delivery_results = []
    delivery_failed = False
    successful_deliveries = 0

    if channel in [
        'email',
    ]:

        email_success, email_message = send_otp_email(
            request,
            user
        )

        delivery_results.append(
            f'Email: {email_message}'
        )

        if not email_success:
            delivery_failed = True
        else:
            successful_deliveries += 1

    else:

        user.generate_otp()

    if channel in [
        'whatsapp',
    ]:

        whatsapp_success, whatsapp_message = send_registration_whatsapp_otp(user)

        delivery_results.append(
            f'WhatsApp: {whatsapp_message}'
        )

        if not whatsapp_success:
            delivery_failed = True
        else:
            successful_deliveries += 1

    if channel == 'sms':

        sms_success, sms_message = send_registration_sms_otp(user)

        delivery_results.append(
            f'SMS: {sms_message}'
        )

        if not sms_success:
            delivery_failed = True
        else:
            successful_deliveries += 1

    result_message = ' '.join(delivery_results)

    if successful_deliveries == 0:

        user.otp_code = None
        user.otp_created_at = None
        user.save()

        messages.error(
            request,
            f'No verification code was delivered to {user.username}. {result_message}'
        )

        return redirect('dashboard')

    if delivery_failed:

        messages.warning(
            request,
            f'Verification code process completed for {user.username}, but one channel failed. {result_message}'
        )

    else:

        messages.success(
            request,
            f'Verification code sent to {user.username}. {result_message}'
        )

    return redirect('dashboard')


@login_required
def approve_user(request, user_id):

    if request.user.role != 'admin':

        messages.error(
            request,
            'Only administrators can approve users.'
        )

        return redirect('dashboard')

    user = get_object_or_404(
        User,
        id=user_id
    )

    if not user.is_email_verified:

        messages.error(
            request,
            'This user must enter the admin-generated verification code. Successful verification activates the account automatically.'
        )

        return redirect('dashboard')

    user.is_approved = True
    user.is_active = True
    user.save()

    Notification.objects.create(
        user=user,
        message='Your account has been approved. You can now login and access your dashboard.'
    )

    send_system_email(
        subject='Account Approved',
        message=(
            f'Hello {user.username},\n\n'
            f'Your account has been approved successfully.\n\n'
            f'You can now login and access your dashboard.\n\n'
            f'AI Internship & Attachment Matching System'
        ),
        recipient_list=[
            user.email
        ],
        button_text='Login to Dashboard',
        button_url=build_absolute_url(
            request,
            'login'
        )
    )

    messages.success(
        request,
        f'{user.username} approved successfully. Email notification sent.'
    )

    return redirect('dashboard')


@login_required
def reject_user(request, user_id):

    if request.user.role != 'admin':

        messages.error(
            request,
            'Only administrators can reject users.'
        )

        return redirect('dashboard')

    user = User.objects.filter(
        id=user_id
    ).first()

    if user is None:

        messages.error(
            request,
            'User does not exist.'
        )

        return redirect('dashboard')

    if user.role == 'admin':

        messages.error(
            request,
            'Admin account cannot be rejected here.'
        )

        return redirect('dashboard')

    username = user.username
    user_email = user.email

    send_system_email(
        subject='Account Registration Rejected',
        message=(
            f'Hello {username},\n\n'
            f'Your account registration was not approved.\n\n'
            f'If you believe this was a mistake, please contact the system administrator.\n\n'
            f'AI Internship & Attachment Matching System'
        ),
        recipient_list=[
            user_email
        ]
    )

    user.delete()

    messages.warning(
        request,
        f'{username} has been rejected and removed. Email notification sent.'
    )

    return redirect('dashboard')


@login_required
def delete_user_account(request, user_id):

    if request.user.role != 'admin':

        messages.error(
            request,
            'Only admin can delete users.'
        )

        return redirect('dashboard')

    user = User.objects.filter(
        id=user_id
    ).first()

    if user is None:

        messages.error(
            request,
            'User does not exist.'
        )

        return redirect('dashboard')

    if user.role == 'admin':

        messages.error(
            request,
            'Admin account cannot be deleted here.'
        )

        return redirect('dashboard')

    username = user.username
    user_role = user.role

    user.delete()

    messages.success(
        request,
        f'{username} ({user_role}) deleted successfully.'
    )

    return redirect('dashboard')


@login_required
def logout_user(request):

    logout(request)

    return redirect('login')
