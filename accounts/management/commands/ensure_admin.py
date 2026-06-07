import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


TRUE_VALUES = {"1", "true", "yes", "on"}


class Command(BaseCommand):
    help = (
        "Create or update the initial admin account from environment "
        "variables without changing an existing password by default."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default=os.environ.get("DJANGO_ADMIN_USERNAME", "admin"),
            help="Admin username. Defaults to DJANGO_ADMIN_USERNAME or admin.",
        )
        parser.add_argument(
            "--email",
            default=os.environ.get("DJANGO_ADMIN_EMAIL", "admin@example.com"),
            help="Admin email. Defaults to DJANGO_ADMIN_EMAIL or admin@example.com.",
        )
        parser.add_argument(
            "--password",
            default=os.environ.get("DJANGO_ADMIN_PASSWORD"),
            help="Admin password. Defaults to DJANGO_ADMIN_PASSWORD.",
        )
        parser.add_argument(
            "--force-password-reset",
            action="store_true",
            default=os.environ.get("DJANGO_ADMIN_FORCE_PASSWORD_RESET", "").lower()
            in TRUE_VALUES,
            help="Reset the admin password when the account already exists.",
        )

    def handle(self, *args, **options):
        username = (options["username"] or "").strip()
        email = (options["email"] or "").strip().lower()
        password = options["password"]
        force_password_reset = options["force_password_reset"]

        if not username:
            raise CommandError("Admin username is required.")

        if not email:
            raise CommandError("Admin email is required.")

        User = get_user_model()
        user = User.objects.filter(username__iexact=username).first()

        if user is None:
            user = User.objects.filter(email__iexact=email).first()

        created = user is None
        password_updated = False

        if created:
            if not password:
                self.stdout.write(
                    self.style.WARNING(
                        "No admin account exists and DJANGO_ADMIN_PASSWORD is not set. "
                        "Skipping admin creation."
                    )
                )
                return

            user = User(username=username, email=email)
            user.set_password(password)
            password_updated = True

        else:
            username_conflict = (
                User.objects.filter(username__iexact=username)
                .exclude(pk=user.pk)
                .exists()
            )
            email_conflict = (
                User.objects.filter(email__iexact=email)
                .exclude(pk=user.pk)
                .exists()
            )

            if username_conflict:
                raise CommandError(f"Another user already has username {username}.")

            if email_conflict:
                raise CommandError(f"Another user already has email {email}.")

            if password and force_password_reset:
                user.set_password(password)
                password_updated = True

            if password and not force_password_reset:
                self.stdout.write(
                    "Admin exists. Password was not changed because "
                    "DJANGO_ADMIN_FORCE_PASSWORD_RESET is not true."
                )

        user.username = username
        user.email = email
        user.role = "admin"
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.is_email_verified = True
        user.is_approved = True
        user.save()

        action = "Created" if created else "Updated"
        password_message = "password set" if password_updated else "password unchanged"

        self.stdout.write(
            self.style.SUCCESS(
                f"{action} admin account {user.username} ({password_message})."
            )
        )
