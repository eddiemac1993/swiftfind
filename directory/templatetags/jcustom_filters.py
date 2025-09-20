from django import template

register = template.Library()

@register.filter(name='dividedby')
def dividedby(value, arg):
    try:
        return int(value) // int(arg)
    except (ValueError, ZeroDivisionError):
        return 0