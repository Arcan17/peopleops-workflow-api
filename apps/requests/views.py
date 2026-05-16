from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import InternalRequest, RequestStatus
from .serializers import (
    InternalRequestSerializer,
    InternalRequestCreateSerializer,
    InternalRequestUpdateSerializer,
    ApproveRejectSerializer,
)
from apps.employees.permissions import IsManagerOrAdmin


class InternalRequestViewSet(viewsets.ModelViewSet):
    queryset = InternalRequest.objects.select_related("employee").all()
    permission_classes = [IsAuthenticated]
    search_fields = ["title", "description", "employee__email"]
    ordering_fields = ["created_at", "status", "request_type"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return InternalRequestCreateSerializer
        if self.action in ("update", "partial_update"):
            return InternalRequestUpdateSerializer
        if self.action in ("approve", "reject"):
            return ApproveRejectSerializer
        return InternalRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(InternalRequestSerializer(instance).data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        user = self.request.user
        if user.is_manager_or_admin:
            return super().get_queryset()
        return super().get_queryset().filter(employee=user)

    @action(detail=True, methods=["post"], permission_classes=[IsManagerOrAdmin])
    def approve(self, request, pk=None):
        internal_request = self.get_object()
        if internal_request.status not in (RequestStatus.PENDING, RequestStatus.IN_REVIEW):
            return Response(
                {"detail": "Only pending or in-review requests can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ApproveRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        internal_request.status = RequestStatus.APPROVED
        internal_request.save()

        # Create approval record
        from apps.approvals.models import Approval
        Approval.objects.create(
            request=internal_request,
            approver=request.user,
            decision="approved",
            comment=serializer.validated_data.get("comment", ""),
        )

        # Create notification for the employee
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=internal_request.employee,
            message=f'Your request "{internal_request.title}" has been approved.',
            notification_type="request_approved",
            related_request=internal_request,
        )

        return Response(InternalRequestSerializer(internal_request).data)

    @action(detail=True, methods=["post"], permission_classes=[IsManagerOrAdmin])
    def reject(self, request, pk=None):
        internal_request = self.get_object()
        if internal_request.status not in (RequestStatus.PENDING, RequestStatus.IN_REVIEW):
            return Response(
                {"detail": "Only pending or in-review requests can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ApproveRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        internal_request.status = RequestStatus.REJECTED
        internal_request.save()

        from apps.approvals.models import Approval
        Approval.objects.create(
            request=internal_request,
            approver=request.user,
            decision="rejected",
            comment=serializer.validated_data.get("comment", ""),
        )

        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=internal_request.employee,
            message=f'Your request "{internal_request.title}" has been rejected.',
            notification_type="request_rejected",
            related_request=internal_request,
        )

        return Response(InternalRequestSerializer(internal_request).data)
