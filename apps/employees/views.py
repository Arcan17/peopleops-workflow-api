from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import EmployeeFilter
from .models import Employee
from .permissions import IsAdminUser, IsManagerOrAdmin
from .serializers import (
    EmployeeCreateSerializer,
    EmployeeSerializer,
    EmployeeUpdateSerializer,
    ManagerEmployeeUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Employees"],
        summary="List employees",
        description=(
            "Returns a paginated list of employees. "
            "Admins see everyone. "
            "Managers see their direct reports (plus their own profile if they have one). "
            "Employees see only their own profile. "
            "Supports filtering by status, department and contract type."
        ),
        parameters=[
            OpenApiParameter("status", description="Filter by status (active/inactive/on_leave)"),
            OpenApiParameter("department", description="Filter by department name"),
            OpenApiParameter("contract_type", description="Filter by contract type"),
            OpenApiParameter("search", description="Search by name, email or position"),
        ],
    ),
    retrieve=extend_schema(tags=["Employees"], summary="Get employee detail"),
    create=extend_schema(
        tags=["Employees"],
        summary="Create employee",
        description="Create a new employee record. Admin only.",
    ),
    update=extend_schema(
        tags=["Employees"],
        summary="Update employee",
        description=(
            "Update an employee. Manager or Admin only. "
            "Admins may change any field including salary, status and manager. "
            "Managers may only update position, department, hire_date and contract_type."
        ),
    ),
    partial_update=extend_schema(
        tags=["Employees"],
        summary="Partial update employee",
        description=(
            "Partial update of an employee. Manager or Admin only. "
            "Same field restrictions as full update apply."
        ),
    ),
    destroy=extend_schema(
        tags=["Employees"],
        summary="Deactivate employee (soft delete)",
        description="Sets employee status to inactive and deactivates the user account. Admin only. Data is preserved.",
    ),
)
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("user", "manager").all()
    filterset_class = EmployeeFilter
    search_fields = ["user__first_name", "user__last_name", "user__email", "position", "department"]
    ordering_fields = ["hire_date", "department", "status"]
    ordering = ["user__first_name"]

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsAdminUser()]
        if self.action in ("update", "partial_update"):
            return [IsManagerOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return EmployeeCreateSerializer
        if self.action in ("update", "partial_update"):
            # Admins can change all fields (salary, status, manager reassignment)
            # Managers can only change operational fields
            if self.request.user.is_admin:
                return EmployeeUpdateSerializer
            return ManagerEmployeeUpdateSerializer
        return EmployeeSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return super().get_queryset()
        if user.is_manager:
            # Direct reports + the manager's own profile (if they have an Employee record)
            return super().get_queryset().filter(
                Q(manager=user) | Q(user=user)
            )
        return super().get_queryset().filter(user=user)

    def destroy(self, request, *args, **kwargs):
        """Soft delete: set status to inactive instead of deleting."""
        employee = self.get_object()
        employee.status = "inactive"
        employee.user.is_active = False
        employee.user.save()
        employee.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
