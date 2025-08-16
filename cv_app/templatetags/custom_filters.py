from django import template

register = template.Library()

@register.filter
def split_by_index(value, index):
    """
    Splits a string by '|' and returns the element at the index.
    """
    try:
        parts = value.split('|')
        return parts[int(index)]
    except (IndexError, ValueError, AttributeError):
        return ''
