# In your pos_system/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the arg"""
    try:
        return value * arg
    except (ValueError, TypeError):
        return 0