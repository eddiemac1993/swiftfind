from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument and rounds it to the nearest whole number."""
    return round(float(value) * float(arg))