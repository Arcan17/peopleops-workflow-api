from django.contrib import admin
from django.utils.html import format_html

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "title", "employee_name", "document_type_badge", "uploaded_by_name",
        "file_link", "created_at",
    ]
    list_filter = ["document_type", "created_at"]
    search_fields = [
        "title",
        "employee__user__email", "employee__user__first_name", "employee__user__last_name",
        "uploaded_by__email",
    ]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "uploaded_by"]
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        ("Document", {"fields": ("employee", "document_type", "title", "file")}),
        ("Metadata", {
            "fields": ("uploaded_by", "created_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Employee")
    def employee_name(self, obj):
        return obj.employee.user.full_name

    @admin.display(description="Uploaded By")
    def uploaded_by_name(self, obj):
        return obj.uploaded_by.full_name if obj.uploaded_by else "—"

    @admin.display(description="Type")
    def document_type_badge(self, obj):
        colors = {
            "contract": "#0d6efd",
            "annex": "#6610f2",
            "certificate": "#198754",
            "payslip": "#fd7e14",
            "personal": "#6c757d",
        }
        color = colors.get(obj.document_type, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color,
            obj.get_document_type_display(),
        )

    @admin.display(description="File")
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file.url)
        return "—"
