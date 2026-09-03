from django.contrib import admin
from .models import DiscountRule


@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "unit_type", "min_qty", "max_qty", "percentage", "fixed_amount", "active")
    list_filter = ("unit_type", "active")
