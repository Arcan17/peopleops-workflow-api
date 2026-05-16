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

    def test_employee_cannot_list_approvals(self, employee_client):
        response = employee_client.get(self.URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN
