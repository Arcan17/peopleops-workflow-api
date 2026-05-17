import csv

from django.db.models import Count
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.employees.models import Employee, EmployeeStatus
from apps.employees.permissions import IsManagerOrAdmin
from apps.requests.models import InternalRequest, RequestStatus


class RequestReportView(APIView):
    permission_classes = [IsManagerOrAdmin]

    @extend_schema(
        tags=["Reports"],
        summary="Request statistics",
        description=(
            "Returns aggregated statistics for internal requests: "
            "breakdown by status, by request type, total count and pending count. "
            "Admins see all requests; managers see only their direct reports' requests. "
            "Manager or Admin only."
        ),
    )
    def get(self, request):
        qs = self._base_queryset(request.user)

        by_status = (
            qs.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        by_type = (
            qs.values("request_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        return Response({
            "by_status": list(by_status),
            "by_type": list(by_type),
            "total": qs.count(),
            "pending": qs.filter(status=RequestStatus.PENDING).count(),
        })

    @staticmethod
    def _base_queryset(user):
        qs = InternalRequest.objects
        if not user.is_admin:
            # Managers see only requests submitted by their direct reports
            qs = qs.filter(employee__employee_profile__manager=user)
        return qs


class EmployeeReportView(APIView):
    permission_classes = [IsManagerOrAdmin]

    @extend_schema(
        tags=["Reports"],
        summary="Employee summary",
        description=(
            "Returns a summary of the employee workforce: "
            "breakdown by employment status, by department, total headcount and active count. "
            "Admins see all employees; managers see only their direct reports. "
            "Manager or Admin only."
        ),
    )
    def get(self, request):
        qs = self._base_queryset(request.user)

        by_status = (
            qs.values("status")
            .annotate(count=Count("id"))
        )
        by_department = (
            qs.values("department")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        return Response({
            "by_status": list(by_status),
            "by_department": list(by_department),
            "total": qs.count(),
            "active": qs.filter(status=EmployeeStatus.ACTIVE).count(),
        })

    @staticmethod
    def _base_queryset(user):
        if user.is_admin:
            return Employee.objects.all()
        return Employee.objects.filter(manager=user)


class RequestExportView(APIView):
    permission_classes = [IsManagerOrAdmin]

    @extend_schema(
        tags=["Reports"],
        summary="Export requests to CSV",
        description=(
            "Downloads a CSV file with internal requests. "
            "Admins get all requests; managers get only their direct reports' requests. "
            "Manager or Admin only."
        ),
        responses={(200, "text/csv"): bytes},
    )
    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="requests_export.csv"'

        writer = csv.writer(response)
        writer.writerow(["ID", "Employee", "Type", "Status", "Title", "Start Date", "End Date", "Amount", "Created At"])

        qs = RequestReportView._base_queryset(request.user).select_related("employee")
        for req in qs:
            writer.writerow([
                req.id,
                req.employee.email,
                req.get_request_type_display(),
                req.get_status_display(),
                req.title,
                req.start_date or "",
                req.end_date or "",
                req.amount or "",
                req.created_at.strftime("%Y-%m-%d %H:%M"),
            ])

        return response
