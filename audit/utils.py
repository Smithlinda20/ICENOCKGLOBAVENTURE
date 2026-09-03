from .models import AuditLog


def log_action(user, action, description):
    AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        description=description[:500],
    )
