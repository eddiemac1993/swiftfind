# messaging/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from directory.models import Business

User = get_user_model()

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id}"

    def get_unread_count(self, user):
        return self.messages.filter(read=False).exclude(sender=user).count()

    def get_display_name(self, current_user):
        if current_user == self.business.owner:
            other_participant = self.participants.exclude(id=current_user.id).first()
            return other_participant.username if other_participant else "Unknown User"
        else:
            return self.business.name

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if this is a new message
        super().save(*args, **kwargs)
        
        if is_new:
            self.create_notifications()
            self.send_email_notifications()

    def create_notifications(self):
        """Create notifications for all participants except sender"""
        recipients = self.conversation.participants.exclude(id=self.sender.id)
        notifications = [
            Notification(
                user=user,
                message=self,
                notification_type='message'
            )
            for user in recipients
        ]
        Notification.objects.bulk_create(notifications)

    def send_email_notifications(self):
        """Send email notifications to participants"""
        recipients = self.conversation.participants.exclude(id=self.sender.id)
        site_url = settings.SITE_URL
        
        for user in recipients:
            # Check if user has email and profile exists
            if not user.email:
                continue
                
            # Safely check email preferences - default to True if profile doesn't exist
            receive_emails = True
            if hasattr(user, 'profile'):
                receive_emails = getattr(user.profile, 'receive_message_emails', True)
            
            if receive_emails:
                context = {
                    'sender': self.sender,
                    'receiver': user,
                    'message': self.content,
                    'business': self.conversation.business,
                    'conversation_url': site_url + reverse('messaging:conversation_detail', args=[self.conversation.id]),
                    'site_name': settings.SITE_NAME
                }
                
                subject = f"New message from {self.sender.username} regarding {self.conversation.business.name}"
                text_message = render_to_string('messaging/email/new_message.txt', context)
                html_message = render_to_string('messaging/email/new_message.html', context)
                
                send_mail(
                    subject,
                    text_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message,
                    fail_silently=True,
                )

    def mark_as_read(self, user):
        if not self.read and self.sender != user:
            self.read = True
            self.save()
            # Mark corresponding notification as read
            Notification.objects.filter(message=self, user=user).update(is_read=True)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=20, default='message')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username} about message {self.message.id}"