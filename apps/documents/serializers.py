from rest_framework import serializers
from .models import Document
from apps.accounts.serializers import UserSerializer


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    type_display = serializers.CharField(source="get_document_type_display", read_only=True)

    class Meta:
        model = Document
        fields = ["id", "employee", "document_type", "type_display", "title", "file", "uploaded_by", "created_at"]
        read_only_fields = ["id", "uploaded_by", "created_at"]

    def create(self, validated_data):
        validated_data["uploaded_by"] = self.context["request"].user
        return super().create(validated_data)
