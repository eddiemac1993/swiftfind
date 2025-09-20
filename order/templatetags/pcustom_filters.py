from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument and rounds it to the nearest whole number."""
    try:
        return round(float(value) * float(arg))
    except (ValueError, TypeError):
        return None

@register.filter
def div(value, arg):
    """Divides the value by the argument safely."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return None
