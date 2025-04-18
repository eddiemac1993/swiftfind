from django import forms
from .models import QuizScore

class SubmitScoreForm(forms.ModelForm):
    class Meta:
        model = QuizScore
        fields = ['username', 'phone_number']  # Include username
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Enter your username',
                'class': 'form-control',
            }),
            'phone_number': forms.TextInput(attrs={
                'placeholder': 'Enter your phone number',
                'class': 'form-control',
            }),
        }