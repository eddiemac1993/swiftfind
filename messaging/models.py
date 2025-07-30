# messaging/models.py
from django.db import models
from django.contrib.auth import get_user_model
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