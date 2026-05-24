from django.db import DatabaseError

from .models import Notification


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {
            "unread_notification_count": 0,
            "recent_notifications": [],
        }

    try:
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        recent_notifications = list(
            Notification.objects.filter(recipient=request.user).select_related("sender")[:5]
        )
    except DatabaseError:
        return {
            "unread_notification_count": 0,
            "recent_notifications": [],
        }

    return {
        "unread_notification_count": unread_count,
        "recent_notifications": recent_notifications,
    }
