"""
Request workflow service layer.

Centralises the approve/reject business logic so it can be reused by
views, admin actions, Celery tasks and tests without duplicating the
transaction + approval-record + notification dance.
"""
from django.db import transaction

from apps.approvals.models import Approval, ApprovalDecision
from apps.notifications.models import Notification, NotificationType

from .models import InternalRequest, RequestStatus


class RequestWorkflowService:
    """
    Encapsulates the approve/reject workflow for InternalRequests.

    Each method runs inside an atomic transaction to guarantee that the
    status change, the Approval record and the Notification are written
    together or not at all.
    """

    @staticmethod
    @transaction.atomic
    def approve(
        internal_request: InternalRequest,
        approver,
        comment: str = "",
    ) -> InternalRequest:
        """
        Approve *internal_request* on behalf of *approver*.

        - Sets status → APPROVED
        - Creates an Approval record with decision=APPROVED
        - Notifies the request owner
        """
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

        - Sets status → REJECTED
        - Creates an Approval record with decision=REJECTED
        - Notifies the request owner
        """
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
