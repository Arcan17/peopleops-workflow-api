from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import InternalRequest


class InternalRequestSerializer(serializers.ModelSerializer):
    employee = UserSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    type_display = serializers.CharField(source="get_request_type_display", read_only=True)
    is_editable = serializers.BooleanField(read_only=True)

    class Meta:
        model = InternalRequest
        fields = [
            "id", "employee", "request_type", "type_display",
            "status", "status_display", "title", "description",
            "start_date", "end_date", "amount",
            "is_editable", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "employee", "status", "created_at", "updated_at"]


class InternalRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternalRequest
        fields = ["request_type", "title", "description", "start_date", "end_date", "amount"]

    def create(self, validated_data):
        validated_data["employee"] = self.context["request"].user
        return super().create(validated_data)


class InternalRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternalRequest
        fields = ["title", "description", "start_date", "end_date", "amount"]

    def validate(self, attrs):
        if not self.instance.is_editable:
            raise serializers.ValidationError("Only pending requests can be edited.")
        return attrs


class ApproveRejectSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True, default="")
