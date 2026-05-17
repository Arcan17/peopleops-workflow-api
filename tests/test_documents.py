import datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from apps.accounts.models import CustomUser, Role
from apps.employees.models import Employee


@pytest.mark.django_db
class TestDocuments:
    URL = "/api/documents/"

    # ── Upload (create) ───────────────────────────────────────────────────────

    def test_manager_can_upload_for_direct_report(self, manager_client, sample_employee, sample_document_file):
        response = manager_client.post(
            self.URL,
            {
                "employee": sample_employee.id,
                "document_type": "contract",
                "title": "Signed contract",
                "file": sample_document_file,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["document_type"] == "contract"

    def test_manager_cannot_upload_for_other_team_employee(
        self, manager_client, sample_document_file, db
    ):
        """A manager cannot upload a document for an employee in another team."""
        other_manager = CustomUser.objects.create_user(
            email="other_mgr@example.com",
            password="pass",
            first_name="Other",
            last_name="Manager",
            role=Role.MANAGER,
        )
        other_employee_user = CustomUser.objects.create_user(
            email="other_emp@example.com",
            password="pass",
            first_name="Other",
            last_name="Employee",
            role=Role.EMPLOYEE,
        )
        other_employee = Employee.objects.create(
            user=other_employee_user,
            position="Designer",
            department="Design",
            hire_date=datetime.date(2023, 1, 1),
            manager=other_manager,
        )
        response = manager_client.post(
            self.URL,
            {
                "employee": other_employee.id,
                "document_type": "contract",
                "title": "Unauthorized upload",
                "file": sample_document_file,
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_upload_for_any_employee(self, admin_client, sample_employee, sample_document_file):
        response = admin_client.post(
            self.URL,
            {
                "employee": sample_employee.id,
                "document_type": "payslip",
                "title": "January payslip",
                "file": sample_document_file,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_employee_cannot_upload_document(self, employee_client, sample_employee, sample_document_file):
        response = employee_client.post(
            self.URL,
            {
                "employee": sample_employee.id,
                "document_type": "contract",
                "title": "Unauthorized upload",
                "file": sample_document_file,
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ── Visibility (queryset filtering) ──────────────────────────────────────

    def test_employee_sees_only_own_documents(self, employee_client, sample_employee, sample_document_file):
        from apps.documents.models import Document
        document = Document.objects.create(
            employee=sample_employee,
            document_type="contract",
            title="Private contract",
            file=sample_document_file,
            uploaded_by=sample_employee.manager,
        )
        response = employee_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == document.id

    def test_manager_sees_only_direct_reports_documents(
        self, manager_client, manager_user, sample_employee, sample_document_file, db
    ):
        """Manager should NOT see documents belonging to other teams."""
        from apps.documents.models import Document

        # Document for manager's direct report — should be visible
        own_doc = Document.objects.create(
            employee=sample_employee,
            document_type="contract",
            title="My report's contract",
            file=sample_document_file,
            uploaded_by=manager_user,
        )

        # Document for an unrelated employee — should NOT be visible
        other_manager = CustomUser.objects.create_user(
            email="other_mgr2@example.com", password="pass",
            first_name="X", last_name="Y", role=Role.MANAGER,
        )
        other_emp_user = CustomUser.objects.create_user(
            email="other_emp2@example.com", password="pass",
            first_name="A", last_name="B", role=Role.EMPLOYEE,
        )
        other_emp = Employee.objects.create(
            user=other_emp_user, position="QA", department="QA",
            hire_date=datetime.date(2023, 1, 1), manager=other_manager,
        )
        Document.objects.create(
            employee=other_emp,
            document_type="payslip",
            title="Other team payslip",
            file=SimpleUploadedFile("other.pdf", b"%PDF-1.4", content_type="application/pdf"),
            uploaded_by=other_manager,
        )

        response = manager_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert own_doc.id in ids
        assert len(ids) == 1  # only the direct report's document

    def test_admin_sees_all_documents(self, admin_client, sample_employee, sample_document_file, db):
        """Admins see documents from all teams."""
        from apps.documents.models import Document
        Document.objects.create(
            employee=sample_employee,
            document_type="contract",
            title="A contract",
            file=sample_document_file,
            uploaded_by=sample_employee.manager,
        )
        response = admin_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    # ── File validation ───────────────────────────────────────────────────────

    def test_invalid_mime_type_rejected(self, manager_client, sample_employee):
        bad_file = SimpleUploadedFile("malware.exe", b"MZ\x90\x00", content_type="application/octet-stream")
        response = manager_client.post(
            self.URL,
            {"employee": sample_employee.id, "document_type": "contract",
             "title": "Suspicious file", "file": bad_file},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported file type" in str(response.data)

    def test_oversized_file_rejected(self, manager_client, sample_employee):
        big_file = SimpleUploadedFile(
            "huge.pdf", b"A" * (11 * 1024 * 1024), content_type="application/pdf"
        )
        response = manager_client.post(
            self.URL,
            {"employee": sample_employee.id, "document_type": "payslip",
             "title": "Huge payslip", "file": big_file},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "limit" in str(response.data).lower()

    def test_png_file_accepted(self, manager_client, sample_employee):
        png_file = SimpleUploadedFile("id_card.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
        response = manager_client.post(
            self.URL,
            {"employee": sample_employee.id, "document_type": "personal",
             "title": "ID card scan", "file": png_file},
        )
        assert response.status_code == status.HTTP_201_CREATED
