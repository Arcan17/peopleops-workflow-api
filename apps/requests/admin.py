from django.contrib import admin
from django.utils.html import format_html

from apps.approvals.models import Approval
from apps.notifications.models import Notification, NotificationType

from .models import InternalRequest, RequestStatus


def approve_requests(modeladmin, request, queryset):
    eligible = queryset.filter(status__in=[RequestStatus.PENDING, RequestStatus.IN_REVIEW])
    for req in eligible:
        req.status = RequestStatus.APPROVED
        req.save()
        Approval.objects.create(
            request=req,
            approver=request.user,
            decision="approved",
            comment="Bulk approved via admin panel",
        )
        Notification.objects.create(
            recipient=req.employee,
            message=f'Your request "{req.title}" has been approved.',
            notification_type=NotificationType.REQUEST_APPROVED,
            related_request=req,
        )


approve_requests.short_description = "✓ Approve selected requests"


def reject_requests(modeladmin, request, queryset):
    eligible = queryset.filter(status__in=[RequestStatus.PENDING, RequestStatus.IN_REVIEW])
    for req in eligible:
        req.status = RequestStatus.REJECTED
        req.save()
        Approval.objects.create(
            request=req,
            approver=request.user,
            decision="rejected",
            comment="Bulk rejected via admin panel",
        )
        Notification.objects.create(
            recipient=req.employee,
            message=f'Your request "{req.title}" has been rejected.',
            notification_type=NotificationType.REQUEST_REJECTED,
            related_request=req,
        )


reject_requests.short_description = "✗ Reject selected requests"


def mark_in_review(modeladmin, request, queryset):
    queryset.filter(status=RequestStatus.PENDING).update(status=RequestStatus.IN_REVIEW)


mark_in_review.short_description = "→ Mark selected requests as In Review"


@admin.register(InternalRequest)
class InternalRequestAdmin(admin.ModelAdmin):
    list_display = [
        "title", "employee_name", "request_type", "status_badge", "created_at", "start_date",
    ]
    list_filter = ["status", "request_type", "created_at"]
    search_fields = ["title", "description", "employee__email", "employee__first_name", "employee__last_name"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]
    actions = [approve_requests, reject_requests, mark_in_review]
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        ("Request", {"fields": ("employee", "request_type", "status", "title", "description")}),
        ("Dates & Amount", {"fields": ("start_date", "end_date", "amount")}),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Employee", ordering="employee__first_name")
    def employee_name(self, obj):
        return obj.employee.full_name

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            RequestStatus.PENDING: "#fd7e14",
            RequestStatus.IN_REVIEW: "#0dcaf0",
            RequestStatus.APPROVED: "#198754",
            RequestStatus.REJECTED: "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color,
            obj.get_status_display(),
        )
