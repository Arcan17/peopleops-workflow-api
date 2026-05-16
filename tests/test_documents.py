import pytest
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
