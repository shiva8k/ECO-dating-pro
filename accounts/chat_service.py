from django.utils import timezone

from .models import ChatMessage, ChatRoom, Notification


def save_chat_message(room, sender, content):
    content = (content or "").strip()
    if not content or len(content) > 1000:
        return None

    chat_message = ChatMessage.objects.create(room=room, sender=sender, content=content)
    recipient = room.other_user(sender)
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=Notification.MESSAGE,
        title="New message",
        message=f"{sender.username}: {content[:80]}",
        link=room.get_absolute_url(),
    )
    return chat_message


def serialize_chat_message(message):
    return {
        "id": message.id,
        "message": message.content,
        "sender": message.sender.username,
        "timestamp": timezone.localtime(message.created_at).strftime("%b %d, %I:%M %p"),
    }
