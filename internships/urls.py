from django.urls import path

from . import views


urlpatterns = [

    path(
        'opportunities/',
        views.opportunity_list,
        name='opportunity_list'
    ),

    path(
        'opportunity/<int:opportunity_id>/',
        views.opportunity_detail,
        name='opportunity_detail'
    ),

    path(
        'apply/<int:opportunity_id>/',
        views.apply_opportunity,
        name='apply_opportunity'
    ),

    path(
        'my-applications/',
        views.my_applications,
        name='my_applications'
    ),

    path(
        'my-interviews/',
        views.my_interviews,
        name='my_interviews'
    ),

    path(
        'interview/<int:application_id>/accept/',
        views.accept_interview,
        name='accept_interview'
    ),

    path(
        'interview/<int:application_id>/decline/',
        views.decline_interview,
        name='decline_interview'
    ),

    path(
        'employer-applications/',
        views.employer_applications,
        name='employer_applications'
    ),

    path(
        'employer-applications/pdf/',
        views.employer_applications_pdf,
        name='employer_applications_pdf'
    ),

    path(
        'application/<int:application_id>/',
        views.application_detail,
        name='application_detail'
    ),

    path(
        'application/<int:application_id>/schedule-interview/',
        views.schedule_interview,
        name='schedule_interview'
    ),

    path(
        'update-application-status/<int:application_id>/<str:status>/',
        views.update_application_status,
        name='update_application_status'
    ),

    path(
        'create-opportunity/',
        views.create_opportunity,
        name='create_opportunity'
    ),

    path(
        'my-opportunities/',
        views.my_opportunities,
        name='my_opportunities'
    ),

    path(
        'edit-opportunity/<int:opportunity_id>/',
        views.edit_opportunity,
        name='edit_opportunity'
    ),

    path(
        'delete-opportunity/<int:opportunity_id>/',
        views.delete_opportunity,
        name='delete_opportunity'
    ),

    path(
        'toggle-opportunity-status/<int:opportunity_id>/',
        views.toggle_opportunity_status,
        name='toggle_opportunity_status'
    ),
]