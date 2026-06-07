from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.test import RequestFactory
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.core import signing

from notifications.models import (
    EmailLog,
    Notification
)
from notifications.context_processors import notification_count
from notifications.email_service import get_active_email_config
from notifications.email_service import send_system_email
from employers.models import EmployerProfile
from students.models import StudentProfile

from .models import User
from .auth_flow import (
    authenticate_identifier,
    clean_login_value,
    dashboard_redirect_name,
)
from .forms import (
    CustomLoginForm,
    EmployerRegistrationForm,
    OTPVerificationForm,
    StudentRegistrationForm,
)
from .views import (
    build_absolute_url,
    notify_admin_new_registration,
    REGISTRATION_VERIFY_SALT
)


class RegistrationNotificationTests(TestCase):

    def test_clean_login_value_removes_phone_keyboard_noise(self):

        self.assertEqual(
            clean_login_value(' \ufeffPy\u200bthon '),
            'Python'
        )

    def test_authenticate_identifier_accepts_inactive_otp_user(self):

        user = User.objects.create_user(
            username='python',
            email='python-user@example.com',
            password='Testpass12345',
            role='student',
            is_active=False,
            is_approved=False,
            is_email_verified=False
        )

        response = authenticate_identifier(
            None,
            ' Python ',
            '\u200bTestpass12345\ufeff'
        )

        self.assertEqual(
            response.user,
            user
        )
        self.assertEqual(
            response.reason,
            'inactive_or_unverified'
        )

    def test_custom_login_form_accepts_phone_keyboard_hidden_characters(self):

        User.objects.create_user(
            username='formuser',
            email='form-user@example.com',
            password='Testpass12345',
            role='student',
            is_active=True,
            is_approved=True,
            is_email_verified=True
        )

        form = CustomLoginForm(
            data={
                'username': '  form-user@example.com\u200e  ',
                'password': '\u200bTestpass12345\u2060',
            }
        )

        self.assertTrue(
            form.is_valid(),
            form.errors.as_data()
        )

    def test_dashboard_redirect_sends_profileless_student_to_profile(self):

        user = User.objects.create_user(
            username='profileless',
            email='profileless@example.com',
            password='Testpass12345',
            role='student',
            is_active=True,
            is_approved=True,
            is_email_verified=True
        )

        self.assertEqual(
            dashboard_redirect_name(user),
            'create_student_profile'
        )

    def test_dashboard_redirect_sends_student_with_profile_to_dashboard(self):

        user = User.objects.create_user(
            username='student_with_profile',
            email='student-profile@example.com',
            password='Testpass12345',
            role='student',
            is_active=True,
            is_approved=True,
            is_email_verified=True
        )

        StudentProfile.objects.create(
            user=user,
            first_name='Amina',
            surname='Hassan',
            phone_number='0712345678',
            location='Nairobi'
        )

        self.assertEqual(
            dashboard_redirect_name(user),
            'student_dashboard'
        )

    def test_dashboard_redirect_sends_employer_with_profile_to_dashboard(self):

        user = User.objects.create_user(
            username='employer_with_profile',
            email='employer-profile@example.com',
            password='Testpass12345',
            role='employer',
            is_active=True,
            is_approved=True,
            is_email_verified=True
        )

        EmployerProfile.objects.create(
            user=user,
            company_name='Acme Ltd',
            company_email='acme@example.com',
            company_phone='0712345678',
            company_location='Nairobi',
            industry='Technology',
            company_description='Hiring interns.'
        )

        self.assertEqual(
            dashboard_redirect_name(user),
            'employer_profile'
        )

    def test_sidebar_uses_employer_logo_url(self):

        user = User.objects.create_user(
            username='logo_employer',
            email='logo-employer@example.com',
            password='Testpass12345',
            role='employer',
            is_active=True,
            is_approved=True,
            is_email_verified=True
        )

        EmployerProfile.objects.create(
            user=user,
            company_name='Logo Ltd',
            company_email='logo@example.com',
            company_phone='0712345678',
            company_location='Nairobi',
            industry='Technology',
            company_description='Logo test.',
            logo='company_logos/logo.png'
        )

        request = RequestFactory().get('/')
        request.user = user

        context = notification_count(request)

        self.assertEqual(
            context['dashboard_profile_image_url'],
            '/media/company_logos/logo.png'
        )

    def test_phone_input_attributes_are_mobile_safe(self):

        forms_and_fields = [
            (CustomLoginForm(), ['username', 'password']),
            (StudentRegistrationForm(), ['username', 'email', 'phone_number', 'password1', 'password2']),
            (EmployerRegistrationForm(), ['username', 'email', 'phone_number', 'password1', 'password2']),
            (OTPVerificationForm(), ['otp_code']),
        ]

        for form, field_names in forms_and_fields:
            for field_name in field_names:
                attrs = form.fields[field_name].widget.attrs

                self.assertEqual(
                    attrs.get('autocapitalize'),
                    'none',
                    f'{form.__class__.__name__}.{field_name} must not autocapitalize on phone.'
                )
                self.assertEqual(
                    attrs.get('autocorrect'),
                    'off',
                    f'{form.__class__.__name__}.{field_name} must not autocorrect on phone.'
                )
                self.assertEqual(
                    attrs.get('spellcheck'),
                    'false',
                    f'{form.__class__.__name__}.{field_name} must not spellcheck on phone.'
                )

    def test_registration_creates_admin_notification_without_email_config(self):

        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='Testpass12345',
            role='admin',
            is_active=True
        )

        user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='Testpass12345',
            role='student',
            phone_number='0712345678',
            is_active=False,
            is_approved=False,
            is_email_verified=False
        )

        request = RequestFactory().get('/')
        request.META['HTTP_HOST'] = 'testserver'

        success, message = notify_admin_new_registration(
            request,
            user
        )

        self.assertTrue(success)
        self.assertIn(
            'Dashboard notification created',
            message
        )
        self.assertTrue(
            Notification.objects.filter(
                user=admin,
                message__contains='New student registration'
            ).exists()
        )

    @override_settings(PUBLIC_SITE_URL='https://ai-attachment-system.onrender.com')
    def test_public_site_url_is_used_for_email_links(self):

        request = RequestFactory().get('/')
        request.META['HTTP_HOST'] = 'testserver'

        url = build_absolute_url(
            request,
            'dashboard'
        )

        self.assertEqual(
            url,
            'https://ai-attachment-system.onrender.com/dashboard/'
        )

    def test_admin_dashboard_exposes_pending_and_recent_registrations(self):

        admin = User.objects.create_user(
            username='dashboard_admin',
            email='dashboard-admin@example.com',
            password='Testpass12345',
            role='admin',
            is_active=True
        )

        user = User.objects.create_user(
            username='new_student',
            email='new-student@example.com',
            password='Testpass12345',
            role='student',
            phone_number='0712345678',
            is_active=False,
            is_approved=False,
            is_email_verified=False
        )

        self.client.force_login(admin)

        response = self.client.get(
            reverse('dashboard')
        )

        self.assertEqual(
            response.status_code,
            200
        )
        self.assertIn(
            user,
            list(response.context['pending_users'])
        )
        self.assertIn(
            user,
            list(response.context['latest_registration_otps'])
        )
        self.assertIn(
            user,
            list(response.context['recent_registered_users'])
        )
        self.assertEqual(
            response.context['total_registered_accounts'],
            1
        )
        self.assertEqual(
            response.context['pending_registration_count'],
            1
        )

    def test_registration_without_email_config_goes_to_pending_approval(self):

        admin = User.objects.create_user(
            username='registration_admin',
            email='registration-admin@example.com',
            password='Testpass12345',
            role='admin',
            is_active=True
        )

        response = self.client.post(
            reverse('student_register'),
            {
                'username': 'otp_student',
                'email': 'otp-student@example.com',
                'phone_number': '0712345678',
                'password1': 'Testpass12345',
                'password2': 'Testpass12345',
            }
        )

        user = User.objects.get(
            username='otp_student'
        )

        self.assertRedirects(
            response,
            reverse('pending_approval')
        )
        self.assertIsNone(user.otp_code)
        self.assertFalse(user.is_email_verified)
        self.assertFalse(user.is_approved)
        self.assertFalse(user.is_active)
        self.assertTrue(
            EmailLog.objects.filter(
                recipient='otp-student@example.com',
                subject='Verify Your Registration',
                status='failed',
                error_message='No active email configuration found.'
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                user=admin,
                message__contains='Verification email'
            ).exists()
        )

    def test_registration_email_link_verifies_and_opens_profile(self):

        user = User.objects.create_user(
            username='email_link_student',
            email='email-link-student@example.com',
            password='Testpass12345',
            role='student',
            phone_number='0712345678',
            is_active=False,
            is_approved=False,
            is_email_verified=False
        )

        token = signing.dumps(
            {
                'user_id': user.id
            },
            salt=REGISTRATION_VERIFY_SALT
        )

        response = self.client.get(
            reverse(
                'verify_registration_email',
                args=[
                    token
                ]
            )
        )

        user.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('create_student_profile'),
            fetch_redirect_response=False
        )
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.is_approved)
        self.assertTrue(user.is_active)
        self.assertIsNone(user.otp_code)

    def test_login_accepts_email_and_phone_keyboard_hidden_characters(self):

        User.objects.create_user(
            username='phoneuser',
            email='phone-user@example.com',
            password='Testpass12345',
            role='student',
            is_active=True,
            is_approved=True,
            is_email_verified=True
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': '  phone-user@example.com\ufeff  ',
                'password': '\u200bTestpass12345\u2060',
            }
        )

        self.assertRedirects(
            response,
            reverse('create_student_profile'),
            fetch_redirect_response=False
        )

    def test_login_page_is_not_cached_so_csrf_token_stays_fresh(self):

        response = self.client.get(
            reverse('login')
        )

        self.assertContains(
            response,
            'csrfmiddlewaretoken'
        )
        self.assertIn(
            'no-cache',
            response.headers.get('Cache-Control', '')
        )
        self.assertIn(
            'no-store',
            response.headers.get('Cache-Control', '')
        )

    def test_registration_trims_phone_keyboard_spaces(self):

        response = self.client.post(
            reverse('student_register'),
            {
                'username': '  spaceduser  ',
                'email': '  SPACED-USER@EXAMPLE.COM  ',
                'phone_number': ' 0712345678 ',
                'password1': 'Testpass12345',
                'password2': 'Testpass12345',
            }
        )

        user = User.objects.get(
            username='spaceduser'
        )

        self.assertRedirects(
            response,
            reverse('pending_approval')
        )
        self.assertEqual(
            user.email,
            'spaced-user@example.com'
        )
        self.assertEqual(
            user.phone_number,
            '0712345678'
        )

    def test_login_accepts_username_case_insensitively(self):

        User.objects.create_user(
            username='caseuser',
            email='case-user@example.com',
            password='Testpass12345',
            role='student',
            is_active=True,
            is_approved=True,
            is_email_verified=True
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': 'CaseUser',
                'password': 'Testpass12345',
            }
        )

        self.assertRedirects(
            response,
            reverse('create_student_profile'),
            fetch_redirect_response=False
        )

    def test_unapproved_inactive_user_login_redirects_to_pending_approval(self):

        user = User.objects.create_user(
            username='python',
            email='python-user@example.com',
            password='Testpass12345',
            role='student',
            phone_number='0712345678',
            is_active=False,
            is_approved=False,
            is_email_verified=False
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': ' Python ',
                'password': 'Testpass12345\u200d',
            }
        )

        self.assertRedirects(
            response,
            reverse('pending_approval'),
            fetch_redirect_response=False
        )

    def test_email_config_can_fall_back_to_environment(self):

        with patch.dict(
            'os.environ',
            {
                'EMAIL_HOST': 'smtp.gmail.com',
                'EMAIL_PORT': '587',
                'EMAIL_USE_TLS': 'True',
                'EMAIL_HOST_USER': 'sender@example.com',
                'EMAIL_HOST_PASSWORD': 'app-password',
                'DEFAULT_FROM_EMAIL': 'sender@example.com',
                'ADMIN_NOTIFICATION_EMAIL': 'admin@example.com',
            }
        ):

            config = get_active_email_config()

        self.assertEqual(
            config.email_host,
            'smtp.gmail.com'
        )
        self.assertEqual(
            config.email_host_user,
            'sender@example.com'
        )
        self.assertEqual(
            config.admin_notification_email,
            'admin@example.com'
        )

    def test_email_config_accepts_original_email_user_aliases(self):

        with patch.dict(
            'os.environ',
            {
                'EMAIL_HOST': 'smtp.gmail.com',
                'EMAIL_PORT': '587',
                'EMAIL_USE_TLS': 'True',
                'EMAIL_USER': 'original-sender@example.com',
                'EMAIL_PASS': 'original-app-password',
            },
            clear=True
        ):

            config = get_active_email_config()

        self.assertEqual(
            config.email_host_user,
            'original-sender@example.com'
        )
        self.assertEqual(
            config.email_host_password,
            'original-app-password'
        )
        self.assertEqual(
            config.default_from_email,
            'original-sender@example.com'
        )

    def test_missing_email_config_creates_failed_email_log(self):

        success, message = send_system_email(
            subject='Missing Config Test',
            message='Test body',
            recipient_list=[
                'student@example.com'
            ]
        )

        self.assertFalse(success)
        self.assertEqual(
            message,
            'No active email configuration found.'
        )
        self.assertTrue(
            EmailLog.objects.filter(
                recipient='student@example.com',
                subject='Missing Config Test',
                status='failed',
                error_message='No active email configuration found.'
            ).exists()
        )

    def test_email_retries_with_insecure_smtp_on_certificate_error(self):

        with patch.dict(
            'os.environ',
            {
                'EMAIL_HOST': 'smtp.gmail.com',
                'EMAIL_PORT': '587',
                'EMAIL_USE_TLS': 'True',
                'EMAIL_HOST_USER': 'sender@example.com',
                'EMAIL_HOST_PASSWORD': 'app-password',
                'DEFAULT_FROM_EMAIL': 'sender@example.com',
            }
        ):
            with patch(
                'notifications.email_service._send_email_once',
                side_effect=[
                    Exception('[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed'),
                    None,
                ]
            ) as send_once:
                success, message = send_system_email(
                    subject='Retry Certificate Test',
                    message='Test body',
                    recipient_list=[
                        'student@example.com'
                    ]
                )

        self.assertTrue(success)
        self.assertIn(
            'Email sent successfully',
            message
        )
        self.assertEqual(
            send_once.call_count,
            2
        )
        self.assertTrue(
            send_once.call_args_list[1].kwargs['allow_insecure_ssl']
        )
        self.assertTrue(
            EmailLog.objects.filter(
                recipient='student@example.com',
                subject='Retry Certificate Test',
                status='sent'
            ).exists()
        )

    def test_otp_verification_activates_and_logs_in_user(self):

        user = User.objects.create_user(
            username='approval_student',
            email='approval-student@example.com',
            password='Testpass12345',
            role='student',
            phone_number='0712345678',
            is_active=False,
            is_approved=False,
            is_email_verified=False
        )
        otp = user.generate_otp()

        response = self.client.post(
            reverse(
                'verify_otp',
                args=[
                    user.id
                ]
            ),
            {
                'otp_code': otp
            }
        )

        user.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('create_student_profile'),
            fetch_redirect_response=False
        )
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.is_approved)
        self.assertTrue(user.is_active)

    def test_otp_verification_accepts_phone_formatted_code(self):

        user = User.objects.create_user(
            username='phone_otp_student',
            email='phone-otp-student@example.com',
            password='Testpass12345',
            role='student',
            phone_number='0712345678',
            is_active=False,
            is_approved=False,
            is_email_verified=False
        )
        user.otp_code = '123456'
        user.otp_created_at = timezone.now()
        user.save()

        response = self.client.post(
            reverse(
                'verify_otp',
                args=[
                    user.id
                ]
            ),
            {
                'otp_code': '123 456'
            }
        )

        user.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('create_student_profile'),
            fetch_redirect_response=False
        )
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.is_approved)
        self.assertTrue(user.is_active)

    def test_admin_can_verify_and_activate_pending_user(self):

        admin = User.objects.create_user(
            username='verify_admin',
            email='verify-admin@example.com',
            password='Testpass12345',
            role='admin',
            is_active=True
        )

        user = User.objects.create_user(
            username='admin_verified_student',
            email='admin-verified-student@example.com',
            password='Testpass12345',
            role='student',
            phone_number='0712345678',
            is_active=False,
            is_approved=False,
            is_email_verified=False
        )
        user.generate_otp()

        self.client.force_login(admin)

        response = self.client.get(
            reverse(
                'admin_verify_user',
                args=[
                    user.id
                ]
            )
        )

        user.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('dashboard'),
            fetch_redirect_response=False
        )
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.is_approved)
        self.assertTrue(user.is_active)
        self.assertIsNone(user.otp_code)

    def test_admin_can_reset_user_password_for_phone_and_laptop_login(self):

        admin = User.objects.create_user(
            username='reset_admin',
            email='reset-admin@example.com',
            password='Testpass12345',
            role='admin',
            is_active=True
        )

        user = User.objects.create_user(
            username='reset_student',
            email='reset-student@example.com',
            password='Oldpass12345',
            role='student',
            phone_number='0712345678',
            is_active=True,
            is_approved=True,
            is_email_verified=True
        )

        self.client.force_login(admin)

        response = self.client.get(
            reverse(
                'admin_reset_user_password',
                args=[
                    user.id
                ]
            )
        )

        user.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('dashboard'),
            fetch_redirect_response=False
        )
        self.assertTrue(
            user.check_password('Testpass12345')
        )

    def test_ensure_admin_creates_admin_when_password_is_supplied(self):

        out = StringIO()

        call_command(
            'ensure_admin',
            username='admin',
            email='admin@example.com',
            password='AdminPass12345!',
            stdout=out,
        )

        user = User.objects.get(username='admin')

        self.assertEqual(user.email, 'admin@example.com')
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.is_approved)
        self.assertTrue(user.check_password('AdminPass12345!'))
        self.assertIn(
            'Created admin account admin',
            out.getvalue()
        )

    def test_ensure_admin_does_not_change_existing_password_by_default(self):

        User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='OriginalPass12345!',
            role='student',
            is_active=False,
            is_approved=False,
            is_email_verified=False,
            is_staff=False,
            is_superuser=False,
        )

        out = StringIO()

        call_command(
            'ensure_admin',
            username='admin',
            email='admin@example.com',
            password='NewPass12345!',
            stdout=out,
        )

        user = User.objects.get(username='admin')

        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.is_approved)
        self.assertTrue(user.check_password('OriginalPass12345!'))
        self.assertFalse(user.check_password('NewPass12345!'))
        self.assertIn(
            'Password was not changed',
            out.getvalue()
        )

    def test_admin_can_delete_only_old_pending_accounts(self):

        admin = User.objects.create_user(
            username='cleanup_admin',
            email='cleanup-admin@example.com',
            password='Testpass12345',
            role='admin',
            is_active=True
        )

        pending_user = User.objects.create_user(
            username='old_pending_student',
            email='old-pending-student@example.com',
            password='Testpass12345',
            role='student',
            is_active=False,
            is_approved=False,
            is_email_verified=False
        )

        active_user = User.objects.create_user(
            username='active_student',
            email='active-student@example.com',
            password='Testpass12345',
            role='student',
            is_active=True,
            is_approved=True,
            is_email_verified=True
        )

        self.client.force_login(admin)

        response = self.client.get(
            reverse('delete_old_pending_accounts')
        )

        self.assertRedirects(
            response,
            reverse('dashboard'),
            fetch_redirect_response=False
        )
        self.assertFalse(
            User.objects.filter(id=pending_user.id).exists()
        )
        self.assertTrue(
            User.objects.filter(id=active_user.id).exists()
        )
        self.assertTrue(
            User.objects.filter(id=admin.id).exists()
        )
