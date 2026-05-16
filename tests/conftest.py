import pytest
from rest_framework.test import APIClient
from apps.accounts.models import CustomUser, Role
from apps.employees.models import Employee
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
def sample_employee(db, employee_user):
    import datetime
    return Employee.objects.create(
        user=employee_user,
        position="Software Engineer",
        department="Engineering",
        hire_date=datetime.date(2023, 1, 15),
        contract_type="full_time",
    )


@pytest.fixture
def sample_request(db, employee_user):
    return InternalRequest.objects.create(
        employee=employee_user,
        request_type=RequestType.VACATION,
        title="Vacation Request",
        description="I need 5 days off.",
        status="pending",
    )
