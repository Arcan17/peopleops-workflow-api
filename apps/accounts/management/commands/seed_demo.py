"""
Management command: seed_demo

Creates a realistic demo dataset for local development and portfolio showcasing.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --reset   # wipe existing data first
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed the database with demo data for development/portfolio purposes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing demo data before seeding",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()

        self.stdout.write(self.style.MIGRATE_HEADING("\n🌱  Seeding demo data...\n"))

        admin = self._create_admin()
        managers = self._create_managers(admin)
        employees = self._create_employees(managers)
        requests = self._create_requests(employees, managers)
        self._create_approvals(requests, managers)
        self._create_notifications(requests, employees)

        self.stdout.write(self.style.SUCCESS("\n✅  Demo data seeded successfully!\n"))
        self.stdout.write("─" * 50)
        self.stdout.write("  Admin:     admin@peopleops.com  / Admin1234!")
        self.stdout.write("  Manager:   carlos@peopleops.com / Manager1234!")
        self.stdout.write("  Employee:  ana@peopleops.com    / Employee1234!")
        self.stdout.write("─" * 50)
        self.stdout.write("  API docs:  http://localhost:8000/api/docs/")
        self.stdout.write("  Admin UI:  http://localhost:8000/admin/\n")

    def _reset(self):
        from apps.accounts.models import CustomUser
        from apps.employees.models import Employee
        from apps.notifications.models import Notification
        from apps.requests.models import InternalRequest

        self.stdout.write("🗑  Resetting demo data...")
        Notification.objects.all().delete()
        InternalRequest.objects.all().delete()
        Employee.objects.all().delete()
        CustomUser.objects.filter(is_superuser=False).delete()
        self.stdout.write("   Done.\n")

    # ── creators ─────────────────────────────────────────────────────────────

    def _create_admin(self):
        from apps.accounts.models import CustomUser, Role

        user, created = CustomUser.objects.get_or_create(
            email="admin@peopleops.com",
            defaults={
                "first_name": "Admin",
                "last_name": "PeopleOps",
                "role": Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password("Admin1234!")
            user.save()
            self.stdout.write(f"  ✓ Admin created: {user.email}")
        else:
            self.stdout.write(f"  · Admin already exists: {user.email}")
        return user

    def _create_managers(self, admin):
        from apps.accounts.models import CustomUser, Role
        from apps.employees.models import ContractType, Employee

        managers_data = [
            {
                "email": "carlos@peopleops.com",
                "first_name": "Carlos",
                "last_name": "Gonzalez",
                "position": "HR Manager",
                "department": "Human Resources",
                "hire_date": date(2020, 3, 15),
                "salary": Decimal("3500000"),
            },
            {
                "email": "sofia@peopleops.com",
                "first_name": "Sofia",
                "last_name": "Herrera",
                "position": "Engineering Manager",
                "department": "Engineering",
                "hire_date": date(2019, 7, 1),
                "salary": Decimal("4200000"),
            },
        ]

        managers = []
        for data in managers_data:
            user, created = CustomUser.objects.get_or_create(
                email=data["email"],
                defaults={
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "role": Role.MANAGER,
                },
            )
            if created:
                user.set_password("Manager1234!")
                user.save()

            Employee.objects.get_or_create(
                user=user,
                defaults={
                    "position": data["position"],
                    "department": data["department"],
                    "contract_type": ContractType.FULL_TIME,
                    "hire_date": data["hire_date"],
                    "base_salary": data["salary"],
                    "manager": admin,
                },
            )
            managers.append(user)
            self.stdout.write(f"  ✓ Manager: {user.email}")

        return managers

    def _create_employees(self, managers):
        from apps.accounts.models import CustomUser, Role
        from apps.employees.models import ContractType, Employee, EmployeeStatus

        employees_data = [
            {
                "email": "ana@peopleops.com",
                "first_name": "Ana",
                "last_name": "Martinez",
                "position": "Backend Developer",
                "department": "Engineering",
                "hire_date": date(2022, 1, 10),
                "salary": Decimal("2400000"),
                "manager_idx": 1,
                "status": EmployeeStatus.ACTIVE,
            },
            {
                "email": "pedro@peopleops.com",
                "first_name": "Pedro",
                "last_name": "Ramirez",
                "position": "Frontend Developer",
                "department": "Engineering",
                "hire_date": date(2021, 8, 20),
                "salary": Decimal("2200000"),
                "manager_idx": 1,
                "status": EmployeeStatus.ACTIVE,
            },
            {
                "email": "lucia@peopleops.com",
                "first_name": "Lucia",
                "last_name": "Torres",
                "position": "HR Analyst",
                "department": "Human Resources",
                "hire_date": date(2023, 3, 5),
                "salary": Decimal("1800000"),
                "manager_idx": 0,
                "status": EmployeeStatus.ACTIVE,
            },
            {
                "email": "miguel@peopleops.com",
                "first_name": "Miguel",
                "last_name": "Castro",
                "position": "DevOps Engineer",
                "department": "Engineering",
                "hire_date": date(2020, 11, 15),
                "salary": Decimal("2800000"),
                "manager_idx": 1,
                "status": EmployeeStatus.ON_LEAVE,
            },
            {
                "email": "valentina@peopleops.com",
                "first_name": "Valentina",
                "last_name": "Rojas",
                "position": "Product Manager",
                "department": "Product",
                "hire_date": date(2021, 4, 1),
                "salary": Decimal("3100000"),
                "manager_idx": 1,
                "status": EmployeeStatus.ACTIVE,
            },
        ]

        employees = []
        for data in employees_data:
            user, created = CustomUser.objects.get_or_create(
                email=data["email"],
                defaults={
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "role": Role.EMPLOYEE,
                },
            )
            if created:
                user.set_password("Employee1234!")
                user.save()

            Employee.objects.get_or_create(
                user=user,
                defaults={
                    "position": data["position"],
                    "department": data["department"],
                    "contract_type": ContractType.FULL_TIME,
                    "hire_date": data["hire_date"],
                    "base_salary": data["salary"],
                    "status": data["status"],
                    "manager": managers[data["manager_idx"]],
                },
            )
            employees.append(user)
            self.stdout.write(f"  ✓ Employee: {user.email}")

        return employees

    def _create_requests(self, employees, managers):
        from apps.requests.models import InternalRequest, RequestStatus, RequestType

        today = date.today()
        requests_data = [
            {
                "employee_idx": 0,  # Ana
                "request_type": RequestType.VACATION,
                "status": RequestStatus.APPROVED,
                "title": "Summer vacation 2026",
                "description": "Annual vacation leave for July.",
                "start_date": today + timedelta(days=30),
                "end_date": today + timedelta(days=44),
            },
            {
                "employee_idx": 1,  # Pedro
                "request_type": RequestType.VACATION,
                "status": RequestStatus.PENDING,
                "title": "Long weekend — June",
                "description": "Requesting 3 days off to attend a family event.",
                "start_date": today + timedelta(days=10),
                "end_date": today + timedelta(days=12),
            },
            {
                "employee_idx": 2,  # Lucia
                "request_type": RequestType.REIMBURSEMENT,
                "status": RequestStatus.APPROVED,
                "title": "Office supplies reimbursement",
                "description": "Reimbursement for keyboard, mouse and headset purchased for remote work.",
                "amount": Decimal("89000"),
            },
            {
                "employee_idx": 3,  # Miguel
                "request_type": RequestType.PERMISSION,
                "status": RequestStatus.IN_REVIEW,
                "title": "Medical appointment — Thursday morning",
                "description": "Need to leave early on Thursday for a specialist appointment.",
                "start_date": today + timedelta(days=3),
                "end_date": today + timedelta(days=3),
            },
            {
                "employee_idx": 4,  # Valentina
                "request_type": RequestType.DOCUMENT,
                "status": RequestStatus.PENDING,
                "title": "Employment certificate for bank loan",
                "description": "Need official employment certificate for mortgage application.",
            },
            {
                "employee_idx": 0,  # Ana
                "request_type": RequestType.PERSONAL_DATA,
                "status": RequestStatus.REJECTED,
                "title": "Update emergency contact info",
                "description": "Request to update emergency contact phone number in HR system.",
            },
            {
                "employee_idx": 1,  # Pedro
                "request_type": RequestType.REIMBURSEMENT,
                "status": RequestStatus.IN_REVIEW,
                "title": "Conference registration fee",
                "description": "PyCon Chile 2026 registration — $45.000 CLP.",
                "amount": Decimal("45000"),
            },
        ]

        requests = []
        for data in requests_data:
            employee = employees[data["employee_idx"]]
            req, created = InternalRequest.objects.get_or_create(
                employee=employee,
                title=data["title"],
                defaults={
                    "request_type": data["request_type"],
                    "status": data["status"],
                    "description": data["description"],
                    "start_date": data.get("start_date"),
                    "end_date": data.get("end_date"),
                    "amount": data.get("amount"),
                },
            )
            requests.append(req)
            if created:
                self.stdout.write(f"  ✓ Request: [{data['request_type']}] {data['title'][:40]}")

        return requests

    def _create_approvals(self, requests, managers):
        from apps.approvals.models import Approval
        from apps.requests.models import RequestStatus

        approved = [r for r in requests if r.status == RequestStatus.APPROVED]
        rejected = [r for r in requests if r.status == RequestStatus.REJECTED]
        manager = managers[0]

        for req in approved:
            Approval.objects.get_or_create(
                request=req,
                defaults={
                    "approver": manager,
                    "decision": "approved",
                    "comment": "Looks good. Approved.",
                },
            )

        for req in rejected:
            Approval.objects.get_or_create(
                request=req,
                defaults={
                    "approver": manager,
                    "decision": "rejected",
                    "comment": "Missing required supporting documentation. Please resubmit.",
                },
            )

        self.stdout.write(
            f"  ✓ Approvals: {len(approved)} approved, {len(rejected)} rejected"
        )

    def _create_notifications(self, requests, employees):
        from apps.notifications.models import Notification, NotificationType
        from apps.requests.models import RequestStatus

        count = 0
        for req in requests:
            if req.status == RequestStatus.APPROVED:
                Notification.objects.get_or_create(
                    recipient=req.employee,
                    related_request=req,
                    notification_type=NotificationType.REQUEST_APPROVED,
                    defaults={
                        "message": f'Your request "{req.title}" has been approved.',
                        "is_read": True,
                    },
                )
                count += 1
            elif req.status == RequestStatus.REJECTED:
                Notification.objects.get_or_create(
                    recipient=req.employee,
                    related_request=req,
                    notification_type=NotificationType.REQUEST_REJECTED,
                    defaults={
                        "message": f'Your request "{req.title}" has been rejected.',
                        "is_read": False,
                    },
                )
                count += 1

        # A couple of unread pending reminders
        if employees:
            Notification.objects.get_or_create(
                recipient=employees[0],
                notification_type=NotificationType.GENERAL,
                message="Welcome to PeopleOps! Your profile is now active.",
                defaults={"is_read": False},
            )
            count += 1

        self.stdout.write(f"  ✓ Notifications: {count} created")
