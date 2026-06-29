from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import (
    ApprovalStep,
    ClarificationMessage,
    DeliveryNote,
    DocumentNumberSetting,
    GoodsReceivedNote,
    Invoice,
    PaymentRecord,
    ProcurementRequest,
    PurchaseOrder,
    Quotation,
    QuotationItem,
    Receipt,
    RequestItem,
    School,
    Supplier,
)


class DateInput(forms.DateInput):
    input_type = "date"


class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css = "form-check-input"
            field.widget.attrs.setdefault("class", css)


class OptionalAccountMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"] = forms.CharField(
            required=False,
            label="Login username",
            help_text="Optional. Fill this in to create a linked user account.",
        )
        self.fields["password"] = forms.CharField(
            required=False,
            label="Temporary password",
            widget=forms.PasswordInput(render_value=True),
            help_text="Optional. Use a temporary password the user can change later.",
        )
        for name in ["username", "password"]:
            self.fields[name].widget.attrs.setdefault("class", "form-control")

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username")
        password = cleaned.get("password")
        if username and not password:
            self.add_error("password", "Enter a temporary password for the new login account.")
        if password and not username:
            self.add_error("username", "Enter a username for the new login account.")
        return cleaned


class SchoolForm(OptionalAccountMixin, BootstrapModelForm):
    class Meta:
        model = School
        fields = ["name", "district", "province", "address", "contact_person", "phone", "email"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class SupplierForm(OptionalAccountMixin, BootstrapModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "district", "address", "contact_person", "phone", "email", "categories", "is_active"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "categories": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categories"].widget.attrs["class"] = "choice-grid"


class ProcurementRequestForm(BootstrapModelForm):
    def __init__(self, *args, locked_school=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.locked_school = locked_school
        self.fields["quotation_deadline"].input_formats = ["%Y-%m-%dT%H:%M"]
        if locked_school:
            self.fields.pop("school", None)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.locked_school:
            instance.school = self.locked_school
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    class Meta:
        model = ProcurementRequest
        fields = ["school", "title", "needed_by", "quotation_deadline", "notes"]
        widgets = {
            "needed_by": DateInput(),
            "quotation_deadline": DateTimeInput(format="%Y-%m-%dT%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }


class RequestItemForm(BootstrapModelForm):
    class Meta:
        model = RequestItem
        fields = ["product", "quantity", "notes"]


RequestItemFormSet = inlineformset_factory(
    ProcurementRequest,
    RequestItem,
    form=RequestItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class QuotationForm(BootstrapModelForm):
    def __init__(self, *args, locked_supplier=None, request_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.locked_supplier = locked_supplier
        if request_queryset is not None:
            self.fields["request"].queryset = request_queryset
        if locked_supplier:
            self.fields.pop("supplier", None)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.locked_supplier:
            instance.supplier = self.locked_supplier
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    class Meta:
        model = Quotation
        fields = ["request", "supplier", "quotation_number", "valid_until", "delivery_days", "notes"]
        widgets = {"valid_until": DateInput(), "notes": forms.Textarea(attrs={"rows": 4})}


class QuotationSelectionForm(forms.Form):
    selection_reason = forms.CharField(
        label="Reason for selecting this supplier",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )


class QuotationItemForm(BootstrapModelForm):
    class Meta:
        model = QuotationItem
        fields = ["request_item", "unit_price"]
        widgets = {"request_item": forms.HiddenInput()}


QuotationItemFormSet = inlineformset_factory(
    Quotation,
    QuotationItem,
    form=QuotationItemForm,
    extra=0,
    can_delete=False,
)


class PurchaseOrderForm(BootstrapModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ["request", "supplier", "po_number", "issued_date", "document", "notes"]
        widgets = {"issued_date": DateInput()}

    def __init__(self, *args, request_queryset=None, supplier=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request_queryset is not None:
            self.fields["request"].queryset = request_queryset
        if supplier:
            self.locked_supplier = supplier
            self.fields.pop("supplier", None)
        else:
            self.locked_supplier = None

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.locked_supplier:
            instance.supplier = self.locked_supplier
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class DeliveryNoteForm(BootstrapModelForm):
    class Meta:
        model = DeliveryNote
        fields = ["request", "supplier", "delivery_number", "delivered_date", "items_delivered", "document", "notes"]
        widgets = {
            "delivered_date": DateInput(),
            "items_delivered": forms.Textarea(attrs={"rows": 4, "placeholder": "List delivered items, quantities, and any shortages."}),
        }

    def __init__(self, *args, request_queryset=None, supplier=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request_queryset is not None:
            self.fields["request"].queryset = request_queryset
        if supplier:
            self.locked_supplier = supplier
            self.fields.pop("supplier", None)
        else:
            self.locked_supplier = None

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.locked_supplier:
            instance.supplier = self.locked_supplier
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class GoodsReceivedNoteForm(BootstrapModelForm):
    class Meta:
        model = GoodsReceivedNote
        fields = ["request", "grn_number", "received_date", "received_by", "condition_notes"]
        widgets = {"received_date": DateInput()}

    def __init__(self, *args, request_queryset=None, supplier=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request_queryset is not None:
            self.fields["request"].queryset = request_queryset


class InvoiceForm(BootstrapModelForm):
    class Meta:
        model = Invoice
        fields = ["request", "supplier", "invoice_number", "invoice_date", "amount", "document", "notes"]
        widgets = {"invoice_date": DateInput()}

    def __init__(self, *args, request_queryset=None, supplier=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request_queryset is not None:
            self.fields["request"].queryset = request_queryset
        if supplier:
            self.locked_supplier = supplier
            self.fields.pop("supplier", None)
        else:
            self.locked_supplier = None

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.locked_supplier:
            instance.supplier = self.locked_supplier
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class PaymentRecordForm(BootstrapModelForm):
    class Meta:
        model = PaymentRecord
        fields = ["request", "status", "amount", "payment_reference", "paid_date", "notes"]
        widgets = {"paid_date": DateInput()}

    def __init__(self, *args, request_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request_queryset is not None:
            self.fields["request"].queryset = request_queryset


class ReceiptForm(BootstrapModelForm):
    class Meta:
        model = Receipt
        fields = ["request", "supplier", "receipt_number", "receipt_date", "amount", "document", "notes"]
        widgets = {"receipt_date": DateInput()}

    def __init__(self, *args, request_queryset=None, supplier=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request_queryset is not None:
            self.fields["request"].queryset = request_queryset
        if supplier:
            self.locked_supplier = supplier
            self.fields.pop("supplier", None)
        else:
            self.locked_supplier = None

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.locked_supplier:
            instance.supplier = self.locked_supplier
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ClarificationMessageForm(BootstrapModelForm):
    class Meta:
        model = ClarificationMessage
        fields = ["recipient", "request", "subject", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 5})}


class ApprovalStepForm(BootstrapModelForm):
    class Meta:
        model = ApprovalStep
        fields = ["status", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class DocumentNumberSettingForm(BootstrapModelForm):
    class Meta:
        model = DocumentNumberSetting
        fields = ["document_type", "prefix", "next_number", "padding"]
    DocumentNumberSetting,
