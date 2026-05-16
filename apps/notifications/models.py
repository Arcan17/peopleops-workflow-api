from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    REQUEST_APPROVED = "request_approved", "Request Approved"
    REQUEST_REJECTED = "request_rejected", "Request Rejected"
    REQUEST_PENDING = "request_pending", "Request Pending Reminder"
    GENERAL = "general", "General"


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30, choices=NotificationType.choices, default=NotificationType.GENERAL
    )
    related_request = models.ForeignKey(
        "requests.InternalRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"[{self.notification_type}] → {self.recipient.email}"
