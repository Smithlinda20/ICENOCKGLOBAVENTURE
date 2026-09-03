from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

from .models import AuditLog


def _is_admin(user):
    return user.is_authenticated and user.is_admin_role


@user_passes_test(_is_admin)
def audit_log_list(request):
    logs = AuditLog.objects.select_related("user").all()[:500]
    return render(request, "admin_dash/audit_log.html", {"logs": logs})
