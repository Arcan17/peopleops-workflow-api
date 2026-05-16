from django.db import models
from django.conf import settings


class ApprovalDecision(models.TextChoices):
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class Approval(models.Model):
    request = models.ForeignKey(
        "requests.InternalRequest",
        on_delete=models.CASCADE,
        related_name="approvals",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="approvals_made",
    )
    decision = models.CharField(max_length=10, choices=ApprovalDecision.choices)
    comment = models.TextField(blank=True, default="")
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-decided_at"]
        verbose_name = "Approval"
        verbose_name_plural = "Approvals"

    def __str__(self):
        return f"{self.decision} by {self.approver} on {self.request}"
