import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from .models import ChatMessage, ChatRoom, Notification


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        self.user = self.scope["user"]

        self.room = await self.get_room_for_user()
        if self.room is None:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "").strip()
        if not message:
            return

        chat_message = await self.save_message(message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": chat_message.content,
                "sender": self.user.username,
                "timestamp": timezone.localtime(chat_message.created_at).strftime("%b %d, %I:%M %p"),
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @sync_to_async
    def get_room_for_user(self):
        try:
            room = ChatRoom.objects.select_related("match__user_one", "match__user_two").get(id=self.room_id)
        except ChatRoom.DoesNotExist:
            return None

        if not room.has_member(self.user):
            return None
        return room

    @sync_to_async
    def save_message(self, message):
        chat_message = ChatMessage.objects.create(room=self.room, sender=self.user, content=message)
        recipient = self.room.other_user(self.user)
        Notification.objects.create(
            recipient=recipient,
            sender=self.user,
            notification_type=Notification.MESSAGE,
            title="New message",
            message=f"{self.user.username}: {message[:80]}",
            link=self.room.get_absolute_url(),
        )
        return chat_message
