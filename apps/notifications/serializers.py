from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_notification_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "message", "notification_type", "type_display", "related_request", "is_read", "created_at"]
        read_only_fields = ["id", "message", "notification_type", "related_request", "created_at"]
