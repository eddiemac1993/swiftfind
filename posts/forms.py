from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description', 'category', 'phone_number', 'location', 'price_range']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'phone_number': forms.TextInput(attrs={'pattern': '[0-9]{10}', 'placeholder': 'Enter a 10-digit phone number'}),
            'location': forms.TextInput(attrs={'placeholder': 'Enter the location (optional)'}),
            'price_range': forms.TextInput(attrs={'placeholder': 'Enter the price range (optional)'}),
        }
        labels = {
            'title': 'Post Title',
            'description': 'Post Description',
            'category': 'Category',
            'phone_number': 'Phone Number',
            'location': 'Location',
            'price_range': 'Price Range',
        }
        help_texts = {
            'title': 'Enter a descriptive title for your post.',
            'description': 'Provide details about the post.',
            'category': 'Select the category for the post.',
            'phone_number': 'Enter your contact phone number.',
            'location': 'Enter the location relevant to the post (optional).',
            'price_range': 'Enter the price range if applicable (optional).',
        }