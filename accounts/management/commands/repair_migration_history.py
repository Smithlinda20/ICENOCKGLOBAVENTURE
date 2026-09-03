"""
Safely repairs an inconsistent accounts/admin migration history.

This command changes only django_migrations records. It never deletes
application data and never resets the database.
"""
from django.core.management import BaseCommand, call_command
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = "Repair the accounts/admin migration history mismatch safely."

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        applied = recorder.applied_migrations()

        accounts_applied = ("accounts", "0001_initial") in applied
        admin_chain_inconsistent = (
            ("admin", "0001_initial") not in applied
            and any(app_label == "admin" for app_label, _ in applied)
        )

        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))

        if accounts_applied and admin_chain_inconsistent:
            if "django_admin_log" in tables:
                recorder.record_applied("admin", "0001_initial")
                self.stdout.write(
                    self.style.SUCCESS(
                        "Repaired migration history: recorded admin.0001_initial "
                        "because django_admin_log already exists."
                    )
                )
                return

            self.stdout.write(
                self.style.WARNING(
                    "admin migration records are inconsistent and django_admin_log "
                    "does not exist; rebuilding the admin migration chain."
                )
            )
            for app_label, migration_name in applied:
                if app_label == "admin":
                    recorder.record_unapplied(app_label, migration_name)
            call_command("migrate", "admin", interactive=False, verbosity=1)
            return

        if accounts_applied:
            self.stdout.write(
                self.style.SUCCESS("Migration history is already consistent; no repair needed.")
            )
            return

        if "accounts_user" in tables:
            recorder.record_applied("accounts", "0001_initial")
            if "django_admin_log" in tables and ("admin", "0001_initial") not in applied:
                recorder.record_applied("admin", "0001_initial")
            self.stdout.write(
                self.style.SUCCESS(
                    "Repaired migration history using the existing accounts/admin schemas."
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                "accounts.0001_initial is missing and accounts_user does not exist. "
                "Temporarily adjusting the applied admin migration chain so the "
                "accounts migration can be applied."
            )
        )

        applied_admin_migrations = sorted(
            migration_name
            for app_label, migration_name in applied
            if app_label == "admin"
        )
        for migration_name in applied_admin_migrations:
            recorder.record_unapplied("admin", migration_name)

        try:
            call_command("migrate", "accounts", "0001", interactive=False, verbosity=1)
        except Exception:
            for migration_name in applied_admin_migrations:
                if ("admin", migration_name) not in recorder.applied_migrations():
                    recorder.record_applied("admin", migration_name)
            raise
        else:
            if "django_admin_log" in tables and "0001_initial" not in applied_admin_migrations:
                applied_admin_migrations.insert(0, "0001_initial")

            if "django_admin_log" not in tables:
                call_command("migrate", "admin", interactive=False, verbosity=1)
            else:
                for migration_name in applied_admin_migrations:
                    if ("admin", migration_name) not in recorder.applied_migrations():
                        recorder.record_applied("admin", migration_name)

            self.stdout.write(
                self.style.SUCCESS(
                    "Repaired migration history and applied accounts/admin migrations."
                )
            )
