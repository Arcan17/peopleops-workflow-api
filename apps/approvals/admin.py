from django.contrib import admin
from django.utils.html import format_html

from .models import Approval


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ["request_title", "approver_name", "decision_badge", "comment_short", "decided_at"]
    list_filter = ["decision", "decided_at"]
    search_fields = [
        "request__title", "approver__email",
        "approver__first_name", "approver__last_name", "comment",
    ]
    ordering = ["-decided_at"]
    readonly_fields = ["request", "approver", "decision", "decided_at"]
    list_per_page = 25
    date_hierarchy = "decided_at"

    fieldsets = (
        ("Decision", {"fields": ("request", "approver", "decision", "decided_at")}),
        ("Comment", {"fields": ("comment",)}),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Request", ordering="request__title")
    def request_title(self, obj):
        return obj.request.title

    @admin.display(description="Approver")
    def approver_name(self, obj):
        return obj.approver.full_name

    @admin.display(description="Decision")
    def decision_badge(self, obj):
        color = "#198754" if obj.decision == "approved" else "#dc3545"
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color,
            obj.decision.capitalize(),
        )

    @admin.display(description="Comment")
    def comment_short(self, obj):
        if not obj.comment:
            return "—"
        return obj.comment[:60] + ("…" if len(obj.comment) > 60 else "")
