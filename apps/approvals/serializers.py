from rest_framework import serializers
from .models import Approval
from apps.accounts.serializers import UserSerializer


class ApprovalSerializer(serializers.ModelSerializer):
    approver = UserSerializer(read_only=True)
    decision_display = serializers.CharField(source="get_decision_display", read_only=True)

    class Meta:
        model = Approval
        fields = ["id", "request", "approver", "decision", "decision_display", "comment", "decided_at"]
        read_only_fields = ["id", "approver", "decided_at"]
