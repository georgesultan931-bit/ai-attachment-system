from django.contrib import admin

from .models import (
    StudentProfile,
    AcademicQualification,
    WorkExperience,
    Referee
)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):

    list_display = (
        'full_name',
        'institution',
        'course',
        'phone_number'
    )

    search_fields = (
        'full_name',
        'institution',
        'course'
    )


@admin.register(AcademicQualification)
class AcademicQualificationAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'qualification',
        'institution_name',
        'end_year'
    )

    search_fields = (
        'qualification',
        'institution_name'
    )


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'organization',
        'position'
    )

    search_fields = (
        'organization',
        'position'
    )


@admin.register(Referee)
class RefereeAdmin(admin.ModelAdmin):

    list_display = (
        'full_name',
        'organization',
        'phone_number'
    )

    search_fields = (
        'full_name',
        'organization'
    )