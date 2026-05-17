import pytest
from rest_framework import status


@pytest.mark.django_db
class TestNotifications:
    URL = "/api/notifications/"

    def test_employee_sees_only_own_notifications(self, employee_client, sample_notification, admin_user):
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=admin_user,
            message="Admin only",
            notification_type="general",
        )
        response = employee_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_read_all_marks_notifications_as_read(self, employee_client, sample_notification):
        response = employee_client.post(f"{self.URL}read_all/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["marked_read"] == 1

    def test_create_notification_via_api_is_not_allowed(self, employee_client):
        """POST /api/notifications/ must not be a valid endpoint — notifications are system-generated."""
        response = employee_client.post(
            self.URL,
            {"message": "Injected notification", "notification_type": "general"},
            format="json",
        )
        # The endpoint should not exist (405 Method Not Allowed)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_unauthenticated_cannot_list_notifications(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
