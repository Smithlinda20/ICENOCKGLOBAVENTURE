from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("admin/products/", views.product_list, name="list"),
    path("admin/products/new/", views.product_edit, name="new"),
    path("admin/products/<int:pk>/edit/", views.product_edit, name="edit"),
    path("admin/products/<int:pk>/toggle/", views.product_toggle_active, name="toggle"),
    path("admin/products/<int:pk>/price-history/", views.product_price_history, name="price_history"),
    path("api/products/search/", views.product_search_api, name="search_api"),
]
