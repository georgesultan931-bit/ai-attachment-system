from django.urls import path

from . import views


urlpatterns = [

    path(
        'create-profile/',
        views.create_student_profile,
        name='create_student_profile'
    ),

    path(
        'student-profile/',
        views.student_profile,
        name='student_profile'
    ),

    path(
        'edit-student-profile/',
        views.edit_student_profile,
        name='edit_student_profile'
    ),

    path(
        'add-academic-qualification/',
        views.add_academic_qualification,
        name='add_academic_qualification'
    ),

    path(
        'edit-academic-qualification/<int:qualification_id>/',
        views.edit_qualification,
        name='edit_qualification'
    ),

    path(
        'delete-academic-qualification/<int:qualification_id>/',
        views.delete_qualification,
        name='delete_qualification'
    ),

    path(
        'add-work-experience/',
        views.add_work_experience,
        name='add_work_experience'
    ),

    path(
        'edit-work-experience/<int:work_id>/',
        views.edit_work,
        name='edit_work'
    ),

    path(
        'delete-work-experience/<int:work_id>/',
        views.delete_work,
        name='delete_work'
    ),

    path(
        'add-referee/',
        views.add_referee,
        name='add_referee'
    ),

    path(
        'edit-referee/<int:referee_id>/',
        views.edit_referee,
        name='edit_referee'
    ),

    path(
        'delete-referee/<int:referee_id>/',
        views.delete_referee,
        name='delete_referee'
    ),

    path(
        'generate-resume/',
        views.generate_resume_pdf,
        name='generate_resume_pdf'
    ),

    path(
    'student-dashboard/',
    views.student_dashboard,
    name='student_dashboard'
),
]
