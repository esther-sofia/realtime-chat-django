import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message
from .tasks import notify_new_message


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]                     # set by AuthMiddlewareStack
        if not self.user.is_authenticated:
            await self.close()                             # no login, no connection
            return

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        recent_messages = await self.get_recent_messages(self.room_name)
        for msg in recent_messages:
            await self.send(text_data=json.dumps({
                'message': msg['message'],
                'sender': msg['sender'],
            }))

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):              # only if connect got that far
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender = self.user.username                        # from the login, NOT from the browser

        await self.save_message(self.user, self.room_name, message)
        notify_new_message.delay(sender, self.room_name, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chat_message', 'message': message, 'sender': sender},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
        }))

    @database_sync_to_async
    def save_message(self, user, room_name, content):
        return Message.objects.create(sender=user, room_name=room_name, content=content)

    @database_sync_to_async
    def get_recent_messages(self, room_name):
        messages = Message.objects.filter(room_name=room_name).order_by('-timestamp')[:20]
        return [
            {'sender': msg.sender.username, 'message': msg.content}
            for msg in reversed(messages)
        ]