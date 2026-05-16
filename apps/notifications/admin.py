from django.contrib import admin
from django.utils.html import format_html

from .models import Notification, NotificationType


def mark_as_read(modeladmin, request, queryset):
    queryset.update(is_read=True)


mark_as_read.short_description = "Mark selected notifications as read"


def mark_as_unread(modeladmin, request, queryset):
    queryset.update(is_read=False)


mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "recipient_name", "notification_type_badge", "message_short",
        "related_request_link", "is_read", "created_at",
    ]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = [
        "recipient__email", "recipient__first_name", "recipient__last_name", "message",
    ]
    ordering = ["-created_at"]
    readonly_fields = ["recipient", "message", "notification_type", "related_request", "created_at"]
    actions = [mark_as_read, mark_as_unread]
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        ("Notification", {"fields": ("recipient", "notification_type", "message", "is_read")}),
        ("Related", {
            "fields": ("related_request", "created_at"),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="Recipient")
    def recipient_name(self, obj):
        return obj.recipient.full_name

    @admin.display(description="Message")
    def message_short(self, obj):
        return obj.message[:70] + ("…" if len(obj.message) > 70 else "")

    @admin.display(description="Type")
    def notification_type_badge(self, obj):
        colors = {
            NotificationType.REQUEST_APPROVED: "#198754",
            NotificationType.REQUEST_REJECTED: "#dc3545",
            NotificationType.REQUEST_PENDING: "#fd7e14",
            NotificationType.GENERAL: "#6c757d",
        }
        color = colors.get(obj.notification_type, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color,
            obj.get_notification_type_display(),
        )

    @admin.display(description="Request")
    def related_request_link(self, obj):
        if obj.related_request:
            return format_html(
                '<a href="/admin/requests/internalrequest/{}/change/">{}</a>',
                obj.related_request.pk,
                obj.related_request.title[:30],
            )
        return "—"
