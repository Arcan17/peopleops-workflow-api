from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["user", "position", "department", "contract_type", "status", "hire_date"]
    list_filter = ["status", "contract_type", "department"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "position"]
    ordering = ["user__first_name"]
