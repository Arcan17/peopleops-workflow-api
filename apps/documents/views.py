from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.employees.permissions import IsManagerOrAdmin

from .models import Document
from .serializers import DocumentSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Documents"],
        summary="List documents",
        description=(
            "Admins see all documents. "
            "Managers see only documents belonging to their direct reports. "
            "Employees see only their own documents."
        ),
    ),
    retrieve=extend_schema(tags=["Documents"], summary="Get document detail"),
    create=extend_schema(
        tags=["Documents"],
        summary="Upload a document",
        description=(
            "Upload a file for an employee. "
            "Admins may upload for any employee; "
            "managers may only upload for their direct reports. "
            "Accepted file types: PDF, DOCX, JPEG, PNG (max 10 MB)."
        ),
    ),
    destroy=extend_schema(tags=["Documents"], summary="Delete document — Manager or Admin"),
)
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.select_related("employee", "uploaded_by").all()
    serializer_class = DocumentSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsManagerOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            # Admins see every document in the system
            return super().get_queryset()
        if user.is_manager:
            # Managers see only documents for employees who report to them
            return super().get_queryset().filter(employee__manager=user)
        # Employees see only their own documents
        return super().get_queryset().filter(employee__user=user)

    def perform_create(self, serializer):
        """
        Enforce the upload restriction: a manager may only upload documents
        for employees who report directly to them.  Admins have no restriction.
        """
        user = self.request.user
        employee = serializer.validated_data["employee"]

        if not user.is_admin and employee.manager_id != user.id:
            raise PermissionDenied(
                "You can only upload documents for employees who report directly to you."
            )
        serializer.save()
