from django.conf import settings
from django.db import models


class Notification(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.message


class EmailConfiguration(models.Model):

    email_host = models.CharField(
        max_length=255,
        default='smtp.gmail.com'
    )

    email_port = models.PositiveIntegerField(
        default=587
    )

    email_use_tls = models.BooleanField(
        default=True
    )

    email_host_user = models.EmailField(
        help_text='Example: yourcompany@gmail.com'
    )

    email_host_password = models.CharField(
        max_length=255,
        help_text='Use Gmail App Password, not normal Gmail password.'
    )

    default_from_email = models.EmailField()

    admin_notification_email = models.EmailField(
        help_text='Admin email that receives new registration alerts.'
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):

        if self.is_active:

            EmailConfiguration.objects.exclude(
                id=self.id
            ).update(
                is_active=False
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.email_host_user


class EmailLog(models.Model):

    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )

    recipient = models.EmailField()

    subject = models.CharField(
        max_length=255
    )

    message = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    error_message = models.TextField(
        blank=True,
        default=''
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.recipient} - {self.status}'


class WhatsAppConfiguration(models.Model):

    access_token = models.TextField(
        help_text='Permanent Meta WhatsApp Cloud API access token.'
    )

    phone_number_id = models.CharField(
        max_length=100,
        help_text='Meta WhatsApp Cloud API Phone Number ID.'
    )

    registration_template_name = models.CharField(
        max_length=100,
        default='registration_otp',
        help_text='Approved WhatsApp template name for registration OTP messages.'
    )

    language_code = models.CharField(
        max_length=20,
        default='en_US'
    )

    default_country_code = models.CharField(
        max_length=5,
        default='254',
        help_text='Used when users enter local phone numbers, e.g. 254 for Kenya.'
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):

        if self.is_active:

            WhatsAppConfiguration.objects.exclude(
                id=self.id
            ).update(
                is_active=False
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.phone_number_id


class WhatsAppLog(models.Model):

    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )

    recipient = models.CharField(
        max_length=30
    )

    template_name = models.CharField(
        max_length=100
    )

    message = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    response_message = models.TextField(
        blank=True,
        default=''
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.recipient} - {self.status}'


class SMSConfiguration(models.Model):

    username = models.CharField(
        max_length=100,
        help_text='Africa\'s Talking username. Use sandbox for testing.'
    )

    api_key = models.TextField(
        help_text='Africa\'s Talking API key.'
    )

    sender_id = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text='Optional approved sender ID or shortcode.'
    )

    default_country_code = models.CharField(
        max_length=5,
        default='254',
        help_text='Used when users enter local phone numbers, e.g. 254 for Kenya.'
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):

        if self.is_active:

            SMSConfiguration.objects.exclude(
                id=self.id
            ).update(
                is_active=False
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class SMSLog(models.Model):

    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )

    recipient = models.CharField(
        max_length=30
    )

    message = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    response_message = models.TextField(
        blank=True,
        default=''
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.recipient} - {self.status}'
