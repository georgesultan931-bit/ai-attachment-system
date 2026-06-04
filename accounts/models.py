from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

import random


class User(AbstractUser):

    ROLE_CHOICES = (
        ('student', 'Student'),
        ('employer', 'Employer'),
        ('admin', 'Admin'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    email = models.EmailField(
        unique=True
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )

    is_email_verified = models.BooleanField(
        default=False
    )

    is_approved = models.BooleanField(
        default=False
    )

    otp_code = models.CharField(
        max_length=6,
        blank=True,
        null=True
    )

    otp_created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def generate_otp(self):

        self.otp_code = str(
            random.randint(
                100000,
                999999
            )
        )

        self.otp_created_at = timezone.now()
        self.save()

        return self.otp_code

    def __str__(self):
        return self.username
