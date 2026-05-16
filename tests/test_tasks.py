"""
Tests for Celery tasks: remind_pending_requests, mark_expired_requests,
generate_weekly_report.

Settings use CELERY_TASK_ALWAYS_EAGER=True so tasks run synchronously.
"""
from datetime import date, timedelta

import pytest
from django.utils import timezone

from apps.notifications.models import Notification
from apps.requests.models import InternalRequest, RequestStatus, RequestType

# ── remind_pending_requests ───────────────────────────────────────────────────

@pytest.mark.django_db
def test_remind_pending_no_stale(manager_client, sample_request):
    """Task returns early when no requests are older than 48h."""
    from apps.requests.tasks import remind_pending_requests

    # sample_request was just created — not stale
    result = remind_pending_requests()
    assert result == "No stale requests"
    assert Notification.objects.filter(notification_type="pending_reminder").count() == 0


@pytest.mark.django_db
def test_remind_pending_sends_notifications(manager_user, employee_user, sample_request):
    """Stale pending requests trigger notifications to managers/admins."""
    from apps.requests.tasks import remind_pending_requests

    # Back-date the request to 3 days ago so it's stale
    InternalRequest.objects.filter(pk=sample_request.pk).update(
        created_at=timezone.now() - timedelta(hours=73)
    )

    result = remind_pending_requests()

    # At least one notification was created (for manager_user)
    notifications = Notification.objects.filter(notification_type="pending_reminder")
    assert notifications.exists()
    assert "has been pending" in notifications.first().message
    assert "1 stale" in result or "stale requests" in result


# ── mark_expired_requests ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_mark_expired_nothing_to_expire(sample_request):
    """Task returns early when no expired vacation requests exist."""
    from apps.requests.tasks import mark_expired_requests

    # sample_request is not a vacation type with a past end_date
    result = mark_expired_requests()
    assert result == "Nothing expired"


@pytest.mark.django_db
def test_mark_expired_rejects_old_vacations(employee_user):
    """Vacation requests with past end_date get auto-rejected."""
    from apps.requests.tasks import mark_expired_requests

    past_vacation = InternalRequest.objects.create(
        employee=employee_user,
        request_type=RequestType.VACATION,
        status=RequestStatus.PENDING,
        title="Old summer vacation",
        description="Should be expired",
        start_date=date.today() - timedelta(days=10),
        end_date=date.today() - timedelta(days=3),
    )

    result = mark_expired_requests()

    past_vacation.refresh_from_db()
    assert past_vacation.status == RequestStatus.REJECTED
    assert "1" in result

    notification = Notification.objects.filter(
        recipient=employee_user,
        notification_type="request_rejected",
        related_request=past_vacation,
    ).first()
    assert notification is not None
    assert "automatically" in notification.message


@pytest.mark.django_db
def test_mark_expired_skips_approved_vacations(employee_user):
    """Already-approved vacations are not re-rejected even if dates passed."""
    from apps.requests.tasks import mark_expired_requests

    approved_vacation = InternalRequest.objects.create(
        employee=employee_user,
        request_type=RequestType.VACATION,
        status=RequestStatus.APPROVED,
        title="Approved old vacation",
        description="Already approved",
        start_date=date.today() - timedelta(days=10),
        end_date=date.today() - timedelta(days=3),
    )

    mark_expired_requests()

    approved_vacation.refresh_from_db()
    assert approved_vacation.status == RequestStatus.APPROVED  # unchanged


# ── generate_weekly_report ────────────────────────────────────────────────────

@pytest.mark.django_db
def test_generate_weekly_report_structure(sample_request):
    """Weekly report returns a dict with period, total, and by_status keys."""
    from apps.requests.tasks import generate_weekly_report

    result = generate_weekly_report()

    assert isinstance(result, dict)
    assert "period" in result
    assert "total_requests" in result
    assert "by_status" in result
    assert result["total_requests"] >= 1  # sample_request was created this week

    # All statuses present in by_status
    for status, _ in RequestStatus.choices:
        assert status in result["by_status"]


@pytest.mark.django_db
def test_generate_weekly_report_excludes_old_requests(employee_user):
    """Requests older than 7 days are NOT counted in the weekly report."""
    from apps.requests.tasks import generate_weekly_report

    old_request = InternalRequest.objects.create(
        employee=employee_user,
        request_type=RequestType.PERMISSION,
        status=RequestStatus.PENDING,
        title="Ancient request",
        description="Too old for weekly report",
    )
    # Back-date it to 8 days ago
    InternalRequest.objects.filter(pk=old_request.pk).update(
        created_at=timezone.now() - timedelta(days=8)
    )

    result = generate_weekly_report()
    assert result["total_requests"] == 0
