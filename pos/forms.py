from django import forms
from .models import Product, Sale

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock_quantity']

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['quantity']