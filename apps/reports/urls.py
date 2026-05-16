from django.urls import path

from .views import EmployeeReportView, RequestExportView, RequestReportView

urlpatterns = [
    path("requests/", RequestReportView.as_view(), name="report-requests"),
    path("employees/", EmployeeReportView.as_view(), name="report-employees"),
    path("requests/export/", RequestExportView.as_view(), name="report-requests-export"),
]
