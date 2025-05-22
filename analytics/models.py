from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.sessions.models import Session

class PageVisit(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Authenticated User"
    )
    session = models.ForeignKey(
        Session, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Session"
    )
    path = models.CharField(max_length=255, verbose_name="Page URL")
    method = models.CharField(max_length=10, default='GET')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referrer = models.CharField(max_length=255, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Visit Time")
    is_authenticated = models.BooleanField(default=False, verbose_name="Logged In")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Page Visit'
        verbose_name_plural = 'Page Visits'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['path']),
            models.Index(fields=['user']),
            models.Index(fields=['session']),
            models.Index(fields=['is_authenticated']),
        ]
        
    def __str__(self):
        if self.user:
            return f"{self.user.username} visited {self.path}"
        elif self.session:
            return f"Anonymous (session {self.session.pk[:8]}) visited {self.path}"
        else:
            return f"Unknown visitor to {self.path}"