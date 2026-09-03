from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("pos/", views.pos, name="pos"),
    path("pos/complete/", views.complete_sale_view, name="complete_sale"),
    path("receipt/<int:pk>/", views.receipt_detail, name="receipt"),
    path("receipt/<int:pk>/reprint/", views.receipt_reprint, name="receipt_reprint"),
    path("receipt/<int:pk>/pdf/", views.receipt_pdf, name="receipt_pdf"),
    path("my-sales/", views.my_sales, name="my_sales"),
    path("admin/sales/", views.all_sales, name="all_sales"),
    path("admin/sales/<int:pk>/cancel/", views.sale_cancel, name="sale_cancel"),
]
