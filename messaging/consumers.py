# messaging/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Conversation, Message, Notification
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.user = self.scope["user"]
        
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
            
        if not await self.is_participant():
            await self.close()
            return
            
        self.room_group_name = f'chat_{self.conversation_id}'
        self.notification_group = f'user_{self.user.id}_notifications'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.channel_layer.group_add(
            self.notification_group,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.notification_group,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(data)

    async def handle_chat_message(self, data):
        message = data['message']
        message_obj, notifications = await self.save_message_and_notifications(message)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message_obj.id,
                'sender_id': str(self.user.id),
                'sender_username': self.user.username,
                'content': message_obj.content,
                'timestamp': message_obj.timestamp.isoformat(),
            }
        )
        
        for notification in notifications:
            await self.send_notification(notification)

    async def handle_read_receipt(self, data):
        message_id = data['message_id']
        await self.mark_message_as_read(message_id)
        
    async def send_notification(self, notification):
        await self.channel_layer.group_send(
            f'user_{notification.user.id}_notifications',
            {
                'type': 'notification',
                'notification_id': str(notification.id),
                'message_id': str(notification.message.id),
                'conversation_id': str(notification.message.conversation.id),
                'sender_id': str(notification.message.sender.id),
                'sender_username': notification.message.sender.username,
                'preview': notification.message.content[:50],
                'timestamp': notification.created_at.isoformat(),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            **event
        }))

    async def notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            **event
        }))

    @database_sync_to_async
    def is_participant(self):
        return Conversation.objects.filter(
            id=self.conversation_id,
            participants=self.user
        ).exists()

    @database_sync_to_async
    def save_message_and_notifications(self, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )
        
        participants = conversation.participants.exclude(id=self.user.id)
        notifications = [
            Notification.objects.create(
                user=participant,
                message=message
            )
            for participant in participants
        ]
        
        conversation.save()
        return message, notifications

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        message = Message.objects.get(id=message_id)
        message.mark_as_read(self.user)