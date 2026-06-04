from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        'username',
        'email',
        'role',
        'phone_number',
        'is_email_verified',
        'is_approved',
        'is_active',
        'is_staff',
    )

    list_filter = (
        'role',
        'is_email_verified',
        'is_approved',
        'is_active',
        'is_staff',
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            'Approval & Verification',
            {
                'fields': (
                    'role',
                    'phone_number',
                    'is_email_verified',
                    'is_approved',
                    'otp_code',
                )
            }
        ),
    )

    actions = [
        'approve_users',
    ]

    def approve_users(self, request, queryset):
        queryset.update(
            is_email_verified=True,
            is_approved=True,
            is_active=True
        )

    approve_users.short_description = 'Approve selected users'