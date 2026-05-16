from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import InternalRequest, RequestType


def validate_request_payload(attrs, instance=None):
    request_type = attrs.get("request_type", getattr(instance, "request_type", None))
    start_date = attrs.get("start_date", getattr(instance, "start_date", None))
    end_date = attrs.get("end_date", getattr(instance, "end_date", None))
    amount = attrs.get("amount", getattr(instance, "amount", None))

    errors = {}

    if start_date and end_date and start_date > end_date:
        errors["end_date"] = "end_date must be greater than or equal to start_date."

    if request_type in {RequestType.VACATION, RequestType.PERMISSION}:
        if not start_date:
            errors["start_date"] = "This field is required for date-based requests."
        if not end_date:
            errors["end_date"] = "This field is required for date-based requests."

    if request_type == RequestType.REIMBURSEMENT:
        if amount is None:
            errors["amount"] = "This field is required for reimbursement requests."
        elif amount <= 0:
            errors["amount"] = "Amount must be greater than zero."
    elif amount is not None and amount < 0:
        errors["amount"] = "Amount cannot be negative."

    if errors:
        raise serializers.ValidationError(errors)

    return attrs


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

    def validate(self, attrs):
        return validate_request_payload(attrs)

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
        return validate_request_payload(attrs, instance=self.instance)


class ApproveRejectSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True, default="")
