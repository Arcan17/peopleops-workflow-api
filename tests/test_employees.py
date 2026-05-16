
import pytest
from rest_framework import status


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

    # ── List ──────────────────────────────────────────────────────────────────
    def test_admin_can_list_all_employees(self, admin_client, sample_employee):
        response = admin_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_employee_sees_only_themselves(self, employee_client, sample_employee):
        response = employee_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

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

    # ── Soft delete ───────────────────────────────────────────────────────────
    def test_admin_can_deactivate_employee(self, admin_client, sample_employee):
        response = admin_client.delete(f"{self.URL}{sample_employee.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        sample_employee.refresh_from_db()
        assert sample_employee.status == "inactive"

    # ── Filter ────────────────────────────────────────────────────────────────
    def test_filter_by_department(self, admin_client, sample_employee):
        response = admin_client.get(f"{self.URL}?department=Engineering")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_search_by_name(self, admin_client, sample_employee):
        response = admin_client.get(f"{self.URL}?search=Employee")
        assert response.status_code == status.HTTP_200_OK
