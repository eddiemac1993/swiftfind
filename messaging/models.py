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
        """
        Returns business name if current user is a customer,
        or username if current user is the business owner
        """
        if current_user == self.business.owner:
            # For business owner, show the other participant's username
            other_participant = self.participants.exclude(id=current_user.id).first()
            return other_participant.username if other_participant else "Unknown User"
        else:
            # For regular users, show the business name
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