from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import CustomUser, Role


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = [
        "email", "full_name_display", "role_badge", "is_active", "is_staff", "date_joined",
    ]
    list_filter = ["role", "is_active", "is_staff", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["email"]
    readonly_fields = ["date_joined", "last_login"]
    list_per_page = 25

    fieldsets = (
        ("Credentials", {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "role")}),
        ("Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("date_joined", "last_login"),
            "classes": ("collapse",),
        }),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "role", "password1", "password2"),
        }),
    )

    @admin.display(description="Name")
    def full_name_display(self, obj):
        return obj.full_name

    @admin.display(description="Role")
    def role_badge(self, obj):
        colors = {
            Role.ADMIN: "#dc3545",
            Role.MANAGER: "#0d6efd",
            Role.EMPLOYEE: "#198754",
        }
        color = colors.get(obj.role, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color,
            obj.get_role_display(),
        )
