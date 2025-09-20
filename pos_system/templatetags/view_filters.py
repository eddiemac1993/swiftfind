# Create a new file: pos_system/templatetags/view_filters.py
from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def format_duration(seconds):
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}m {seconds}s"