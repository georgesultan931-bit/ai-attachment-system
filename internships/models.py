from django.conf import settings
from django.db import models
from django.utils import timezone

from employers.models import EmployerProfile
from students.models import StudentProfile


class InternshipOpportunity(models.Model):

    INTERNSHIP_TYPE_CHOICES = (
        ('attachment', 'Industrial Attachment'),
        ('internship', 'Internship'),
        ('graduate_trainee', 'Graduate Trainee'),
    )

    STATUS_CHOICES = (
        ('open', 'Open'),
        ('closed', 'Closed'),
    )

    employer = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        related_name='opportunities'
    )

    company_name = models.CharField(
        max_length=255,
        blank=True
    )

    company_email = models.EmailField(
        blank=True
    )

    company_image = models.ImageField(
        upload_to='opportunity_company_images/',
        blank=True,
        null=True
    )

    title = models.CharField(
        max_length=255
    )

    internship_type = models.CharField(
        max_length=30,
        choices=INTERNSHIP_TYPE_CHOICES
    )

    description = models.TextField()

    required_skills = models.TextField()

    location = models.CharField(
        max_length=255
    )

    slots_available = models.PositiveIntegerField()

    deadline = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    @property
    def display_company_name(self):
        return self.company_name or self.employer.company_name

    @property
    def display_company_email(self):
        return self.company_email or self.employer.company_email

    @property
    def display_company_image(self):
        return self.company_image or self.employer.logo

    def is_expired(self):
        return self.deadline < timezone.localdate()

    def is_open_for_applications(self):
        return self.status == 'open' and not self.is_expired()

    def __str__(self):
        return self.title


class Application(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    INTERVIEW_RESPONSE_CHOICES = (
        ('pending', 'Pending Response'),
        ('accepted', 'Accepted Interview'),
        ('declined', 'Declined Interview'),
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )

    opportunity = models.ForeignKey(
        InternshipOpportunity,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending'
    )

    interview_date = models.DateField(
        blank=True,
        null=True
    )

    interview_time = models.TimeField(
        blank=True,
        null=True
    )

    interview_location = models.CharField(
        max_length=255,
        blank=True
    )

    interview_notes = models.TextField(
        blank=True
    )

    interview_response = models.CharField(
        max_length=30,
        choices=INTERVIEW_RESPONSE_CHOICES,
        default='pending'
    )

    interview_response_note = models.TextField(
        blank=True
    )

    applied_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.student.user.username} - {self.opportunity.title}"


class ApplicationMessage(models.Model):

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_application_messages'
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username} - {self.application.opportunity.title}'
