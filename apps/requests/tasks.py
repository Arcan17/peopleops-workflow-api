from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

logger = get_task_logger(__name__)


@shared_task(name="requests.remind_pending_requests")
def remind_pending_requests():
    """
    Notify managers about requests that have been PENDING for more than 48 hours.
    Runs every 24 hours via Celery Beat.
    """
    from apps.notifications.models import Notification
    from apps.requests.models import InternalRequest, RequestStatus

    cutoff = timezone.now() - timedelta(hours=48)
    stale = InternalRequest.objects.filter(
        status=RequestStatus.PENDING,
        created_at__lte=cutoff,
    ).select_related("employee")

    count = stale.count()
    if count == 0:
        logger.info("remind_pending_requests: no stale requests found")
        return "No stale requests"

    # Import here to avoid circular imports at module level
    from apps.accounts.models import CustomUser, Role

    managers = CustomUser.objects.filter(role__in=[Role.ADMIN, Role.MANAGER], is_active=True)

    notifications = []
    for request in stale:
        for manager in managers:
            notifications.append(
                Notification(
                    recipient=manager,
                    message=(
                        f'Request "{request.title}" by {request.employee.full_name} '
                        f"has been pending for more than 48 hours."
                    ),
                    notification_type="pending_reminder",
                    related_request=request,
                )
            )

    Notification.objects.bulk_create(notifications)
    logger.info("remind_pending_requests: sent %d reminder notifications", len(notifications))
    return f"Sent {len(notifications)} reminders for {count} stale requests"


@shared_task(name="requests.mark_expired_requests")
def mark_expired_requests():
    """
    Auto-reject vacation requests whose end_date is in the past and are still pending/in_review.
    Runs every hour via Celery Beat.
    """
    from apps.notifications.models import Notification
    from apps.requests.models import InternalRequest, RequestStatus, RequestType

    today = timezone.now().date()
    expired = InternalRequest.objects.filter(
        request_type=RequestType.VACATION,
        status__in=[RequestStatus.PENDING, RequestStatus.IN_REVIEW],
        end_date__lt=today,
    ).select_related("employee")

    count = expired.count()
    if count == 0:
        logger.info("mark_expired_requests: nothing to expire")
        return "Nothing expired"

    notifications = []
    for request in expired:
        request.status = RequestStatus.REJECTED
        notifications.append(
            Notification(
                recipient=request.employee,
                message=(
                    f'Your vacation request "{request.title}" was automatically '
                    f"rejected because the requested dates have already passed."
                ),
                notification_type="request_rejected",
                related_request=request,
            )
        )

    InternalRequest.objects.bulk_update(expired, ["status"])
    Notification.objects.bulk_create(notifications)
    logger.info("mark_expired_requests: expired %d requests", count)
    return f"Expired {count} vacation requests"


@shared_task(name="requests.generate_weekly_report")
def generate_weekly_report():
    """
    Generate a weekly summary of request statistics and log it.
    Runs every Monday at 08:00 via Celery Beat.
    """
    from apps.requests.models import InternalRequest, RequestStatus

    one_week_ago = timezone.now() - timedelta(days=7)
    requests_this_week = InternalRequest.objects.filter(created_at__gte=one_week_ago)

    total = requests_this_week.count()
    by_status = {
        status: requests_this_week.filter(status=status).count()
        for status, _ in RequestStatus.choices
    }

    summary = {
        "period": f"{one_week_ago.date()} to {timezone.now().date()}",
        "total_requests": total,
        "by_status": by_status,
    }
    logger.info("Weekly report: %s", summary)
    return summary
