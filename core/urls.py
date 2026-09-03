from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("admin/dashboard/", views.dashboard, name="dashboard"),
    path("admin/settings/", views.settings_view, name="settings"),
]
