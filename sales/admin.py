from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "salesperson", "total", "payment_method", "status", "created_at")
    list_filter = ("status", "payment_method")
    search_fields = ("receipt_number", "customer_name", "customer_phone")
    inlines = [SaleItemInline]
