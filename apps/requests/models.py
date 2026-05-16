from django.db import models
from django.conf import settings


class RequestType(models.TextChoices):
    VACATION = "vacation", "Vacation"
    PERMISSION = "permission", "Permission"
    REIMBURSEMENT = "reimbursement", "Reimbursement"
    DOCUMENT = "document", "Document Request"
    PERSONAL_DATA = "personal_data", "Personal Data Change"


class RequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_REVIEW = "in_review", "In Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class InternalRequest(models.Model):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requests",
    )
    request_type = models.CharField(max_length=20, choices=RequestType.choices)
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Internal Request"
        verbose_name_plural = "Internal Requests"

    def __str__(self):
        return f"[{self.request_type}] {self.title} — {self.employee.full_name}"

    @property
    def is_editable(self):
        return self.status == RequestStatus.PENDING
