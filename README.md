# PeopleOps Workflow API

[![CI](https://github.com/Arcan17/peopleops-workflow-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Arcan17/peopleops-workflow-api/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.x-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-red.svg)](https://www.django-rest-framework.org/)

Backend API for HR workflow automation. Manages employees, internal requests, approvals, documents, notifications and reports. Includes role-based permissions, JWT auth, async tasks with Celery/Redis, automated tests and CI.

## Tech Stack

- **Python 3.11** · **Django 5** · **Django REST Framework**
- **PostgreSQL 15** · **Redis 7** · **Celery** (async tasks)
- **pytest** · **pytest-django** (automated testing)
- **drf-spectacular** (OpenAPI/Swagger docs)
- **Docker** · **Docker Compose** · **GitHub Actions** CI

## Features

| Module | Description |
|--------|-------------|
| **Employees** | CRUD with role-based access, soft delete, filters |
| **Requests** | Vacation, permissions, reimbursements, document requests |
| **Approvals** | Approve/reject workflow with comments and manager ownership checks |
| **Documents** | File upload per employee with type classification |
| **Notifications** | Auto-generated on status changes, mark-as-read |
| **Reports** | JSON summaries + CSV export |

## Role Permissions

| Action | Employee | Manager | Admin |
|--------|----------|---------|-------|
| View own profile/requests | ✅ | ✅ | ✅ |
| Create request | ✅ | ✅ | ✅ |
| Approve/reject direct reports | ❌ | ✅ | ❌ |
| Approve/reject any request | ❌ | ❌ | ✅ |
| View all employees | ❌ | ✅ | ✅ |
| Create/edit employees | ❌ | ❌ | ✅ |
| View reports | ❌ | ✅ | ✅ |

## Quick Start

```bash
# Clone
git clone https://github.com/Arcan17/peopleops-workflow-api.git
cd peopleops-workflow-api

# Configure environment
cp .env.example .env

# Development mode for local Docker
echo "DEBUG=True" >> .env
echo "SECRET_KEY=django-insecure-development-key-12345" >> .env

# Start all services
docker compose up -d

# Create superuser
make superuser
```

Visit:
- **API**: http://localhost:8000/api/
- **Swagger UI**: http://localhost:8000/api/docs/
- **Admin panel**: http://localhost:8000/admin/

Production-style defaults stay disabled unless you explicitly set environment variables such as `SECRET_KEY`, `ALLOWED_HOSTS`, and `DJANGO_SETTINGS_MODULE=config.settings.production`.

## API Endpoints

### Auth
```
POST /api/auth/token/          → Get JWT token
POST /api/auth/token/refresh/  → Refresh token
```

### Employees
```
GET    /api/employees/             → List employees
POST   /api/employees/             → Create employee (admin only)
GET    /api/employees/{id}/        → Employee detail
PATCH  /api/employees/{id}/        → Update employee
DELETE /api/employees/{id}/        → Deactivate employee (soft delete)
```

### Requests
```
GET    /api/requests/              → List requests
POST   /api/requests/              → Create request
GET    /api/requests/{id}/         → Request detail
PATCH  /api/requests/{id}/         → Edit own pending request
POST   /api/requests/{id}/approve/ → Approve (manager/admin)
POST   /api/requests/{id}/reject/  → Reject (manager/admin)
```

### Reports
```
GET /api/reports/requests/         → Request statistics (JSON)
GET /api/reports/employees/        → Employee summary (JSON)
GET /api/reports/requests/export/  → CSV download
```

## Running Tests

```bash
# Install test dependencies
pip install -r requirements/test.txt

# Run all tests with coverage
python -m pytest tests/ -v --cov=apps --cov-report=term-missing

# Run specific module
python -m pytest tests/test_requests.py -v
```

## Project Structure

```
peopleops-workflow-api/
├── apps/
│   ├── accounts/        # CustomUser, roles
│   ├── employees/       # Employee CRUD
│   ├── requests/        # Internal requests
│   ├── approvals/       # Approval workflow
│   ├── documents/       # Document management
│   ├── notifications/   # Auto-notifications
│   └── reports/         # Reports & CSV export
├── config/
│   ├── settings/        # base / development / testing
│   ├── urls.py
│   └── celery.py
├── tests/               # pytest test suite
├── docker-compose.yml
├── Dockerfile
└── .github/workflows/ci.yml
```
