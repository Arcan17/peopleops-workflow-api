import pytest
from rest_framework import status


@pytest.mark.django_db
class TestReports:
    # ── Request report ────────────────────────────────────────────────────────

    def test_manager_can_view_request_report(self, manager_client, sample_request):
        response = manager_client.get("/api/reports/requests/")
        assert response.status_code == status.HTTP_200_OK
        assert "total" in response.data
        assert "by_status" in response.data
        assert "by_type" in response.data

    def test_employee_cannot_view_report(self, employee_client):
        response = employee_client.get("/api/reports/requests/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_sees_all_requests_in_report(self, admin_client, sample_request):
        response = admin_client.get("/api/reports/requests/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total"] >= 1

    def test_manager_report_scoped_to_direct_reports(self, manager_client, manager_user, employee_user, sample_request):
        """Manager's report total should only count their direct reports' requests."""
        from apps.accounts.models import CustomUser, Role
        from apps.requests.models import InternalRequest, RequestStatus, RequestType

        # Create another request from a user NOT managed by manager_user
        other_user = CustomUser.objects.create_user(
            email="unrelated@example.com", password="pass",
            first_name="Unrelated", last_name="User", role=Role.EMPLOYEE,
        )
        InternalRequest.objects.create(
            employee=other_user,
            request_type=RequestType.PERMISSION,
            status=RequestStatus.PENDING,
            title="Unrelated request",
            description="Should not appear in manager's report",
        )

        response = manager_client.get("/api/reports/requests/")
        assert response.status_code == status.HTTP_200_OK
        # Manager should only see sample_request (from their direct report)
        assert response.data["total"] == 1

    # ── Employee report ───────────────────────────────────────────────────────

    def test_employee_report(self, admin_client, sample_employee):
        response = admin_client.get("/api/reports/employees/")
        assert response.status_code == status.HTTP_200_OK
        assert "total" in response.data
        assert "active" in response.data

    def test_manager_employee_report_scoped_to_team(self, manager_client, sample_employee):
        """Manager's employee report should only show their direct reports."""
        response = manager_client.get("/api/reports/employees/")
        assert response.status_code == status.HTTP_200_OK
        # sample_employee reports to manager_user
        assert response.data["total"] >= 1

    # ── CSV export ────────────────────────────────────────────────────────────

    def test_csv_export(self, manager_client, sample_request):
        response = manager_client.get("/api/reports/requests/export/")
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        content = b"".join(response.streaming_content) if hasattr(response, "streaming_content") else response.content
        assert b"ID" in content
        assert b"Employee" in content

    def test_admin_csv_export_contains_all_requests(self, admin_client, sample_request):
        response = admin_client.get("/api/reports/requests/export/")
        assert response.status_code == status.HTTP_200_OK
        content = b"".join(response.streaming_content) if hasattr(response, "streaming_content") else response.content
        assert b"Vacation Request" in content
