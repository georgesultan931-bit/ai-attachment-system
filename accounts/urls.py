from django.urls import path
from django.contrib.auth import views as auth_views

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

    # FIXED: Added login URL with custom view for mobile compatibility
    path(
        'login/',
        views.user_login,
        name='login'
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
        'register/',
        views.account_start,
        name='account_start'
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
        'admin-verify-user/<int:user_id>/',
        views.admin_verify_user,
        name='admin_verify_user'
    ),

    path(
        'admin-reset-user-password/<int:user_id>/',
        views.admin_reset_user_password,
        name='admin_reset_user_password'
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

    path(
        'delete-old-pending-accounts/',
        views.delete_old_pending_accounts,
        name='delete_old_pending_accounts'
    ),
    
path('create-student-profile/', views.create_student_profile, name='create_student_profile'),
path('create-employer-profile/', views.create_employer_profile, name='create_employer_profile'),
]
