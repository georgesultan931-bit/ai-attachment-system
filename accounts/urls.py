from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs
    path('', views.home, name='home'),
    path('account-start/', views.account_start, name='account_start'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('student/register/', views.student_register, name='student_register'),
    path('employer/register/', views.employer_register, name='employer_register'),
    path('verify-registration/<token>/', views.verify_registration_email, name='verify_registration_email'),
    path('verify/<token>/', views.verify_registration_email, name='verify_registration_email_legacy'),
    path('pending-approval/', views.pending_approval, name='pending_approval'),
    path('create-student-profile/', views.create_student_profile, name='create_student_profile'),
    path('create-employer-profile/', views.create_employer_profile, name='create_employer_profile'),
    path('approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('reject/<int:user_id>/', views.reject_user, name='reject_user'),
    path('delete/<int:user_id>/', views.delete_user_account, name='delete_user_account'),
    path('verify-user/<int:user_id>/', views.admin_verify_user, name='admin_verify_user'),
    path('reset-password-admin/<int:user_id>/', views.admin_reset_user_password, name='admin_reset_user_password'),
    path('delete-pending/', views.delete_old_pending_accounts, name='delete_old_pending_accounts'),
    
    # Password Reset URLs (ADD THESE)
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('reset-password/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset-password/complete/', views.password_reset_complete, name='password_reset_complete'),
]
