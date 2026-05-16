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
            "Returns aggregated statistics for all internal requests: "
            "breakdown by status, by request type, total count and pending count. "
            "Manager or Admin only."
        ),
    )
    def get(self, request):
        by_status = (
            InternalRequest.objects
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        by_type = (
            InternalRequest.objects
            .values("request_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        return Response({
            "by_status": list(by_status),
            "by_type": list(by_type),
            "total": InternalRequest.objects.count(),
            "pending": InternalRequest.objects.filter(status=RequestStatus.PENDING).count(),
        })


class EmployeeReportView(APIView):
    permission_classes = [IsManagerOrAdmin]

    @extend_schema(
        tags=["Reports"],
        summary="Employee summary",
        description=(
            "Returns a summary of the employee workforce: "
            "breakdown by employment status, by department, total headcount and active count. "
            "Manager or Admin only."
        ),
    )
    def get(self, request):
        by_status = (
            Employee.objects
            .values("status")
            .annotate(count=Count("id"))
        )
        by_department = (
            Employee.objects
            .values("department")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        return Response({
            "by_status": list(by_status),
            "by_department": list(by_department),
            "total": Employee.objects.count(),
            "active": Employee.objects.filter(status=EmployeeStatus.ACTIVE).count(),
        })


class RequestExportView(APIView):
    permission_classes = [IsManagerOrAdmin]

    @extend_schema(
        tags=["Reports"],
        summary="Export requests to CSV",
        description=(
            "Downloads a CSV file with all internal requests including employee name, "
            "type, status, title and timestamps. Manager or Admin only."
        ),
        responses={(200, "text/csv"): bytes},
    )
    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="requests_export.csv"'

        writer = csv.writer(response)
        writer.writerow(["ID", "Employee", "Type", "Status", "Title", "Start Date", "End Date", "Amount", "Created At"])

        requests_qs = InternalRequest.objects.select_related("employee").all()
        for req in requests_qs:
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
