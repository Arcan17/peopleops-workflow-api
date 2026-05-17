"""
Request workflow service layer.

All approve/reject business rules live here — status validation, permission
checks, atomic persistence and notification dispatch.  Views, admin actions
and Celery tasks all delegate to this layer so the rules are enforced
consistently regardless of the entry point.
"""
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.approvals.models import Approval, ApprovalDecision
from apps.notifications.models import Notification, NotificationType

from .models import InternalRequest, RequestStatus

# Statuses that can still be acted upon
REVIEWABLE_STATUSES = frozenset({RequestStatus.PENDING, RequestStatus.IN_REVIEW})


class RequestWorkflowService:
    """
    Encapsulates approve/reject workflow for InternalRequests.

    Business rules enforced here (not in the view layer):
    - Only PENDING / IN_REVIEW requests may be approved or rejected.
    - An employee cannot approve or reject their own request.
    - A manager may only act on requests from their direct active reports.
    - An admin may act on any request.

    Every mutation runs inside @transaction.atomic to guarantee that the
    status change, Approval record and Notification are committed together.
    """

    # ── Permission checks ─────────────────────────────────────────────────────

    @staticmethod
    def can_review(approver, internal_request: InternalRequest) -> bool:
        """
        Return True if *approver* is allowed to approve or reject
        *internal_request*, without raising an exception.
        """
        from apps.employees.models import Employee, EmployeeStatus

        if internal_request.employee_id == approver.id:
            return False  # self-approval is never allowed
        if approver.is_admin:
            return True   # admin can act on any request
        return Employee.objects.filter(
            user=internal_request.employee,
            manager=approver,
            status=EmployeeStatus.ACTIVE,
        ).exists()

    @staticmethod
    def assert_can_review(approver, internal_request: InternalRequest) -> None:
        """Raise PermissionDenied if *approver* cannot act on *internal_request*."""
        from apps.employees.models import Employee, EmployeeStatus

        if internal_request.employee_id == approver.id:
            raise PermissionDenied(
                "An employee cannot approve or reject their own request."
            )
        if approver.is_admin:
            return
        is_direct_report = Employee.objects.filter(
            user=internal_request.employee,
            manager=approver,
            status=EmployeeStatus.ACTIVE,
        ).exists()
        if not is_direct_report:
            raise PermissionDenied(
                "You can only approve or reject requests from your direct active reports."
            )

    @staticmethod
    def assert_reviewable(internal_request: InternalRequest, action: str = "approve") -> None:
        """Raise ValidationError if *internal_request* is not in a reviewable status."""
        if internal_request.status not in REVIEWABLE_STATUSES:
            raise ValidationError(
                {
                    "detail": (
                        f"Only pending or in-review requests can be {action}d. "
                        f"Current status: «{internal_request.get_status_display()}»."
                    )
                }
            )

    # ── Workflow mutations ────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def approve(
        internal_request: InternalRequest,
        approver,
        comment: str = "",
    ) -> InternalRequest:
        """
        Approve *internal_request* on behalf of *approver*.

        Validates permissions and status before writing anything.
        Atomically: sets status → APPROVED, creates Approval record,
        and notifies the request owner.
        """
        RequestWorkflowService.assert_can_review(approver, internal_request)
        RequestWorkflowService.assert_reviewable(internal_request, "approve")

        internal_request.status = RequestStatus.APPROVED
        internal_request.save(update_fields=["status", "updated_at"])
        Approval.objects.create(
            request=internal_request,
            approver=approver,
            decision=ApprovalDecision.APPROVED,
            comment=comment,
        )
        Notification.objects.create(
            recipient=internal_request.employee,
            message=f'Your request "{internal_request.title}" has been approved.',
            notification_type=NotificationType.REQUEST_APPROVED,
            related_request=internal_request,
        )
        return internal_request

    @staticmethod
    @transaction.atomic
    def reject(
        internal_request: InternalRequest,
        approver,
        comment: str = "",
    ) -> InternalRequest:
        """
        Reject *internal_request* on behalf of *approver*.

        Validates permissions and status before writing anything.
        Atomically: sets status → REJECTED, creates Approval record,
        and notifies the request owner.
        """
        RequestWorkflowService.assert_can_review(approver, internal_request)
        RequestWorkflowService.assert_reviewable(internal_request, "reject")

        internal_request.status = RequestStatus.REJECTED
        internal_request.save(update_fields=["status", "updated_at"])
        Approval.objects.create(
            request=internal_request,
            approver=approver,
            decision=ApprovalDecision.REJECTED,
            comment=comment,
        )
        Notification.objects.create(
            recipient=internal_request.employee,
            message=f'Your request "{internal_request.title}" has been rejected.',
            notification_type=NotificationType.REQUEST_REJECTED,
            related_request=internal_request,
        )
        return internal_request
