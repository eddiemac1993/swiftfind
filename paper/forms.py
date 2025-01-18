from django import forms
from .models import Paper, PaperItem
from django.forms import inlineformset_factory


class PaperForm(forms.ModelForm):
    class Meta:
        model = Paper
        fields = [
            'company_name', 'company_address', 'company_email', 'phone_number',
            'customer_name', 'date', 'paper_type', 'prepared_by', 'logo'  # Add 'logo' field
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),  # Use HTML5 date picker
            'company_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),  # Textarea for address
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'paper_type': forms.Select(attrs={'class': 'form-control'}),
            'prepared_by': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),  # Custom widget for logo
        }

    def clean_phone_number(self):
        """
        Validate the phone number field.
        """
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        return phone_number

class PaperItemForm(forms.ModelForm):
    class Meta:
        model = PaperItem
        fields = ['description', 'quantity', 'price']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Item description', 'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),  # Allow decimal values
        }

    def clean_quantity(self):
        """
        Validate the quantity field.
        """
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity

    def clean_price(self):
        """
        Validate the price field.
        """
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price


# Create a formset for PaperItem
PaperItemFormSet = inlineformset_factory(
    Paper,  # Parent model
    PaperItem,  # Child model
    form=PaperItemForm,  # Form for the child model
    extra=1,  # Number of empty forms to display
    can_delete=True,  # Allow deletion of items
    widgets={
        'description': forms.TextInput(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        'price': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)