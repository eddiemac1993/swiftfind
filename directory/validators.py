# In validators.py
from verify_email import verify_email
from django.core.exceptions import ValidationError

def validate_email_exists(email):
    """Check if the email address actually exists."""
    if not verify_email(email):
        raise ValidationError("This email address does not exist or cannot receive emails.")