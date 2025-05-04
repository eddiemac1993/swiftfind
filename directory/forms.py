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
from .models import Comment
from django import forms
from .models import BusinessPost
from django.core.validators import FileExtensionValidator

class BusinessPostForm(forms.ModelForm):
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-black-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100',
            'accept': 'image/*'
        }),
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        help_text="Upload an image (JPG, PNG, GIF). Max size: 2MB"
    )

    price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        model = BusinessPost
        fields = ['title', 'post_type', 'content', 'image', 'price', 'is_featured']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': 'Enter post title'
            }),
            'post_type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'content': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'rows': 4,
                'placeholder': 'Describe your product/service...'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-green-600 shadow-sm focus:border-green-500 focus:ring-green-500 dark:bg-gray-700 dark:border-gray-600',
            }),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 2 * 1024 * 1024:  # 2MB limit
                raise forms.ValidationError("Image size must be under 2MB.")
        return image

    # Removed the clean() method that required price for certain types
    # Now price is completely optional for all post types
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'phone_number', 'address', 'bio']

from django import forms
from ckeditor.widgets import CKEditorWidget
from django.core.validators import FileExtensionValidator

class BusinessUpdateForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget(), required=False)

    class Meta:
        model = Business
        fields = [
            'logo',
            'name',
            'email',
            'city',
            'phone_number',
            'category',
            'description',
            'company_profile'  # Add this field
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the company_profile field
        self.fields['company_profile'].widget.attrs.update({
            'accept': '.pdf',  # Only show PDF files in file selector
        })
        self.fields['company_profile'].required = False
        self.fields['company_profile'].help_text = "Upload a PDF file (max 5MB)"
        self.fields['company_profile'].validators = [
            FileExtensionValidator(allowed_extensions=['pdf'])
        ]

    def clean_company_profile(self):
        company_profile = self.cleaned_data.get('company_profile')
        if company_profile:
            # Check file size (5MB limit)
            if company_profile.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 5MB.")
        return company_profile

from django.core.exceptions import ValidationError
from urllib.parse import urlparse

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

    def clean_business_website(self):
        website = self.cleaned_data.get('business_website')

        # If there's a website URL entered, make sure it includes http:// or https://
        if website:
            parsed_url = urlparse(website)
            if not parsed_url.scheme:
                # If there's no scheme, add "https://"
                website = 'https://' + website
        return website

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

from django import forms
from .models import Business
from .widgets import CKEditorCDNWidget

class BusinessForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorCDNWidget(), required=False)

    class Meta:
        model = Business
        fields = ['logo', 'name', 'address', 'email', 'city', 'phone_number', 'category', 'description']



from django import forms
from .models import BusinessImage

class BusinessImageForm(forms.ModelForm):
    class Meta:
        model = BusinessImage
        fields = ['image', 'caption']