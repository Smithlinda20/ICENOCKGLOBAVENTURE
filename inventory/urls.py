from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("admin/inventory/", views.stock_overview, name="overview"),
    path("admin/inventory/adjust/", views.stock_adjust, name="adjust"),
    path("admin/inventory/history/", views.stock_history, name="history"),
]
