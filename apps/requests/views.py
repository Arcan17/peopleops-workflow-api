from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.approvals.models import Approval, ApprovalDecision
from apps.employees.models import Employee, EmployeeStatus
from apps.employees.permissions import IsManagerOrAdmin
from apps.notifications.models import Notification, NotificationType

from .models import InternalRequest, RequestStatus
from .serializers import (
    ApproveRejectSerializer,
    InternalRequestCreateSerializer,
    InternalRequestSerializer,
    InternalRequestUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Requests"],
        summary="List internal requests",
        description=(
            "Returns a paginated list of requests. "
            "Managers and admins see all requests; employees see only their own."
        ),
    ),
    retrieve=extend_schema(tags=["Requests"], summary="Get request detail"),
    create=extend_schema(
        tags=["Requests"],
        summary="Submit a new internal request",
        description="Create a vacation, permission, reimbursement or document request.",
    ),
    partial_update=extend_schema(
        tags=["Requests"],
        summary="Edit request (owner only, while PENDING)",
    ),
    destroy=extend_schema(tags=["Requests"], summary="Delete request"),
)
class InternalRequestViewSet(viewsets.ModelViewSet):
    queryset = InternalRequest.objects.select_related("employee").all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]
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

    def _ensure_owner_can_edit(self):
        internal_request = self.get_object()
        if internal_request.employee_id != self.request.user.id:
            raise PermissionDenied("Only the request owner can edit a request.")
        return internal_request

    def _can_review_request(self, user, internal_request):
        if internal_request.employee_id == user.id:
            return False
        if user.is_admin:
            return True
        return Employee.objects.filter(
            user=internal_request.employee,
            manager=user,
            status=EmployeeStatus.ACTIVE,
        ).exists()

    def update(self, request, *args, **kwargs):
        self._ensure_owner_can_edit()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._ensure_owner_can_edit()
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["Requests"],
        summary="Approve request",
        description="Approve a pending/in-review request. Manager or Admin only. Creates approval record and notifies employee.",
        request=ApproveRejectSerializer,
    )
    @action(detail=True, methods=["post"], permission_classes=[IsManagerOrAdmin])
    def approve(self, request, pk=None):
        internal_request = self.get_object()
        if not self._can_review_request(request.user, internal_request):
            raise PermissionDenied("You cannot approve this request.")
        if internal_request.status not in (RequestStatus.PENDING, RequestStatus.IN_REVIEW):
            return Response(
                {"detail": "Only pending or in-review requests can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ApproveRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            internal_request.status = RequestStatus.APPROVED
            internal_request.save(update_fields=["status", "updated_at"])
            Approval.objects.create(
                request=internal_request,
                approver=request.user,
                decision=ApprovalDecision.APPROVED,
                comment=serializer.validated_data.get("comment", ""),
            )
            Notification.objects.create(
                recipient=internal_request.employee,
                message=f'Your request "{internal_request.title}" has been approved.',
                notification_type=NotificationType.REQUEST_APPROVED,
                related_request=internal_request,
            )

        return Response(InternalRequestSerializer(internal_request).data)

    @extend_schema(
        tags=["Requests"],
        summary="Reject request",
        description="Reject a pending/in-review request. Manager or Admin only. Creates approval record and notifies employee.",
        request=ApproveRejectSerializer,
    )
    @action(detail=True, methods=["post"], permission_classes=[IsManagerOrAdmin])
    def reject(self, request, pk=None):
        internal_request = self.get_object()
        if not self._can_review_request(request.user, internal_request):
            raise PermissionDenied("You cannot reject this request.")
        if internal_request.status not in (RequestStatus.PENDING, RequestStatus.IN_REVIEW):
            return Response(
                {"detail": "Only pending or in-review requests can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ApproveRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            internal_request.status = RequestStatus.REJECTED
            internal_request.save(update_fields=["status", "updated_at"])
            Approval.objects.create(
                request=internal_request,
                approver=request.user,
                decision=ApprovalDecision.REJECTED,
                comment=serializer.validated_data.get("comment", ""),
            )
            Notification.objects.create(
                recipient=internal_request.employee,
                message=f'Your request "{internal_request.title}" has been rejected.',
                notification_type=NotificationType.REQUEST_REJECTED,
                related_request=internal_request,
            )

        return Response(InternalRequestSerializer(internal_request).data)
