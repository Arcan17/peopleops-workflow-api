from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "employee", "document_type", "uploaded_by", "created_at"]
    list_filter = ["document_type"]
    ordering = ["-created_at"]
