from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.employees.permissions import IsManagerOrAdmin

from .models import InternalRequest, RequestStatus
from .serializers import (
    ApproveRejectSerializer,
    InternalRequestCreateSerializer,
    InternalRequestSerializer,
    InternalRequestUpdateSerializer,
)
from .services import RequestWorkflowService


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
        """Only the request owner may edit, and only while status=PENDING."""
        internal_request = self.get_object()
        if internal_request.employee_id != self.request.user.id:
            raise PermissionDenied("Only the request owner can edit a request.")
        if internal_request.status != RequestStatus.PENDING:
            raise PermissionDenied("Requests can only be edited while they are pending.")
        return internal_request

    def update(self, request, *args, **kwargs):
        self._ensure_owner_can_edit()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._ensure_owner_can_edit()
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["Requests"],
        summary="Approve request",
        description=(
            "Approve a pending or in-review request. "
            "Manager (direct reports only) or Admin. "
            "Creates an Approval record and notifies the employee."
        ),
        request=ApproveRejectSerializer,
    )
    @action(detail=True, methods=["post"], permission_classes=[IsManagerOrAdmin])
    def approve(self, request, pk=None):
        internal_request = self.get_object()
        serializer = ApproveRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # All business rules (permission + status) enforced inside the service
        RequestWorkflowService.approve(
            internal_request,
            request.user,
            comment=serializer.validated_data.get("comment", ""),
        )
        return Response(InternalRequestSerializer(internal_request).data)

    @extend_schema(
        tags=["Requests"],
        summary="Reject request",
        description=(
            "Reject a pending or in-review request. "
            "Manager (direct reports only) or Admin. "
            "Creates an Approval record and notifies the employee."
        ),
        request=ApproveRejectSerializer,
    )
    @action(detail=True, methods=["post"], permission_classes=[IsManagerOrAdmin])
    def reject(self, request, pk=None):
        internal_request = self.get_object()
        serializer = ApproveRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # All business rules (permission + status) enforced inside the service
        RequestWorkflowService.reject(
            internal_request,
            request.user,
            comment=serializer.validated_data.get("comment", ""),
        )
        return Response(InternalRequestSerializer(internal_request).data)
