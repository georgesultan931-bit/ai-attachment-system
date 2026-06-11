# accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("start/", views.account_start, name="account_start"),

    path("login/", views.user_login, name="login"),
    path("logout/", views.logout_user, name="logout"),

    path("student/register/", views.student_register, name="student_register"),
    path("employer/register/", views.employer_register, name="employer_register"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path(
        "student/profile/create/",
        views.create_student_profile,
        name="create_student_profile",
    ),

    path(
        "employer/profile/create/",
        views.create_employer_profile,
        name="create_employer_profile",
    ),

    path(
        "verify-email/<str:token>/",
        views.verify_registration_email,
        name="verify_registration_email",
    ),

    path(
        "pending-approval/",
        views.pending_approval,
        name="pending_approval",
    ),

    path(
        "approve-user/<int:user_id>/",
        views.approve_user,
        name="approve_user",
    ),

    path(
        "reject-user/<int:user_id>/",
        views.reject_user,
        name="reject_user",
    ),

    path(
        "delete-user/<int:user_id>/",
        views.delete_user_account,
        name="delete_user_account",
    ),

    path(
        "admin-verify-user/<int:user_id>/",
        views.admin_verify_user,
        name="admin_verify_user",
    ),

    path(
        "admin-reset-password/<int:user_id>/",
        views.admin_reset_user_password,
        name="admin_reset_user_password",
    ),

    path(
        "delete-old-pending-accounts/",
        views.delete_old_pending_accounts,
        name="delete_old_pending_accounts",
    ),

    # Password reset
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="/password-reset/done/",
        ),
        name="password_reset",
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),

    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/reset/done/",
        ),
        name="password_reset_confirm",
    ),

    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]