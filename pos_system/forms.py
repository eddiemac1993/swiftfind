from django import forms
from .models import Product, ProductCategory

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'cost_price', 'stock_quantity', 
                 'category', 'image', 'barcode', 'sku', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)
        
        if self.business:
            self.fields['category'].queryset = ProductCategory.objects.filter(business=self.business)

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name']