import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.test import Client
from django.urls import reverse

from accounts.models import User


def check_public(client, name):
    response = client.get(reverse(name))
    print(f"{name}: {response.status_code}")


def check_logged_in(role, related_lookup, name):
    user = User.objects.filter(role=role, **{related_lookup: False}).first()

    if user is None:
        print(f"{name}: skipped, no {role} with profile")
        return

    client = Client()
    client.force_login(user)
    response = client.get(reverse(name))
    print(f"{name}: {response.status_code}")


client = Client()

for public_name in [
    "home",
    "student_register",
    "employer_register",
    "login",
]:
    check_public(client, public_name)

check_logged_in("student", "studentprofile__isnull", "student_dashboard")
check_logged_in("employer", "employerprofile__isnull", "employer_profile")

admin_user = User.objects.filter(role="admin").first() or User.objects.filter(is_superuser=True).first()

if admin_user:
    admin_client = Client()
    admin_client.force_login(admin_user)
    response = admin_client.get(reverse("dashboard"))
    print(f"admin dashboard: {response.status_code}")
else:
    print("admin dashboard: skipped, no admin user")
