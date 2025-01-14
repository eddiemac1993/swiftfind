from django import forms
from .models import Review
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

from django import forms
from .models import Business

class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'category', 'description', 'address', 'phone_number', 'email', 'website', 'logo', 'latitude', 'longitude']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website:  # Only validate if a website is provided
            if not website.startswith(('http://', 'https://', 'www.')):
                # Prepend 'http://' if the URL starts with 'www.'
                if website.startswith('www.'):
                    website = 'http://' + website
                else:
                    raise ValidationError("Enter a valid URL (e.g., http://example.com or www.example.com).")

            # Validate the URL using Django's URLValidator
            validator = URLValidator()
            try:
                validator(website)
            except ValidationError:
                raise ValidationError("Enter a valid URL.")

        return website