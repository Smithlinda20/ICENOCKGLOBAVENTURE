from django.urls import path

from . import views

app_name = "discounts"

urlpatterns = [
    path("admin/discounts/", views.rule_list, name="list"),
    path("admin/discounts/new/", views.rule_edit, name="new"),
    path("admin/discounts/<int:pk>/edit/", views.rule_edit, name="edit"),
    path("admin/discounts/<int:pk>/toggle/", views.rule_toggle, name="toggle"),
    path("admin/discounts/strategy/", views.strategy_settings, name="strategy"),
]
