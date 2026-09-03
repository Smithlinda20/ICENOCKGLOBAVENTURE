"""
Safely repairs the specific migration-history mismatch caused when
accounts.0001_initial is missing from django_migrations while
admin.0001_initial is already recorded as applied.

This command is intentionally narrow and idempotent. It never deletes
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

        admin_applied = ("admin", "0001_initial") in applied
        accounts_applied = ("accounts", "0001_initial") in applied

        if not (admin_applied and not accounts_applied):
            self.stdout.write(
                self.style.SUCCESS("Migration history is already consistent; no repair needed.")
            )
            return

        # If the custom User table already exists, the schema is already
        # present and only the migration record is missing.
        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))

        if "accounts_user" in tables:
            recorder.record_applied("accounts", "0001_initial")
            self.stdout.write(
                self.style.SUCCESS(
                    "Repaired migration history: recorded accounts.0001_initial "
                    "because accounts_user already exists."
                )
            )
            return

        # The accounts table does not exist. Temporarily remove only the
        # admin migration record so Django can apply accounts.0001_initial,
        # then restore the admin migration record without re-running its
        # schema-creating operations.
        self.stdout.write(
            self.style.WARNING(
                "accounts.0001_initial is missing and accounts_user does not exist. "
                "Temporarily adjusting only the migration record so the accounts "
                "migration can be applied."
            )
        )

        recorder.record_unapplied("admin", "0001_initial")
        try:
            call_command("migrate", "accounts", "0001", interactive=False, verbosity=1)
        except Exception:
            # Restore the original migration-history entry if the migration
            # itself fails. Do not silently hide the real migration error.
            if ("admin", "0001_initial") not in recorder.applied_migrations():
                recorder.record_applied("admin", "0001_initial")
            raise
        else:
            if ("admin", "0001_initial") not in recorder.applied_migrations():
                recorder.record_applied("admin", "0001_initial")

            self.stdout.write(
                self.style.SUCCESS(
                    "Repaired migration history and applied accounts.0001_initial."
                )
            )
