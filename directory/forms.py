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

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from urllib.parse import urlparse

class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'category', 'description', 'address', 'phone_number', 'email', 'website', 'logo', 'city']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


    def clean_website(self):
        website = self.cleaned_data.get('website')

        if website is None or website.strip() == "":  # Ensure website is not None before calling strip()
            return website  # Return None or empty string as-is

        website = website.strip()  # Trim whitespace

        # Normalize the URL
        if not website.startswith(('http://', 'https://')):
            website = 'http://' + website  # Prepend http:// if missing

        # Validate the URL using Django's URLValidator
        validator = URLValidator()
        try:
            validator(website)
        except ValidationError:
            raise ValidationError("Please enter a valid URL. Example: http://example.com or https://example.com")

        # Ensure the URL has a valid scheme and netloc
        parsed_url = urlparse(website)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValidationError("Please enter a complete URL including the scheme (http:// or https://).")

        return website


from django import forms
from .models import BusinessImage

class BusinessImageForm(forms.ModelForm):
    class Meta:
        model = BusinessImage
        fields = ['image', 'caption']