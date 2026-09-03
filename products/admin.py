from django.contrib import admin
from .models import PriceHistory, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "pack_price", "carton_price", "current_stock", "minimum_stock", "active")
    list_filter = ("active", "category")
    search_fields = ("name", "sku")


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("product", "field_changed", "old_price", "new_price", "changed_by", "changed_at")
    list_filter = ("field_changed",)
