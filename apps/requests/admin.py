from django.contrib import admin
from .models import InternalRequest


@admin.register(InternalRequest)
class InternalRequestAdmin(admin.ModelAdmin):
    list_display = ["title", "employee", "request_type", "status", "created_at"]
    list_filter = ["status", "request_type"]
    search_fields = ["title", "employee__email"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]
