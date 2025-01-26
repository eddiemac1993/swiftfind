from django import template
from num2words import num2words

register = template.Library()

@register.filter
def amount_in_words(value):
    try:
        # Split the value into dollars and cents
        dollars = int(value)
        cents = round((value - dollars) * 100)

        # Convert dollars and cents to words
        dollar_words = num2words(dollars, lang='en').title()
        cent_words = num2words(cents, lang='en').title()

        if cents == 0:
            return f"{dollar_words} Kwacha Only"
        else:
            return f"{dollar_words} and {cent_words} Kwacha Only"
    except (ValueError, TypeError):
        return "Zero Only"