"""
Idempotent superuser bootstrap.

Reads ADMIN_USERNAME / ADMIN_EMAIL / ADMIN_PASSWORD from environment
variables (see .env-sample) and creates the owner/admin account if it
does not already exist. Safe to run on every deploy - it will never
create duplicates and never overwrite an existing password.
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create the initial owner/admin account from environment variables (idempotent)."

    def handle(self, *args, **options):
        username = settings.ADMIN_USERNAME
        email = settings.ADMIN_EMAIL
        password = settings.ADMIN_PASSWORD

        if not (username and email and password):
            self.stdout.write(self.style.WARNING(
                "ADMIN_USERNAME / ADMIN_EMAIL / ADMIN_PASSWORD not fully set - skipping admin bootstrap."
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f"Admin user '{username}' already exists - skipping."))
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=User.Role.ADMIN,
        )
        self.stdout.write(self.style.SUCCESS(f"Created owner/admin account '{username}'."))
        self.stdout.write(self.style.WARNING(
            "IMPORTANT: change this password immediately after first login in production."
        ))
