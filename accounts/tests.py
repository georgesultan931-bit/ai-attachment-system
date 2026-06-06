from unittest.mock import patch

from django.test import TestCase
from django.test import RequestFactory
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from notifications.models import (
    EmailLog,
    Notification
)
from notifications.email_service import get_active_email_config
from notifications.email_service import send_system_email

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
    notify_admin_new_registration
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
            ' Testpass12345 '
        )

        self.assertEqual(
            response.user,
            user
        )
        self.assertEqual(
            response.reason,
            'inactive_or_unverified'
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

    def test_registration_without_email_config_still_goes_to_otp_page(self):

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
            reverse(
                'verify_otp',
                args=[
                    user.id
                ]
            )
        )
        self.assertTrue(user.otp_code)
        self.assertFalse(user.is_email_verified)
        self.assertFalse(user.is_approved)
        self.assertFalse(user.is_active)
        self.assertTrue(
            EmailLog.objects.filter(
                recipient='otp-student@example.com',
                subject='Verify Your Email Address',
                status='failed',
                error_message='No active email configuration found.'
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                user=admin,
                message__contains=user.otp_code
            ).exists()
        )

    def test_login_accepts_email_and_trims_phone_keyboard_spaces(self):

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
                'username': '  phone-user@example.com  ',
                'password': ' Testpass12345 ',
            }
        )

        self.assertRedirects(
            response,
            reverse('create_student_profile'),
            fetch_redirect_response=False
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
            reverse(
                'verify_otp',
                args=[
                    user.id
                ]
            )
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

    def test_unverified_inactive_user_login_redirects_to_otp(self):

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
        user.generate_otp()

        response = self.client.post(
            reverse('login'),
            {
                'username': ' Python ',
                'password': ' Testpass12345 ',
            }
        )

        self.assertRedirects(
            response,
            reverse(
                'verify_otp',
                args=[
                    user.id
                ]
            ),
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
