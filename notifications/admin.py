from django.contrib import admin, messages

from .email_service import send_system_email

from .models import (
    Notification,
    EmailConfiguration,
    EmailLog,
    SMSConfiguration,
    SMSLog,
    WhatsAppConfiguration,
    WhatsAppLog
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'message',
        'is_read',
        'created_at',
    )

    list_filter = (
        'is_read',
        'created_at',
    )

    search_fields = (
        'user__username',
        'message',
    )


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):

    list_display = (
        'email_host_user',
        'admin_notification_email',
        'email_host',
        'email_port',
        'is_active',
        'updated_at',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'email_host_user',
        'admin_notification_email',
    )

    actions = [
        'send_test_email',
        'activate_selected_configuration',
    ]

    def send_test_email(self, request, queryset):

        for config in queryset:

            config.is_active = True
            config.save()

            success, response_message = send_system_email(
                subject='SMTP Test Email',
                message=(
                    'This is a test email from the AI Internship & Attachment System.\n\n'
                    'If you received this email, your SMTP configuration is working correctly.'
                ),
                recipient_list=[
                    config.admin_notification_email
                ]
            )

            if success:

                self.message_user(
                    request,
                    f'Test email sent successfully to {config.admin_notification_email}.',
                    level=messages.SUCCESS
                )

            else:

                self.message_user(
                    request,
                    f'Test email failed: {response_message}',
                    level=messages.ERROR
                )

    send_test_email.short_description = (
        'Send test email using selected SMTP configuration'
    )

    def activate_selected_configuration(self, request, queryset):

        for config in queryset:

            config.is_active = True
            config.save()

        self.message_user(
            request,
            'Selected SMTP configuration activated successfully.',
            level=messages.SUCCESS
        )

    activate_selected_configuration.short_description = (
        'Activate selected SMTP configuration'
    )


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):

    list_display = (
        'recipient',
        'subject',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'recipient',
        'subject',
        'message',
        'error_message',
    )

    readonly_fields = (
        'recipient',
        'subject',
        'message',
        'status',
        'error_message',
        'created_at',
    )

    ordering = (
        '-created_at',
    )


@admin.register(WhatsAppConfiguration)
class WhatsAppConfigurationAdmin(admin.ModelAdmin):

    list_display = (
        'phone_number_id',
        'registration_template_name',
        'language_code',
        'default_country_code',
        'is_active',
        'updated_at',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'phone_number_id',
        'registration_template_name',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )


@admin.register(WhatsAppLog)
class WhatsAppLogAdmin(admin.ModelAdmin):

    list_display = (
        'recipient',
        'template_name',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'recipient',
        'template_name',
        'message',
        'response_message',
    )

    readonly_fields = (
        'recipient',
        'template_name',
        'message',
        'status',
        'response_message',
        'created_at',
    )

    ordering = (
        '-created_at',
    )


@admin.register(SMSConfiguration)
class SMSConfigurationAdmin(admin.ModelAdmin):

    list_display = (
        'username',
        'sender_id',
        'default_country_code',
        'is_active',
        'updated_at',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'username',
        'sender_id',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):

    list_display = (
        'recipient',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'recipient',
        'message',
        'response_message',
    )

    readonly_fields = (
        'recipient',
        'message',
        'status',
        'response_message',
        'created_at',
    )

    ordering = (
        '-created_at',
    )
