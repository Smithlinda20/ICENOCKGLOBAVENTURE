from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("admin/reports/monthly/", views.monthly_analysis, name="monthly"),
    path("admin/reports/performance/", views.salesperson_performance, name="performance"),
    path("admin/reports/inventory/", views.inventory_report, name="inventory"),
    path("admin/reports/export/sales.csv", views.export_sales_csv, name="export_sales_csv"),
    path("admin/reports/export/inventory.csv", views.export_inventory_csv, name="export_inventory_csv"),
]
