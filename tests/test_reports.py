import pytest
from rest_framework import status


@pytest.mark.django_db
class TestReports:
    def test_manager_can_view_request_report(self, manager_client, sample_request):
        response = manager_client.get("/api/reports/requests/")
        assert response.status_code == status.HTTP_200_OK
        assert "total" in response.data
        assert "by_status" in response.data
        assert "by_type" in response.data

    def test_employee_cannot_view_report(self, employee_client):
        response = employee_client.get("/api/reports/requests/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_report(self, admin_client, sample_employee):
        response = admin_client.get("/api/reports/employees/")
        assert response.status_code == status.HTTP_200_OK
        assert "total" in response.data
        assert "active" in response.data

    def test_csv_export(self, manager_client, sample_request):
        response = manager_client.get("/api/reports/requests/export/")
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        content = b"".join(response.streaming_content) if hasattr(response, "streaming_content") else response.content
        assert b"ID" in content
        assert b"Employee" in content
