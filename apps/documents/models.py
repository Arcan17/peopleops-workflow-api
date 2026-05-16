from django.db import models
from django.conf import settings


class DocumentType(models.TextChoices):
    CONTRACT = "contract", "Contract"
    ANNEX = "annex", "Annex"
    CERTIFICATE = "certificate", "Certificate"
    PAYSLIP = "payslip", "Payslip"
    PERSONAL = "personal", "Personal Document"


class Document(models.Model):
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="documents/%Y/%m/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return f"[{self.document_type}] {self.title} — {self.employee}"
