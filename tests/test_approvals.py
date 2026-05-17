import pytest
from rest_framework import status


@pytest.mark.django_db
class TestApprovals:
    URL = "/api/approvals/"

    def test_manager_can_list_approvals(self, manager_client, sample_request):
        manager_client.post(f"/api/requests/{sample_request.id}/approve/", {})
        response = manager_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_manager_sees_only_direct_reports_approvals(self, manager_client, sample_request):
        from apps.accounts.models import CustomUser, Role
        from apps.approvals.models import Approval
        from apps.employees.models import Employee
        from apps.requests.models import InternalRequest

        manager_client.post(f"/api/requests/{sample_request.id}/approve/", {})

        other_manager = CustomUser.objects.create_user(
            email="other-manager@example.com",
            password="managerpass123",
            first_name="Other",
            last_name="Manager",
            role=Role.MANAGER,
        )
        other_employee = CustomUser.objects.create_user(
            email="other-employee@example.com",
            password="employeepass123",
            first_name="Other",
            last_name="Employee",
            role=Role.EMPLOYEE,
        )
        Employee.objects.create(
            user=other_employee,
            position="QA Engineer",
            department="Engineering",
            hire_date="2024-01-10",
            contract_type="full_time",
            manager=other_manager,
        )
        other_request = InternalRequest.objects.create(
            employee=other_employee,
            request_type="permission",
            title="Other approval",
            description="Should not be visible to manager_user",
            status="approved",
        )
        Approval.objects.create(
            request=other_request,
            approver=other_manager,
            decision="approved",
            comment="Approved by another manager",
        )

        response = manager_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        visible_ids = {item["request"] for item in response.data["results"]}
        assert sample_request.id in visible_ids
        assert other_request.id not in visible_ids

    def test_employee_cannot_list_approvals(self, employee_client):
        response = employee_client.get(self.URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN
