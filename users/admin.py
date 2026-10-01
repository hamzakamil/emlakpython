from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "tenant", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Tenant & Rol", {"fields": ("tenant", "role")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Tenant & Rol", {"fields": ("tenant", "role")}),
    )