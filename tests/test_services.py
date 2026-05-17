"""
Unit tests for RequestWorkflowService.

Tests are split into:
  - can_review()        : pure predicate, no DB mutations
  - assert_can_review() : raises PermissionDenied on violation
  - assert_reviewable() : raises ValidationError on wrong status
  - approve()           : full happy-path + combined guard tests
  - reject()            : full happy-path + combined guard tests

All HTTP-level concerns (status codes) are covered in test_requests.py.
These tests operate directly on the service so business rules are verified
independently of the view layer.
"""
import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.approvals.models import Approval
from apps.notifications.models import Notification
from apps.requests.models import RequestStatus
from apps.requests.services import RequestWorkflowService

# ── can_review ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCanReview:
    def test_admin_can_review_any_request(self, admin_user, sample_request):
        assert RequestWorkflowService.can_review(admin_user, sample_request) is True

    def test_manager_can_review_direct_report(self, manager_user, sample_request):
        # sample_request.employee is managed by manager_user (via sample_employee fixture)
        assert RequestWorkflowService.can_review(manager_user, sample_request) is True

    def test_employee_cannot_self_review(self, employee_user, sample_request):
        assert RequestWorkflowService.can_review(employee_user, sample_request) is False

    def test_admin_cannot_self_review(self, admin_user):
        from apps.requests.models import InternalRequest, RequestType
        own_request = InternalRequest.objects.create(
            employee=admin_user,
            request_type=RequestType.PERMISSION,
            title="Admin own request",
            description="test",
        )
        assert RequestWorkflowService.can_review(admin_user, own_request) is False

    def test_manager_cannot_review_non_report(self, manager_user, sample_request):
        from apps.employees.models import Employee
        Employee.objects.filter(user=sample_request.employee).update(manager=None)
        assert RequestWorkflowService.can_review(manager_user, sample_request) is False


# ── assert_can_review ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAssertCanReview:
    def test_raises_for_self_approval(self, employee_user, sample_request):
        with pytest.raises(PermissionDenied, match="cannot approve or reject their own"):
            RequestWorkflowService.assert_can_review(employee_user, sample_request)

    def test_raises_for_manager_without_reporting_line(self, manager_user, sample_request):
        from apps.employees.models import Employee
        Employee.objects.filter(user=sample_request.employee).update(manager=None)
        with pytest.raises(PermissionDenied, match="direct active reports"):
            RequestWorkflowService.assert_can_review(manager_user, sample_request)

    def test_does_not_raise_for_admin(self, admin_user, sample_request):
        # Should not raise
        RequestWorkflowService.assert_can_review(admin_user, sample_request)

    def test_does_not_raise_for_direct_manager(self, manager_user, sample_request):
        RequestWorkflowService.assert_can_review(manager_user, sample_request)


# ── assert_reviewable ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAssertReviewable:
    def test_pending_is_reviewable(self, sample_request):
        # Should not raise — default status is pending
        RequestWorkflowService.assert_reviewable(sample_request)

    def test_already_approved_is_not_reviewable(self, admin_user, sample_request):
        sample_request.status = RequestStatus.APPROVED
        sample_request.save()
        with pytest.raises(ValidationError, match="approve"):
            RequestWorkflowService.assert_reviewable(sample_request, "approve")

    def test_already_rejected_is_not_reviewable(self, sample_request):
        sample_request.status = RequestStatus.REJECTED
        sample_request.save()
        with pytest.raises(ValidationError):
            RequestWorkflowService.assert_reviewable(sample_request, "reject")


# ── approve ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestApprove:
    def test_sets_status_approved(self, admin_user, sample_request):
        RequestWorkflowService.approve(sample_request, admin_user, comment="LGTM")
        sample_request.refresh_from_db()
        assert sample_request.status == RequestStatus.APPROVED

    def test_creates_approval_record(self, admin_user, sample_request):
        RequestWorkflowService.approve(sample_request, admin_user, comment="Looks good")
        approval = Approval.objects.get(request=sample_request)
        assert approval.decision == "approved"
        assert approval.comment == "Looks good"
        assert approval.approver == admin_user

    def test_notifies_employee(self, admin_user, employee_user, sample_request):
        RequestWorkflowService.approve(sample_request, admin_user)
        notification = Notification.objects.get(recipient=employee_user, related_request=sample_request)
        assert "approved" in notification.message.lower()

    def test_default_comment_is_empty_string(self, admin_user, sample_request):
        RequestWorkflowService.approve(sample_request, admin_user)
        assert Approval.objects.get(request=sample_request).comment == ""

    def test_rejects_self_approval(self, employee_user, sample_request):
        with pytest.raises(PermissionDenied):
            RequestWorkflowService.approve(sample_request, employee_user)

    def test_rejects_already_approved(self, admin_user, sample_request):
        RequestWorkflowService.approve(sample_request, admin_user)
        with pytest.raises(ValidationError):
            RequestWorkflowService.approve(sample_request, admin_user)


# ── reject ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReject:
    def test_sets_status_rejected(self, admin_user, sample_request):
        RequestWorkflowService.reject(sample_request, admin_user, comment="Missing docs")
        sample_request.refresh_from_db()
        assert sample_request.status == RequestStatus.REJECTED

    def test_creates_approval_record(self, admin_user, sample_request):
        RequestWorkflowService.reject(sample_request, admin_user, comment="No budget")
        approval = Approval.objects.get(request=sample_request)
        assert approval.decision == "rejected"
        assert approval.approver == admin_user

    def test_notifies_employee(self, admin_user, employee_user, sample_request):
        RequestWorkflowService.reject(sample_request, admin_user)
        notification = Notification.objects.get(recipient=employee_user, related_request=sample_request)
        assert "rejected" in notification.message.lower()

    def test_rejects_self_rejection(self, employee_user, sample_request):
        with pytest.raises(PermissionDenied):
            RequestWorkflowService.reject(sample_request, employee_user)

    def test_rejects_already_rejected(self, admin_user, sample_request):
        RequestWorkflowService.reject(sample_request, admin_user)
        with pytest.raises(ValidationError):
            RequestWorkflowService.reject(sample_request, admin_user)
