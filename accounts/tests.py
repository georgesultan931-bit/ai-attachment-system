from django.test import TestCase
from django.test import RequestFactory

from notifications.models import Notification

from .models import User
from .views import notify_admin_new_registration


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
