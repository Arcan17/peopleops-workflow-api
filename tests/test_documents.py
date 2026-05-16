import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status


@pytest.mark.django_db
class TestDocuments:
    URL = "/api/documents/"

    def test_manager_can_upload_document(self, manager_client, sample_employee, sample_document_file):
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

    def test_employee_sees_only_own_documents(self, employee_client, manager_client, sample_employee, sample_document_file):
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

    def test_invalid_mime_type_rejected(self, manager_client, sample_employee):
        """Uploading an unsupported file type returns 400."""
        bad_file = SimpleUploadedFile(
            "malware.exe",
            b"MZ\x90\x00",
            content_type="application/octet-stream",
        )
        response = manager_client.post(
            self.URL,
            {
                "employee": sample_employee.id,
                "document_type": "contract",
                "title": "Suspicious file",
                "file": bad_file,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported file type" in str(response.data)

    def test_oversized_file_rejected(self, manager_client, sample_employee):
        """Files larger than 10 MB are rejected with 400."""
        big_file = SimpleUploadedFile(
            "huge.pdf",
            b"A" * (11 * 1024 * 1024),  # 11 MB
            content_type="application/pdf",
        )
        response = manager_client.post(
            self.URL,
            {
                "employee": sample_employee.id,
                "document_type": "payslip",
                "title": "Huge payslip",
                "file": big_file,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "limit" in str(response.data).lower()

    def test_png_file_accepted(self, manager_client, sample_employee):
        """PNG images are a valid document file type."""
        png_file = SimpleUploadedFile(
            "id_card.png",
            b"\x89PNG\r\n\x1a\n",  # PNG magic bytes
            content_type="image/png",
        )
        response = manager_client.post(
            self.URL,
            {
                "employee": sample_employee.id,
                "document_type": "personal",
                "title": "ID card scan",
                "file": png_file,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
