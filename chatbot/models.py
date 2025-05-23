from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserQuery(models.Model):
    query = models.TextField()
    intent = models.CharField(max_length=50, blank=True, null=True)
    entities = models.JSONField(default=dict, blank=True)
    response = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"Query at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name_plural = "User Queries"
        ordering = ['-timestamp']