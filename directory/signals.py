from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
from django.core.mail import mail_admins
from django_user_agents.utils import get_user_agent

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=User)
def backup_signup_notification(sender, instance, created, **kwargs):
    if created:
        mail_admins(
            subject=f"New Signup: {instance.username}",
            message=f"New user registered:\n\nUsername: {instance.username}\nEmail: {instance.email}",
            html_message=f"""
            <h3>New User (Signal Backup)</h3>
            <p>Username: {instance.username}</p>
            <p>Email: {instance.email}</p>
            """
        )


@receiver(post_save, sender=User)
def notify_on_signup(sender, instance, created, **kwargs):
    if created:
        request = kwargs.get('request')  # Get request from signal

        if request:
            user_agent = get_user_agent(request)
            device_info = f"""
            Device: {user_agent.device.family} ({user_agent.device.brand or 'Unknown'})
            OS: {user_agent.os.family} {user_agent.os.version_string}
            Browser: {user_agent.browser.family} {user_agent.browser.version_string}
            Is Mobile: {user_agent.is_mobile}
            Is Tablet: {user_agent.is_tablet}
            Is Bot: {user_agent.is_bot}
            """
        else:
            device_info = "Device info unavailable (no request context)"

        mail_admins(
            subject=f"New Signup: {instance.username}",
            message=f"""
            New user registered:
            Username: {instance.username}
            Email: {instance.email}
            Date: {instance.date_joined}
            ---
            {device_info}
            """,
            html_message=f"""
            <h3>New User Registration</h3>
            <p><strong>Username:</strong> {instance.username}</p>
            <p><strong>Email:</strong> {instance.email}</p>
            <hr>
            <h4>Device Info</h4>
            <pre>{device_info}</pre>
            """
        )