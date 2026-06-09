# accounts/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Home and Authentication
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Registration
    path('register/', views.account_start, name='account_start'),
    path('register/student/', views.student_register, name='student_register'),
    path('register/employer/', views.employer_register, name='employer_register'),

    # Verification
    path('verify-otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('verify-registration/<str:token>/', views.verify_registration_email, name='verify_registration_email'),
    path('verify-email/<str:token>/', views.verify_registration_email, name='verify_registration_email_alt'),

    # Pending Approval
    path('pending-approval/', views.pending_approval, name='pending_approval'),

    # Profile Creation
    path('create-student-profile/', views.create_student_profile, name='create_student_profile'),
    path('create-employer-profile/', views.create_employer_profile, name='create_employer_profile'),

    # Admin User Management
    path('approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('reject-user/<int:user_id>/', views.reject_user, name='reject_user'),
    path('delete-user/<int:user_id>/', views.delete_user_account, name='delete_user_account'),

    # Admin Verification & Password
    path('send-verification-code/<int:user_id>/', views.send_user_verification_code, name='send_user_verification_code'),
    path('send-verification-code/<int:user_id>/<str:channel>/', views.send_user_verification_code, name='send_user_verification_code_channel'),
    path('admin-verify-user/<int:user_id>/', views.admin_verify_user, name='admin_verify_user'),
    path('admin-reset-password/<int:user_id>/', views.admin_reset_user_password, name='admin_reset_user_password'),

    # Admin Bulk Actions
    path('delete-old-pending/', views.delete_old_pending_accounts, name='delete_old_pending_accounts'),
]
