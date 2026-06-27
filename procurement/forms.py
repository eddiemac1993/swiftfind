from django import forms
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
    RequestItem,
)


class DateInput(forms.DateInput):
    input_type = "date"


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css = "form-check-input"
            field.widget.attrs.setdefault("class", css)


class ProcurementRequestForm(BootstrapModelForm):
    class Meta:
        model = ProcurementRequest
        fields = ["school", "title", "needed_by", "notes"]
        widgets = {"needed_by": DateInput()}


class RequestItemForm(BootstrapModelForm):
    class Meta:
        model = RequestItem
        fields = ["product", "quantity", "notes"]


RequestItemFormSet = inlineformset_factory(
    ProcurementRequest,
    RequestItem,
    form=RequestItemForm,
    extra=4,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class QuotationForm(BootstrapModelForm):
    class Meta:
        model = Quotation
        fields = ["request", "supplier", "quotation_number", "valid_until", "delivery_days", "notes"]
        widgets = {"valid_until": DateInput()}


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


class DeliveryNoteForm(BootstrapModelForm):
    class Meta:
        model = DeliveryNote
        fields = ["request", "supplier", "delivery_number", "delivered_date", "document", "notes"]
        widgets = {"delivered_date": DateInput()}


class GoodsReceivedNoteForm(BootstrapModelForm):
    class Meta:
        model = GoodsReceivedNote
        fields = ["request", "grn_number", "received_date", "received_by", "condition_notes"]
        widgets = {"received_date": DateInput()}


class InvoiceForm(BootstrapModelForm):
    class Meta:
        model = Invoice
        fields = ["request", "supplier", "invoice_number", "invoice_date", "amount", "document", "notes"]
        widgets = {"invoice_date": DateInput()}


class PaymentRecordForm(BootstrapModelForm):
    class Meta:
        model = PaymentRecord
        fields = ["request", "status", "amount", "payment_reference", "paid_date", "notes"]
        widgets = {"paid_date": DateInput()}


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
