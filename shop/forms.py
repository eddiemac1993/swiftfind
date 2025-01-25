from django import forms
from .models import Item, Shop, Request, Payment, Balance

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'description', 'price']

class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'address']

from django import forms
from .models import Request, Item

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['item', 'quantity']

    def __init__(self, *args, **kwargs):
        self.shop = kwargs.pop('shop', None)
        super().__init__(*args, **kwargs)

        # Filter items (if needed)
        if self.shop:
            self.fields['item'].queryset = Item.objects.all()  # Remove the 'available' filter
class PaymentForm(forms.ModelForm):
    payment_type = forms.ChoiceField(choices=[('partial', 'Partial'), ('full', 'Full')])

    class Meta:
        model = Payment
        fields = ['amount_paid', 'payment_type']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        amount_paid = cleaned_data.get('amount_paid')
        payment_type = cleaned_data.get('payment_type')

        if self.request:
            balance = Balance.objects.get(shop=self.request.shop)
            if payment_type == 'partial':
                if amount_paid > balance.amount_due:
                    raise forms.ValidationError("Amount paid cannot exceed the due amount.")
            elif payment_type == 'full':
                if amount_paid != balance.amount_due:
                    raise forms.ValidationError("Full payment must match the due amount.")
        return cleaned_data

class BalanceForm(forms.ModelForm):
    class Meta:
        model = Balance
        fields = ['total_amount', 'amount_paid', 'amount_due']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount_due'].disabled = True  # Amount due is calculated automatically