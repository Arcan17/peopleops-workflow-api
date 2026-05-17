from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Document

# ── File type constraints ─────────────────────────────────────────────────────

ALLOWED_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
    }
)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

# Magic byte signatures per MIME type.
# A client-supplied content_type can be spoofed; reading the actual file
# header provides a second layer of validation against the real format.
# Tuple of accepted byte prefixes (at least one must match).
MAGIC_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    "application/pdf": (b"%PDF",),
    # DOCX / XLSX / PPTX are ZIP-based (Open XML), so the header is the ZIP magic.
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
        b"PK\x03\x04",
    ),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
}


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    type_display = serializers.CharField(source="get_document_type_display", read_only=True)

    class Meta:
        model = Document
        fields = ["id", "employee", "document_type", "type_display", "title", "file", "uploaded_by", "created_at"]
        read_only_fields = ["id", "uploaded_by", "created_at"]

    def validate_file(self, file):
        # 1. MIME type whitelist (client-declared)
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(
                f"Unsupported file type '{file.content_type}'. "
                "Accepted types: PDF, DOCX, JPEG, PNG."
            )

        # 2. File size limit
        if file.size > MAX_FILE_SIZE_BYTES:
            mb = file.size / (1024 * 1024)
            raise serializers.ValidationError(
                f"File size {mb:.1f} MB exceeds the 10 MB limit."
            )

        # 3. Magic bytes — verify the real file header matches the declared type.
        #    This catches attackers who lie about content_type.
        expected_signatures = MAGIC_SIGNATURES.get(file.content_type)
        if expected_signatures:
            header = file.read(8)
            file.seek(0)  # reset so Django can still write the file
            if not any(header.startswith(sig) for sig in expected_signatures):
                raise serializers.ValidationError(
                    "File content does not match the declared type. "
                    "Ensure you are uploading a real PDF, DOCX, JPEG or PNG file."
                )

        return file

    def create(self, validated_data):
        validated_data["uploaded_by"] = self.context["request"].user
        return super().create(validated_data)
