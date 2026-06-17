from django.db import models
from django.conf import settings


class StudentProfile(models.Model):

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    DISABILITY_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
    )

    SALUTATION_CHOICES = (
        ('Mr', 'Mr'),
        ('Mrs', 'Mrs'),
        ('Miss', 'Miss'),
        ('Dr', 'Dr'),
        ('Prof', 'Prof'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    id_number = models.CharField(max_length=50, blank=True, default='')
    huduma_number = models.CharField(max_length=50, blank=True, default='')

    salutation = models.CharField(
        max_length=20,
        choices=SALUTATION_CHOICES,
        blank=True,
        default='Mr'
    )

    surname = models.CharField(max_length=100, blank=True, default='')
    first_name = models.CharField(max_length=100, blank=True, default='')
    other_names = models.CharField(max_length=150, blank=True, default='')

    date_of_birth = models.DateField(blank=True, null=True)

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
        default='male'
    )

    kra_pin = models.CharField(max_length=50, blank=True, default='')
    nationality = models.CharField(max_length=100, blank=True, default='')
    ethnicity = models.CharField(max_length=100, blank=True, default='')

    disability = models.CharField(
        max_length=10,
        choices=DISABILITY_CHOICES,
        blank=True,
        default='no'
    )

    home_county = models.CharField(max_length=100, blank=True, default='')
    home_constituency = models.CharField(max_length=100, blank=True, default='')
    sub_county = models.CharField(max_length=100, blank=True, default='')
    home_ward = models.CharField(max_length=100, blank=True, default='')

    postal_address = models.CharField(max_length=100, blank=True, default='')
    postal_code = models.CharField(max_length=20, blank=True, default='')
    town = models.CharField(max_length=100, blank=True, default='')

    alternative_contact_name = models.CharField(
        max_length=150,
        blank=True,
        default=''
    )

    alternative_contact_phone = models.CharField(
        max_length=30,
        blank=True,
        default=''
    )

    full_name = models.CharField(max_length=255, blank=True, default='')
    course = models.CharField(max_length=255, blank=True, default='')
    institution = models.CharField(max_length=255, blank=True, default='')

    skills = models.TextField(blank=True)
    bio = models.TextField(blank=True)

    phone_number = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=255, blank=True)

    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)

    profile_picture = models.ImageField(
        upload_to='student_profiles/',
        blank=True,
        null=True
    )

    cv = models.FileField(
        upload_to='student_cvs/',
        blank=True,
        null=True
    )

    extracted_skills = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        generated_name = f"{self.first_name} {self.other_names} {self.surname}".strip()

        if generated_name:
            self.full_name = generated_name

        super().save(*args, **kwargs)

    def get_profile_completion_items(self):
        return [
            ('Full name', self.full_name or (self.first_name and self.surname)),
            ('Course', self.course),
            ('Institution', self.institution),
            ('Skills', self.skills or self.extracted_skills),
            ('CV', self.cv),
            ('Preferred location', self.location),
            ('Phone number', self.phone_number or self.user.phone_number),
            ('Short bio', self.bio),
        ]

    def get_profile_completion(self):
        completion_items = self.get_profile_completion_items()
        completed_count = sum(bool(value) for label, value in completion_items)
        return int((completed_count / len(completion_items)) * 100)

    def get_missing_profile_items(self):
        return [label for label, value in self.get_profile_completion_items() if not value]

    def can_apply(self):
        return self.get_profile_completion() >= 70
    def __str__(self):
        return self.full_name or self.user.username


class AcademicQualification(models.Model):

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='academic_qualifications'
    )

    institution_name = models.CharField(max_length=255)
    qualification = models.CharField(max_length=255)
    course_name = models.CharField(max_length=255, blank=True, default='')
    grade = models.CharField(max_length=100, blank=True, default='')

    start_year = models.PositiveIntegerField(blank=True, null=True)
    end_year = models.PositiveIntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.qualification} - {self.institution_name}"


class WorkExperience(models.Model):

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='work_experiences'
    )

    organization = models.CharField(max_length=255)
    position = models.CharField(max_length=255)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    responsibilities = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.position} at {self.organization}"


class Referee(models.Model):

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='referees'
    )

    full_name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True, default='')
    position = models.CharField(max_length=255, blank=True, default='')
    phone_number = models.CharField(max_length=30, blank=True, default='')
    email = models.EmailField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
