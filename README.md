# PeopleOps Workflow API

[![CI](https://github.com/Arcan17/peopleops-workflow-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Arcan17/peopleops-workflow-api/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.x-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.15-red.svg)](https://www.django-rest-framework.org/)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](#running-tests)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Backend REST API for **HR workflow automation** — built to demonstrate production-grade Django patterns for backend engineering roles.

Handles the full lifecycle of employee requests: from creation and review through approval or rejection, with automatic notifications, document management, scheduled background tasks and analytics reports.

---

## What this project demonstrates

| Skill | Implementation |
|---|---|
| **Django REST Framework** | ModelViewSets, custom actions, serializer layering, permission classes |
| **Role-based access control** | Admin / Manager / Employee roles with per-action permission enforcement |
| **Business logic enforcement** | Manager can only approve direct reports; owner-only edits; soft delete |
| **Async background tasks** | Celery + Redis: expiry checks, reminder notifications, weekly reports |
| **Database design** | PostgreSQL with migrations, FKs, select_related, bulk operations |
| **API documentation** | drf-spectacular with OpenAPI tags, summaries and Swagger/ReDoc UIs |
| **Automated testing** | pytest-django, 59 tests, 90% coverage, no external services in CI |
| **CI/CD** | GitHub Actions: lint (ruff) + migration check + test coverage threshold |
| **Containerization** | Docker Compose with 5 services: api, db, redis, celery-worker, celery-beat |
| **Admin interface** | Fully configured Django Admin with bulk actions, badges, fieldsets |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | Django 5.1 · Django REST Framework 3.15 |
| Database | PostgreSQL 15 |
| Cache / Broker | Redis 7 |
| Task queue | Celery 5.4 + django-celery-beat |
| Auth | SimpleJWT (access 1h, refresh 7d) |
| Docs | drf-spectacular (OpenAPI 3.0) |
| Testing | pytest · pytest-django · pytest-cov |
| Linting | ruff |
| Containers | Docker · Docker Compose |
| CI/CD | GitHub Actions |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐   │
│  │ Postgres │   │  Redis   │   │   Django + DRF   │   │
│  │    15    │   │    7     │   │   (Gunicorn 3w)  │   │
│  └──────────┘   └──────────┘   └──────────────────┘   │
│       │               │                  │              │
│       └───────────────┤      ┌───────────┘              │
│                       │      │                          │
│                  ┌────┴──────┴────┐                    │
│                  │  Celery Worker │                    │
│                  │  Celery Beat   │                    │
│                  └────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

### Application modules

```
apps/
├── accounts/      CustomUser with AbstractBaseUser, role enum (admin/manager/employee)
├── employees/     Employee profiles, soft delete, manager hierarchy, filters
├── requests/      InternalRequest workflow: create → review → approve/reject
├── approvals/     Approval records auto-created on request decision
├── documents/     File upload per employee (contract, payslip, certificate…)
├── notifications/ Auto-generated on status change; mark-as-read support
└── reports/       Aggregated JSON stats + CSV export
```

---

## Role Permissions

| Action | Employee | Manager | Admin |
|---|:---:|:---:|:---:|
| View own profile / requests | ✅ | ✅ | ✅ |
| Create internal request | ✅ | ✅ | ✅ |
| Edit own pending request | ✅ | ❌ | ❌ |
| Approve / reject direct reports | ❌ | ✅ | ❌ |
| Approve / reject any request | ❌ | ❌ | ✅ |
| View all employees | ❌ | ✅ | ✅ |
| Create / deactivate employees | ❌ | ❌ | ✅ |
| Upload / delete documents | ❌ | ✅ | ✅ |
| View reports | ❌ | ✅ | ✅ |
| Django Admin access | ❌ | ❌ | ✅ |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Arcan17/peopleops-workflow-api.git
cd peopleops-workflow-api

# 2. Configure environment
cp .env.example .env

# 3. Start all services (api + db + redis + celery-worker + celery-beat)
docker compose up -d --build

# 4. Seed demo data (users, requests, approvals, notifications)
docker compose exec api python manage.py seed_demo
```

| Interface | URL |
|---|---|
| Swagger UI | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| Django Admin | http://localhost:8000/admin/ |
| OpenAPI schema | http://localhost:8000/api/schema/ |

---

## Demo Credentials

Populated automatically by `seed_demo`:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@peopleops.com` | `Admin1234!` |
| Manager | `carlos@peopleops.com` | `Manager1234!` |
| Manager | `sofia@peopleops.com` | `Manager1234!` |
| Employee | `ana@peopleops.com` | `Employee1234!` |
| Employee | `pedro@peopleops.com` | `Employee1234!` |
| Employee | `lucia@peopleops.com` | `Employee1234!` |

---

## API Endpoints

### Authentication
```
POST /api/auth/token/          → Obtain JWT (access + refresh)
POST /api/auth/token/refresh/  → Refresh access token
```

### Employees
```
GET    /api/employees/             → List (filters: status, department, contract_type, search)
POST   /api/employees/             → Create employee — Admin only
GET    /api/employees/{id}/        → Detail
PATCH  /api/employees/{id}/        → Update — Manager or Admin
DELETE /api/employees/{id}/        → Soft delete (sets status=inactive) — Admin only
```

### Internal Requests
```
GET    /api/requests/              → List (employees see own; managers/admins see all)
POST   /api/requests/              → Submit request (vacation/permission/reimbursement/document)
GET    /api/requests/{id}/         → Detail
PATCH  /api/requests/{id}/         → Edit — owner only, while status=PENDING
POST   /api/requests/{id}/approve/ → Approve — Manager (direct reports) or Admin
POST   /api/requests/{id}/reject/  → Reject — Manager (direct reports) or Admin
```

### Approvals
```
GET /api/approvals/        → List all approval records — Manager or Admin
GET /api/approvals/{id}/   → Detail
```

### Documents
```
GET    /api/documents/         → List (employees see own; managers see all)
POST   /api/documents/         → Upload — Manager or Admin
GET    /api/documents/{id}/    → Detail
DELETE /api/documents/{id}/    → Delete — Manager or Admin
```

### Notifications
```
GET   /api/notifications/            → My notifications
PATCH /api/notifications/{id}/       → Mark as read
POST  /api/notifications/read_all/   → Mark all as read
```

### Reports
```
GET /api/reports/requests/         → Stats by status + type (JSON) — Manager or Admin
GET /api/reports/employees/        → Headcount by status + department (JSON) — Manager or Admin
GET /api/reports/requests/export/  → Full CSV download — Manager or Admin
```

---

## Celery Background Tasks

| Task | Schedule | Description |
|---|---|---|
| `remind_pending_requests` | Daily 09:00 UTC | Notifies managers about requests pending >48h |
| `mark_expired_requests` | Every hour | Auto-rejects vacation requests with past end dates |
| `generate_weekly_report` | Monday 08:00 UTC | Logs weekly request statistics |

---

## Running Tests

```bash
# Install dependencies (uses SQLite in-memory — no Docker needed)
pip install -r requirements/test.txt

# Run full suite with coverage
pytest tests/ -v --cov=apps --cov-report=term-missing

# Run specific module
pytest tests/test_requests.py -v

# Run with HTML report
pytest tests/ --cov=apps --cov-report=html
```

**Current results:** 59 tests · 90% coverage · 0.7s

---

## Project Structure

```
peopleops-workflow-api/
├── apps/
│   ├── accounts/
│   │   ├── management/commands/seed_demo.py   ← demo data command
│   │   ├── models.py                          ← CustomUser + Role
│   │   └── admin.py                           ← role badge, readonly timestamps
│   ├── employees/     filters, soft delete, manager hierarchy
│   ├── requests/      workflow, approve/reject via services.py, Celery tasks
│   ├── approvals/     read-only audit trail
│   ├── documents/     file upload, permission guards
│   ├── notifications/ auto-create on status change, bulk mark-read
│   └── reports/       aggregations, CSV export
├── config/
│   ├── settings/
│   │   ├── base.py          ← shared config, Celery Beat schedule
│   │   ├── development.py   ← DEBUG=True, django-extensions
│   │   ├── testing.py       ← SQLite in-memory, CELERY_TASK_ALWAYS_EAGER
│   │   └── production.py    ← HTTPS, HSTS, strict SECRET_KEY
│   ├── urls.py
│   └── celery.py
├── tests/
│   ├── conftest.py          ← shared fixtures
│   ├── test_auth.py
│   ├── test_employees.py
│   ├── test_requests.py     ← full approve/reject workflow
│   ├── test_approvals.py
│   ├── test_documents.py
│   ├── test_notifications.py
│   ├── test_reports.py
│   ├── test_services.py     ← RequestWorkflowService unit tests
│   └── test_tasks.py        ← Celery task tests
├── docs/
│   ├── postman_collection.json
│   └── images/
├── docker-compose.yml        ← 5 services
├── Dockerfile                ← python:3.11-slim + gunicorn
├── Makefile
├── ruff.toml
└── .github/workflows/ci.yml  ← lint + migration check + tests
```

---

## Makefile Commands

```bash
make up              # docker compose up -d
make down            # docker compose down
make logs            # follow api logs
make migrate         # run migrations
make test            # pytest (local)
make lint            # ruff check .
make shell           # django shell
make superuser       # create superuser
make schema          # generate openapi schema.yml
```

---

## Key Design Decisions

**Why AbstractBaseUser?** Email-first auth (no username). Gives full control over the authentication backend for potential SSO/OAuth extension.

**Why soft delete?** Employee data is referenced by requests, approvals and documents. Hard deletion would break referential integrity and audit trails.

**Why Celery Beat over cron?** Schedules are stored in the DB (django-celery-beat), making them inspectable and adjustable without redeployment.

**Why split serializers?** `CreateSerializer` / `UpdateSerializer` / `ReadSerializer` per resource prevents mass-assignment vulnerabilities and keeps validation logic explicit.

**Why CELERY_TASK_ALWAYS_EAGER in tests?** Tasks run synchronously in the test process — no broker needed, no test infrastructure overhead.

---

## Known Limitations & Next Improvements

This is a portfolio project built to demonstrate production-grade Django patterns. The following limitations are intentional trade-offs for scope, not oversights:

| Limitation | Reasoning / Next Step |
|---|---|
| **No frontend** | API-only by design. A React or Next.js frontend would be a separate project. |
| **Single-level approval** | Each request has one approver. Multi-step approval chains (e.g. manager → HR → finance) would require a workflow engine (e.g. Prefect, Temporal). |
| **File storage is local** | `MEDIA_ROOT` stores uploads on disk. Production deployments should use S3 or GCS via `django-storages`. |
| **No real email delivery** | Notifications are DB records. A production system would integrate SendGrid/SES via Django's email backend. |
| **No rate limiting** | API throttling (`DEFAULT_THROTTLE_CLASSES`) is not configured. DRF has built-in support that would be trivial to add. |
| **SQLite in CI only** | Tests run against SQLite for speed. A staging environment should run a real PostgreSQL instance. |
| **Single Celery queue** | All tasks share the default queue. A production setup would route heavy tasks (reports, emails) to a separate high-priority queue. |
