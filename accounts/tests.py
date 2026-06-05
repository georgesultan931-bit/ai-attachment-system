from django.test import TestCase
from django.test import RequestFactory
from django.test import override_settings
from django.urls import reverse

from notifications.models import Notification

from .models import User
from .views import (
    build_absolute_url,
    notify_admin_new_registration
)


class RegistrationNotificationTests(TestCase):

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
