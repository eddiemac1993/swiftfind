from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import mail_admins, send_mail
from django.urls import reverse
from django.contrib.sites.models import Site
from django_user_agents.utils import get_user_agent
from .models import UserProfile, Referral, Business

User = get_user_model()

@receiver(post_save, sender=User)
def handle_user_creation(sender, instance, created, **kwargs):
    """
    Handles user creation tasks including:
    - Profile creation
    - Referral processing
    - Admin notifications
    """
    request = kwargs.get('request')
    
    # 1. Handle profile creation
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    
    # 2. Process referral if exists
    if hasattr(instance, '_referrer'):
        profile.referred_by = instance._referrer
        profile.save()
        
        Referral.objects.create(
            referrer=instance._referrer,
            referred_user=instance,
        )
        del instance._referrer
    
    # 3. Send notifications for new users
    if created:
        send_user_signup_notification(instance, request)

def send_user_signup_notification(user, request=None):
    """Helper function to send user signup notifications"""
    # Basic notification
    mail_admins(
        subject=f"New User Signup: {user.username}",
        message=f"New user registered:\n\nUsername: {user.username}\nEmail: {user.email}",
        html_message=f"""
        <h3>New User Registration</h3>
        <p>Username: {user.username}</p>
        <p>Email: {user.email}</p>
        """
    )
    
    # Detailed notification with device info if available
    device_info = get_device_info(request) if request else "Device info unavailable"
    
    mail_admins(
        subject=f"[Detailed] New Signup: {user.username}",
        message=f"""
        New user registered:
        Username: {user.username}
        Email: {user.email}
        Date: {user.date_joined}
        ---
        {device_info}
        """,
        html_message=f"""
        <h3>New User Details</h3>
        <p><strong>Username:</strong> {user.username}</p>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Joined:</strong> {user.date_joined}</p>
        <hr>
        <h4>Device Info</h4>
        <pre>{device_info}</pre>
        """
    )

def get_device_info(request):
    """Extracts device information from request"""
    user_agent = get_user_agent(request)
    return f"""
    Device: {user_agent.device.family} ({user_agent.device.brand or 'Unknown'})
    OS: {user_agent.os.family} {user_agent.os.version_string}
    Browser: {user_agent.browser.family} {user_agent.browser.version_string}
    Is Mobile: {user_agent.is_mobile}
    Is Tablet: {user_agent.is_tablet}
    Is Bot: {user_agent.is_bot}
    IP Address: {request.META.get('REMOTE_ADDR', 'Unknown')}
    """

@receiver(post_save, sender=Business)
def handle_business_creation(sender, instance, created, **kwargs):
    """
    Handles business creation tasks including:
    - Admin notifications
    - Welcome email to business owner
    """
    if created:
        send_business_creation_notification(instance)
        send_business_welcome_email(instance)

def send_business_creation_notification(business):
    """Sends notification to admins about new business"""
    current_site = Site.objects.get_current()
    admin_url = f"https://{current_site.domain}{reverse('admin:directory_business_change', args=[business.id])}"
    
    mail_admins(
        subject=f"New Business Added: {business.name}",
        message=f"""
        A new business has been added:
        
        Name: {business.name}
        Owner: {business.owner.username} ({business.owner.email})
        Category: {business.category.name if business.category else 'None'}
        Address: {business.address}
        Phone: {business.phone_number}
        Status: {'Verified' if business.is_verified else 'Pending verification'}
        
        Admin URL: {admin_url}
        """,
        html_message=f"""
        <h3>New Business Added</h3>
        <p><strong>Name:</strong> {business.name}</p>
        <p><strong>Owner:</strong> {business.owner.username} ({business.owner.email})</p>
        <p><strong>Category:</strong> {business.category.name if business.category else 'None'}</p>
        <p><strong>Address:</strong> {business.address}</p>
        <p><strong>Phone:</strong> {business.phone_number}</p>
        <p><strong>Status:</strong> {'Verified' if business.is_verified else 'Pending verification'}</p>
        <hr>
        <p><a href="{admin_url}">Manage in Admin</a></p>
        """
    )

def send_business_welcome_email(business):
    """Sends welcome email to business owner"""
    subject = f"Welcome to Our Platform - {business.name}"
    
    send_mail(
        subject=subject,
        message=f"""
        Dear {business.owner.username},
        
        Thank you for adding your business "{business.name}" to our platform!
        
        Here are your next steps:
        1. Complete your business profile
        2. Add your products/services
        3. Verify your contact information
        
        We're excited to have you on board!
        
        The Platform Team
        """,
        from_email='noreply@yourdomain.com',
        recipient_list=[business.owner.email],
        html_message=f"""
        <h2>Welcome to Our Platform!</h2>
        <p>Dear {business.owner.username},</p>
        
        <p>Thank you for adding your business <strong>{business.name}</strong> to our platform!</p>
        
        <h3>Next Steps:</h3>
        <ol>
            <li>Complete your business profile</li>
            <li>Add your products/services</li>
            <li>Verify your contact information</li>
        </ol>
        
        <p>We're excited to have you on board!</p>
        
        <p>The Platform Team</p>
        """
    )