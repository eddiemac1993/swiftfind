from django import forms
from .models import Review
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Business
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Business

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'phone_number', 'address', 'bio']

class BusinessUpdateForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['logo', 'name', 'email', 'city', 'phone_number', 'category', 'description']

class UserRegistrationForm(UserCreationForm):
    business_name = forms.CharField(max_length=200, required=True)
    business_address = forms.CharField(max_length=255, required=True)
    business_phone_number = forms.CharField(max_length=15, required=True)
    business_email = forms.EmailField(required=True)
    business_website = forms.URLField(required=False)
    business_city = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'business_name', 'business_address', 'business_phone_number', 'business_email', 'business_website', 'business_city']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            business = Business.objects.create(
                name=self.cleaned_data['business_name'],
                address=self.cleaned_data['business_address'],
                phone_number=self.cleaned_data['business_phone_number'],
                email=self.cleaned_data['business_email'],
                website=self.cleaned_data.get('business_website', ''),
                city=self.cleaned_data['business_city'],
                owner=user
            )
            UserProfile.objects.get_or_create(user=user, defaults={'business': business})
        return user

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

from django import forms
from .models import UserProfile, Business

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'phone_number', 'address', 'bio']

class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['logo', 'name','address', 'email', 'city', 'phone_number', 'category', 'description']

from django import forms
from .models import BusinessImage

class BusinessImageForm(forms.ModelForm):
    class Meta:
        model = BusinessImage
        fields = ['image', 'caption']