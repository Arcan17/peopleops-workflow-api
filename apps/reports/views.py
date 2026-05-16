import csv

from django.db.models import Count
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.employees.models import Employee, EmployeeStatus
from apps.employees.permissions import IsManagerOrAdmin
from apps.requests.models import InternalRequest, RequestStatus


class RequestReportView(APIView):
    permission_classes = [IsManagerOrAdmin]

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

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="requests_export.csv"'

        writer = csv.writer(response)
        writer.writerow(["ID", "Employee", "Type", "Status", "Title", "Created At"])

        requests_qs = InternalRequest.objects.select_related("employee").all()
        for req in requests_qs:
            writer.writerow([
                req.id,
                req.employee.email,
                req.get_request_type_display(),
                req.get_status_display(),
                req.title,
                req.created_at.strftime("%Y-%m-%d %H:%M"),
            ])

        return response
