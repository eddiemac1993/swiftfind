# signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Comment

@receiver(pre_save, sender=Comment)
def set_anonymous_author(sender, instance, **kwargs):
    if not instance.user:
        instance.user = None  # Explicitly set to None if you want to track as anonymous