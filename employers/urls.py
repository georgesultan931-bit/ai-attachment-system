from django.urls import path
from . import views

urlpatterns = [

    path(
        'create-employer-profile/',
        views.create_employer_profile,
        name='create_employer_profile'
    ),
path(
    'employer-profile/',
    views.employer_profile,
    name='employer_profile'
),
path(
    'edit-employer-profile/',
    views.edit_employer_profile,
    name='edit_employer_profile'
),

path(
    'company/<int:employer_id>/',
    views.company_detail,
    name='company_detail'
),
]