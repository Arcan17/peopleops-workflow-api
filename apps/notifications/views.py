from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Notifications"],
        summary="List my notifications",
        description="Returns all notifications for the authenticated user, ordered by most recent.",
    ),
    retrieve=extend_schema(tags=["Notifications"], summary="Get notification detail"),
    partial_update=extend_schema(
        tags=["Notifications"],
        summary="Mark notification as read",
        description="Set is_read=true on a single notification.",
    ),
)
class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Notifications are system-generated — manual creation via API is not allowed.

    Supported operations:
      GET  /api/notifications/          → list own notifications
      GET  /api/notifications/{id}/     → detail
      PATCH /api/notifications/{id}/    → mark as read
      POST  /api/notifications/read_all/ → mark all as read
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @extend_schema(
        tags=["Notifications"],
        summary="Mark all notifications as read",
        description="Marks all unread notifications of the current user as read in a single operation.",
    )
    @action(detail=False, methods=["post"])
    def read_all(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"marked_read": updated})
