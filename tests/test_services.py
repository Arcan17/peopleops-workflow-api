"""
Unit tests for RequestWorkflowService.

The service is tested in isolation — no HTTP calls, no view layer.
These tests guarantee that the approve/reject logic works correctly
regardless of how it is invoked (view, admin action, Celery task, etc.).
"""
import pytest

from apps.approvals.models import Approval
from apps.notifications.models import Notification
from apps.requests.models import RequestStatus
from apps.requests.services import RequestWorkflowService


@pytest.mark.django_db
class TestRequestWorkflowServiceApprove:
    def test_approve_sets_status(self, admin_user, sample_request):
        RequestWorkflowService.approve(sample_request, admin_user, comment="LGTM")
        sample_request.refresh_from_db()
        assert sample_request.status == RequestStatus.APPROVED

    def test_approve_creates_approval_record(self, admin_user, sample_request):
        RequestWorkflowService.approve(sample_request, admin_user, comment="Looks good")
        approval = Approval.objects.get(request=sample_request)
        assert approval.decision == "approved"
        assert approval.comment == "Looks good"
        assert approval.approver == admin_user

    def test_approve_creates_notification_for_employee(self, admin_user, employee_user, sample_request):
        RequestWorkflowService.approve(sample_request, admin_user)
        notification = Notification.objects.get(
            recipient=employee_user,
            related_request=sample_request,
        )
        assert "approved" in notification.message.lower()
        assert sample_request.title in notification.message

    def test_approve_without_comment(self, admin_user, sample_request):
        """comment defaults to empty string — no validation error expected."""
        RequestWorkflowService.approve(sample_request, admin_user)
        approval = Approval.objects.get(request=sample_request)
        assert approval.comment == ""


@pytest.mark.django_db
class TestRequestWorkflowServiceReject:
    def test_reject_sets_status(self, admin_user, sample_request):
        RequestWorkflowService.reject(sample_request, admin_user, comment="Missing docs")
        sample_request.refresh_from_db()
        assert sample_request.status == RequestStatus.REJECTED

    def test_reject_creates_approval_record(self, admin_user, sample_request):
        RequestWorkflowService.reject(sample_request, admin_user, comment="Insufficient budget")
        approval = Approval.objects.get(request=sample_request)
        assert approval.decision == "rejected"
        assert approval.comment == "Insufficient budget"
        assert approval.approver == admin_user

    def test_reject_creates_notification_for_employee(self, admin_user, employee_user, sample_request):
        RequestWorkflowService.reject(sample_request, admin_user)
        notification = Notification.objects.get(
            recipient=employee_user,
            related_request=sample_request,
        )
        assert "rejected" in notification.message.lower()
        assert sample_request.title in notification.message

    def test_reject_without_comment(self, admin_user, sample_request):
        RequestWorkflowService.reject(sample_request, admin_user)
        approval = Approval.objects.get(request=sample_request)
        assert approval.comment == ""
