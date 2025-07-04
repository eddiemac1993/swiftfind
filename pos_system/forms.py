from django import forms
from .models import Product, ProductCategory

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'cost_price', 'stock_quantity', 
                 'category', 'location', 'image', 'barcode', 'sku', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'location': forms.TextInput(attrs={
                'placeholder': 'e.g., Aisle 3, Shelf B'
            }),
        }
        help_texts = {
            'location': 'Physical location of the product in your store',
        }

    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)
        
        if self.business:
            self.fields['category'].queryset = ProductCategory.objects.filter(business=self.business)

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'location']
        widgets = {
            'location': forms.TextInput(attrs={
                'placeholder': 'e.g., Section A, Back Room'
            }),
        }
        help_texts = {
            'location': 'General location for products in this category',
        }

    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)