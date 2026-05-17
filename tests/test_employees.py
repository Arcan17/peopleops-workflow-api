import datetime

import pytest
from rest_framework import status

from apps.accounts.models import CustomUser, Role
from apps.employees.models import Employee


@pytest.mark.django_db
class TestEmployeeEndpoints:
    URL = "/api/employees/"

    def _employee_payload(self):
        return {
            "user": {
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "role": "employee",
                "password": "securepassword123",
            },
            "position": "Backend Developer",
            "department": "Engineering",
            "hire_date": "2024-01-10",
            "contract_type": "full_time",
        }

    # ── List / visibility ─────────────────────────────────────────────────────

    def test_admin_can_list_all_employees(self, admin_client, sample_employee):
        response = admin_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_employee_sees_only_themselves(self, employee_client, sample_employee):
        response = employee_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_manager_sees_only_direct_reports(self, manager_client, manager_user, sample_employee, db):
        """Manager should NOT see employees from other teams."""
        # Create an unrelated employee under a different manager
        other_mgr = CustomUser.objects.create_user(
            email="other_mgr@example.com", password="pass",
            first_name="Other", last_name="Mgr", role=Role.MANAGER,
        )
        other_emp_user = CustomUser.objects.create_user(
            email="other_emp@example.com", password="pass",
            first_name="Other", last_name="Emp", role=Role.EMPLOYEE,
        )
        Employee.objects.create(
            user=other_emp_user, position="QA", department="QA",
            hire_date=datetime.date(2023, 1, 1), manager=other_mgr,
        )

        response = manager_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        emails = [r["email"] for r in response.data["results"]]
        # sample_employee (direct report) is visible
        assert "employee@example.com" in emails
        # other team employee is NOT visible
        assert "other_emp@example.com" not in emails

    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ── Create ────────────────────────────────────────────────────────────────

    def test_admin_can_create_employee(self, admin_client):
        response = admin_client.post(self.URL, self._employee_payload(), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["email"] == "newuser@example.com"

    def test_manager_cannot_create_employee(self, manager_client):
        response = manager_client.post(self.URL, self._employee_payload(), format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_employee_cannot_create_employee(self, employee_client):
        response = employee_client.post(self.URL, self._employee_payload(), format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ── Update — field restrictions ────────────────────────────────────────────

    def test_admin_can_update_salary(self, admin_client, sample_employee):
        """Admins can update sensitive fields like base_salary."""
        response = admin_client.patch(
            f"{self.URL}{sample_employee.id}/",
            {"base_salary": "5000000.00"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        sample_employee.refresh_from_db()
        assert str(sample_employee.base_salary) == "5000000.00"

    def test_manager_cannot_update_salary(self, manager_client, sample_employee):
        """Managers cannot update sensitive fields — salary is silently ignored."""
        original_salary = sample_employee.base_salary
        response = manager_client.patch(
            f"{self.URL}{sample_employee.id}/",
            {"base_salary": "9999999.00", "position": "Lead Developer"},
            format="json",
        )
        # Update succeeds for the allowed field
        assert response.status_code == status.HTTP_200_OK
        sample_employee.refresh_from_db()
        # Salary unchanged — serializer excluded it
        assert sample_employee.base_salary == original_salary
        # Position updated — this field is allowed
        assert sample_employee.position == "Lead Developer"

    # ── Soft delete ───────────────────────────────────────────────────────────

    def test_admin_can_deactivate_employee(self, admin_client, sample_employee):
        response = admin_client.delete(f"{self.URL}{sample_employee.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        sample_employee.refresh_from_db()
        assert sample_employee.status == "inactive"

    # ── Filter / search ───────────────────────────────────────────────────────

    def test_filter_by_department(self, admin_client, sample_employee):
        response = admin_client.get(f"{self.URL}?department=Engineering")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_search_by_name(self, admin_client, sample_employee):
        response = admin_client.get(f"{self.URL}?search=Employee")
        assert response.status_code == status.HTTP_200_OK
