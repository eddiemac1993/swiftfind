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
# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import BusinessMember, BusinessRole, BusinessDepartment

class ReferralForm(forms.Form):
    referrer_username = forms.CharField(
        max_length=150,
        required=False,
        help_text="Enter the username of the person who referred you (optional)"
    )

    def clean_referrer_username(self):
        username = self.cleaned_data.get('referrer_username')
        if username:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                raise forms.ValidationError("User with this username does not exist.")
        return None
class BusinessMemberForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = BusinessMember
        fields = ['user', 'role', 'business_username', 'password', 'employee_id', 'department', 'position']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.all()

class BusinessRoleForm(forms.ModelForm):
    class Meta:
        model = BusinessRole
        fields = ['name', 'description', 'permissions', 'is_default']

class BusinessDepartmentForm(forms.ModelForm):
    class Meta:
        model = BusinessDepartment
        fields = ['name', 'description', 'parent_department']

    def __init__(self, *args, **kwargs):
        business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)
        if business:
            self.fields['parent_department'].queryset = BusinessDepartment.objects.filter(business=business)

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
from django_ckeditor_5.widgets import CKEditor5Widget
from django.core.validators import FileExtensionValidator

class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['logo', 'name', 'category', 'email', 'phone_number', 'city', 'address', 'description']
        widgets = {
            'description': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='default'
            ),
            'address': forms.TextInput(attrs={'placeholder': 'Street, Building, etc.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['address'].required = True


class BusinessUpdateForm(forms.ModelForm):
    show_store_link = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'toggle-checkbox'}),
        label="Show Store Link in Navigation"
    )

    class Meta:
        model = Business
        fields = ['logo', 'name', 'email', 'city', 'phone_number', 'category',
                 'show_store_link', 'description', 'company_profile']
        widgets = {
            'description': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='default'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['show_store_link'].initial = self.instance.show_store_link

    def save(self, commit=True):
        business = super().save(commit=False)
        business.show_store_link = self.cleaned_data.get('show_store_link', False)
        if commit:
            business.save()
            self.save_m2m()
        return business

from django.core.exceptions import ValidationError
from urllib.parse import urlparse

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


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
from .models import BusinessImage

class BusinessImageForm(forms.ModelForm):
    class Meta:
        model = BusinessImage
        fields = ['image', 'caption']