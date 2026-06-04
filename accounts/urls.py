from django.urls import path

from . import views


urlpatterns = [

    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'home/',
        views.home,
        name='home'
    ),

    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),

    path(
        'register/student/',
        views.student_register,
        name='student_register'
    ),

    path(
        'register/employer/',
        views.employer_register,
        name='employer_register'
    ),

    path(
        'verify-otp/<int:user_id>/',
        views.verify_otp,
        name='verify_otp'
    ),

    path(
        'pending-approval/',
        views.pending_approval,
        name='pending_approval'
    ),

    path(
        'send-verification-code/<int:user_id>/',
        views.send_user_verification_code,
        name='send_user_verification_code'
    ),

    path(
        'send-verification-code/<int:user_id>/<str:channel>/',
        views.send_user_verification_code,
        name='send_user_verification_code_channel'
    ),

    path(
        'approve-user/<int:user_id>/',
        views.approve_user,
        name='approve_user'
    ),

    path(
        'reject-user/<int:user_id>/',
        views.reject_user,
        name='reject_user'
    ),

    path(
        'logout/',
        views.logout_user,
        name='logout'
    ),

    path(
    'delete-user/<int:user_id>/',
    views.delete_user_account,
    name='delete_user_account'
),

]
