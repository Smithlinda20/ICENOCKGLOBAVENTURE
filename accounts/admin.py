from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "get_full_name", "role", "phone", "is_active", "active_staff")
    list_filter = ("role", "is_active", "active_staff")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Store Role", {"fields": ("role", "phone", "active_staff")}),
    )
