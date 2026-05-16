from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Document

ALLOWED_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
    }
)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    type_display = serializers.CharField(source="get_document_type_display", read_only=True)

    class Meta:
        model = Document
        fields = ["id", "employee", "document_type", "type_display", "title", "file", "uploaded_by", "created_at"]
        read_only_fields = ["id", "uploaded_by", "created_at"]

    def validate_file(self, file):
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(
                f"Unsupported file type '{file.content_type}'. "
                "Accepted types: PDF, DOCX, JPEG, PNG."
            )
        if file.size > MAX_FILE_SIZE_BYTES:
            mb = file.size / (1024 * 1024)
            raise serializers.ValidationError(
                f"File size {mb:.1f} MB exceeds the 10 MB limit."
            )
        return file

    def create(self, validated_data):
        validated_data["uploaded_by"] = self.context["request"].user
        return super().create(validated_data)
