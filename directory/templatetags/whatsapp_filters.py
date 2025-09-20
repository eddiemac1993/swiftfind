from django import template

register = template.Library()

@register.filter
def whatsapp_number(value):
    # Remove all non-digit characters
    cleaned = ''.join(c for c in value if c.isdigit())
    
    # If number starts with country code, return as is
    if cleaned.startswith('260'):
        return cleaned
        
    # Otherwise, add country code (assuming local numbers start with 0)
    if cleaned.startswith('0'):
        return '260' + cleaned[1:]
        
    # Fallback - return cleaned as is
    return cleaned