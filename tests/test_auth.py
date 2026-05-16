import pytest
from rest_framework import status


@pytest.mark.django_db
class TestAuthentication:
    URL = "/api/auth/token/"
    REFRESH_URL = "/api/auth/token/refresh/"

    def test_obtain_token_valid_credentials(self, api_client, employee_user):
        response = api_client.post(self.URL, {"email": "employee@example.com", "password": "employeepass123"})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_obtain_token_invalid_password(self, api_client, employee_user):
        response = api_client.post(self.URL, {"email": "employee@example.com", "password": "wrongpassword"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_obtain_token_nonexistent_user(self, api_client):
        response = api_client.post(self.URL, {"email": "nobody@example.com", "password": "any"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token(self, api_client, employee_user):
        response = api_client.post(self.URL, {"email": "employee@example.com", "password": "employeepass123"})
        refresh = response.data["refresh"]
        refresh_response = api_client.post(self.REFRESH_URL, {"refresh": refresh})
        assert refresh_response.status_code == status.HTTP_200_OK
        assert "access" in refresh_response.data

    def test_protected_endpoint_without_token(self, api_client):
        response = api_client.get("/api/employees/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
