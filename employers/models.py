from django.db import models
from django.conf import settings


class EmployerProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    company_name = models.CharField(
        max_length=255
    )

    company_email = models.EmailField(
        unique=True
    )

    company_phone = models.CharField(
        max_length=15
    )

    company_location = models.CharField(
        max_length=255
    )

    industry = models.CharField(
        max_length=255
    )

    company_description = models.TextField()

    website = models.URLField(
        blank=True,
        null=True
    )

    logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.company_name