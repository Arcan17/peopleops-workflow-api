import pytest
from rest_framework import status


@pytest.mark.django_db
class TestInternalRequests:
    URL = "/api/requests/"

    def _request_payload(self):
        return {
            "request_type": "vacation",
            "title": "5-Day Vacation",
            "description": "Family trip planned for the summer.",
            "start_date": "2025-07-01",
            "end_date": "2025-07-05",
        }

    # ── Create ────────────────────────────────────────────────────────────────
    def test_employee_can_create_request(self, employee_client):
        response = employee_client.post(self.URL, self._request_payload(), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "pending"

    def test_unauthenticated_cannot_create(self, api_client):
        response = api_client.post(self.URL, self._request_payload(), format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ── List ──────────────────────────────────────────────────────────────────
    def test_employee_sees_only_own_requests(self, employee_client, sample_request, admin_user):
        from apps.requests.models import InternalRequest
        # Admin also has a request
        InternalRequest.objects.create(
            employee=admin_user, request_type="permission",
            title="Admin request", description="test"
        )
        response = employee_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        emails = [r["employee"]["email"] for r in response.data["results"]]
        assert all(e == "employee@example.com" for e in emails)

    def test_admin_sees_all_requests(self, admin_client, sample_request):
        response = admin_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    # ── Approve / Reject ──────────────────────────────────────────────────────
    def test_manager_can_approve_request(self, manager_client, sample_request):
        response = manager_client.post(
            f"{self.URL}{sample_request.id}/approve/",
            {"comment": "Looks good!"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "approved"

    def test_manager_can_reject_request(self, manager_client, sample_request):
        response = manager_client.post(
            f"{self.URL}{sample_request.id}/reject/",
            {"comment": "Not this week."},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "rejected"

    def test_employee_cannot_approve_request(self, employee_client, sample_request):
        response = employee_client.post(f"{self.URL}{sample_request.id}/approve/", {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cannot_approve_own_request(self, admin_client, admin_user):
        from apps.requests.models import InternalRequest
        own_request = InternalRequest.objects.create(
            employee=admin_user,
            request_type="permission",
            title="Own request",
            description="self review should fail",
        )
        response = admin_client.post(f"{self.URL}{own_request.id}/approve/", {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_cannot_approve_request_without_reporting_line(self, manager_client, sample_request):
        from apps.employees.models import Employee
        Employee.objects.filter(user=sample_request.employee).update(manager=None)
        response = manager_client.post(f"{self.URL}{sample_request.id}/approve/", {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_approve_already_approved_request(self, manager_client, sample_request):
        manager_client.post(f"{self.URL}{sample_request.id}/approve/", {})
        response = manager_client.post(f"{self.URL}{sample_request.id}/approve/", {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ── Update ─────────────────────────────────────────────────────────────────
    def test_employee_can_edit_own_pending_request(self, employee_client, sample_request):
        response = employee_client.patch(
            f"{self.URL}{sample_request.id}/",
            {"title": "Updated title"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated title"

    def test_manager_cannot_edit_employee_request(self, manager_client, sample_request):
        response = manager_client.patch(
            f"{self.URL}{sample_request.id}/",
            {"title": "Manager edit"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_request_rejects_invalid_date_range(self, employee_client):
        payload = self._request_payload()
        payload["start_date"] = "2025-07-10"
        payload["end_date"] = "2025-07-05"
        response = employee_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "end_date" in response.data

    def test_reimbursement_requires_positive_amount(self, employee_client):
        response = employee_client.post(
            self.URL,
            {
                "request_type": "reimbursement",
                "title": "Taxi",
                "description": "Airport transfer",
                "amount": 0,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "amount" in response.data

    # ── Notifications ─────────────────────────────────────────────────────────
    def test_notification_created_on_approve(self, manager_client, sample_request):
        from apps.notifications.models import Notification
        manager_client.post(f"{self.URL}{sample_request.id}/approve/", {})
        assert Notification.objects.filter(
            recipient=sample_request.employee,
            notification_type="request_approved",
        ).exists()

    def test_notification_created_on_reject(self, manager_client, sample_request):
        from apps.notifications.models import Notification
        manager_client.post(f"{self.URL}{sample_request.id}/reject/", {})
        assert Notification.objects.filter(
            recipient=sample_request.employee,
            notification_type="request_rejected",
        ).exists()
