from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser, Role
from apps.employees.models import Employee
from apps.notifications.models import Notification, NotificationType
from apps.requests.models import InternalRequest, RequestType


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return CustomUser.objects.create_user(
        email="admin@example.com",
        password="adminpass123",
        first_name="Admin",
        last_name="User",
        role=Role.ADMIN,
        is_staff=True,
    )


@pytest.fixture
def manager_user(db):
    return CustomUser.objects.create_user(
        email="manager@example.com",
        password="managerpass123",
        first_name="Manager",
        last_name="User",
        role=Role.MANAGER,
    )


@pytest.fixture
def employee_user(db):
    return CustomUser.objects.create_user(
        email="employee@example.com",
        password="employeepass123",
        first_name="Employee",
        last_name="User",
        role=Role.EMPLOYEE,
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def manager_client(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    return api_client


@pytest.fixture
def employee_client(api_client, employee_user):
    api_client.force_authenticate(user=employee_user)
    return api_client


@pytest.fixture
def sample_employee(db, employee_user, manager_user):
    import datetime
    return Employee.objects.create(
        user=employee_user,
        position="Software Engineer",
        department="Engineering",
        hire_date=datetime.date(2023, 1, 15),
        contract_type="full_time",
        manager=manager_user,
    )


@pytest.fixture
def sample_request(db, employee_user, sample_employee):
    start_date = timezone.now().date() + timedelta(days=10)
    end_date = start_date + timedelta(days=4)
    return InternalRequest.objects.create(
        employee=employee_user,
        request_type=RequestType.VACATION,
        title="Vacation Request",
        description="I need 5 days off.",
        status="pending",
        start_date=start_date,
        end_date=end_date,
    )


@pytest.fixture
def sample_notification(db, employee_user, sample_request):
    return Notification.objects.create(
        recipient=employee_user,
        message="You have a pending update.",
        notification_type=NotificationType.GENERAL,
        related_request=sample_request,
    )


@pytest.fixture
def sample_document_file():
    return SimpleUploadedFile(
        "contract.txt",
        b"sample contract content",
        content_type="text/plain",
    )
