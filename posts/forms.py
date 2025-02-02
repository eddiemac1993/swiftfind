# forms.py
from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description', 'category', 'phone_number']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'phone_number': forms.TextInput(attrs={'pattern': '[0-9]{10}'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }