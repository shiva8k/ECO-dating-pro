from django.urls import reverse
from django.utils import timezone

from .models import Notification, Profile


def _sender_avatar_url(notification):
    if not notification.sender_id:
        return None
    try:
        profile = notification.sender.profile
    except Profile.DoesNotExist:
        return None
    if profile.profile_picture:
        return profile.profile_picture.url
    return None


def serialize_notification(notification):
    return {
        "id": notification.id,
        "notification_type": notification.notification_type,
        "title": notification.title,
        "message": notification.message,
        "link": notification.link or "",
        "is_read": notification.is_read,
        "timestamp": notification.timestamp.isoformat(),
        "sender_username": notification.sender.username if notification.sender_id else "",
        "avatar_url": _sender_avatar_url(notification),
    }


def notify_profile_view(viewer, profile_owner):
    if viewer.id == profile_owner.id:
        return None

    recent_cutoff = timezone.now() - timezone.timedelta(hours=24)
    already_notified = Notification.objects.filter(
        recipient=profile_owner,
        sender=viewer,
        notification_type=Notification.PROFILE_VIEW,
        timestamp__gte=recent_cutoff,
    ).exists()
    if already_notified:
        return None

    profile, _ = Profile.objects.get_or_create(user=profile_owner)
    return Notification.objects.create(
        recipient=profile_owner,
        sender=viewer,
        notification_type=Notification.PROFILE_VIEW,
        title="Profile viewed",
        message=f"{viewer.username} viewed your profile.",
        link=profile.get_absolute_url(),
    )


def notify_premium_activated(user, plan_name):
    return Notification.objects.create(
        recipient=user,
        sender=None,
        notification_type=Notification.PREMIUM,
        title="Premium activated",
        message=f"Your ECO Premium plan ({plan_name}) is now active.",
        link=reverse("payment_history"),
    )
