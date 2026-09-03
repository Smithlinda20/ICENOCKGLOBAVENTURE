from django.urls import path

from . import views

app_name = "audit"

urlpatterns = [
    path("admin/audit-log/", views.audit_log_list, name="list"),
]
