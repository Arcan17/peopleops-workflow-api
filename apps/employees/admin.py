from django.contrib import admin
from django.utils.html import format_html

from .models import Employee, EmployeeStatus


def mark_active(modeladmin, request, queryset):
    queryset.update(status=EmployeeStatus.ACTIVE)


mark_active.short_description = "Mark selected employees as Active"


def mark_on_leave(modeladmin, request, queryset):
    queryset.update(status=EmployeeStatus.ON_LEAVE)


mark_on_leave.short_description = "Mark selected employees as On Leave"


def mark_inactive(modeladmin, request, queryset):
    queryset.update(status=EmployeeStatus.INACTIVE)


mark_inactive.short_description = "Mark selected employees as Inactive"


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        "full_name", "position", "department", "contract_type",
        "status_badge", "hire_date", "manager_name",
    ]
    list_filter = ["status", "contract_type", "department"]
    search_fields = [
        "user__email", "user__first_name", "user__last_name",
        "position", "department",
    ]
    ordering = ["user__first_name", "user__last_name"]
    readonly_fields = ["created_at", "updated_at"]
    actions = [mark_active, mark_on_leave, mark_inactive]
    list_per_page = 25
    date_hierarchy = "hire_date"

    fieldsets = (
        ("User Account", {"fields": ("user", "manager")}),
        ("Position", {"fields": ("position", "department", "contract_type", "status")}),
        ("Contract Details", {"fields": ("hire_date", "base_salary")}),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Employee", ordering="user__first_name")
    def full_name(self, obj):
        return obj.user.full_name

    @admin.display(description="Manager")
    def manager_name(self, obj):
        return obj.manager.full_name if obj.manager else "—"

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            EmployeeStatus.ACTIVE: "#198754",
            EmployeeStatus.INACTIVE: "#dc3545",
            EmployeeStatus.ON_LEAVE: "#fd7e14",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color,
            obj.get_status_display(),
        )
