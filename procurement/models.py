from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class UserProfile(models.Model):
    ROLE_ADMIN = "ADMIN"
    ROLE_SCHOOL = "SCHOOL"
    ROLE_SUPPLIER = "SUPPLIER"
    ROLE_VIEWER = "VIEWER"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_SCHOOL, "School user"),
        (ROLE_SUPPLIER, "Supplier user"),
        (ROLE_VIEWER, "Ministry/DEBS/PEO viewer"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_VIEWER)
    school = models.ForeignKey("School", on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey("Supplier", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class School(models.Model):
    name = models.CharField(max_length=180)
    district = models.CharField(max_length=120)
    province = models.CharField(max_length=120, default="Central")
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=180)
    district = models.CharField(max_length=120)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    categories = models.ManyToManyField("ProductCategory", blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Product categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    unit = models.CharField(max_length=40, default="each")
    description = models.TextField(blank=True)
    guide_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__name", "name"]

    def __str__(self):
        return f"{self.name} ({self.unit})"


class ProcurementRequest(models.Model):
    STATUS_DRAFT = "DRAFT"
    STATUS_REQUESTED = "REQUESTED"
    STATUS_QUOTED = "QUOTED"
    STATUS_PO_ISSUED = "PO_ISSUED"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_GRN_CONFIRMED = "GRN_CONFIRMED"
    STATUS_INVOICED = "INVOICED"
    STATUS_PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    STATUS_PAID = "PAID"
    STATUS_CLOSED = "CLOSED"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_REQUESTED, "Requested"),
        (STATUS_QUOTED, "Quoted"),
        (STATUS_PO_ISSUED, "PO Issued"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_GRN_CONFIRMED, "GRN Confirmed"),
        (STATUS_INVOICED, "Invoiced"),
        (STATUS_PAYMENT_PROCESSING, "Payment Processing"),
        (STATUS_PAID, "Paid"),
        (STATUS_CLOSED, "Closed"),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="requests")
    title = models.CharField(max_length=180)
    reference = models.CharField(max_length=40, unique=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    needed_by = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    selected_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.reference:
            self.reference = f"SPR-{self.created_at:%Y%m%d}-{self.pk:04d}"
            super().save(update_fields=["reference"])

    def __str__(self):
        return f"{self.reference or 'New'} - {self.title}"

    def get_absolute_url(self):
        return reverse("request_detail", args=[self.pk])

    @property
    def selected_total(self):
        quotation = self.quotations.filter(is_selected=True).first()
        return quotation.total_amount if quotation else Decimal("0.00")


class ApprovalStep(models.Model):
    APPROVER_HEAD = "HEAD_TEACHER"
    APPROVER_COMMITTEE = "COMMITTEE"
    APPROVER_DEBS = "DEBS_PEO"
    APPROVER_CHOICES = [
        (APPROVER_HEAD, "Head teacher"),
        (APPROVER_COMMITTEE, "Procurement committee"),
        (APPROVER_DEBS, "DEBS/PEO"),
    ]
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_RETURNED = "RETURNED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_RETURNED, "Returned for correction"),
    ]

    request = models.ForeignKey(ProcurementRequest, on_delete=models.CASCADE, related_name="approval_steps")
    approver_role = models.CharField(max_length=30, choices=APPROVER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        unique_together = ["request", "approver_role"]

    def __str__(self):
        return f"{self.request.reference} - {self.get_approver_role_display()}"


class DocumentNumberSetting(models.Model):
    DOC_PO = "PO"
    DOC_DELIVERY = "DN"
    DOC_GRN = "GRN"
    DOC_INVOICE = "INV"
    DOC_CHOICES = [
        (DOC_PO, "Purchase Order"),
        (DOC_DELIVERY, "Delivery Note"),
        (DOC_GRN, "Goods Received Note"),
        (DOC_INVOICE, "Invoice"),
    ]

    document_type = models.CharField(max_length=10, choices=DOC_CHOICES, unique=True)
    prefix = models.CharField(max_length=20)
    next_number = models.PositiveIntegerField(default=1)
    padding = models.PositiveIntegerField(default=4)

    class Meta:
        ordering = ["document_type"]

    def generate_number(self):
        number = f"{self.prefix}-{self.next_number:0{self.padding}d}"
        self.next_number += 1
        self.save(update_fields=["next_number"])
        return number

    def __str__(self):
        return f"{self.get_document_type_display()} ({self.prefix})"


class RequestItem(models.Model):
    request = models.ForeignKey(ProcurementRequest, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.product} x {self.quantity}"


class Quotation(models.Model):
    request = models.ForeignKey(ProcurementRequest, on_delete=models.CASCADE, related_name="quotations")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="quotations")
    quotation_number = models.CharField(max_length=60)
    valid_until = models.DateField(null=True, blank=True)
    delivery_days = models.PositiveIntegerField(default=7)
    notes = models.TextField(blank=True)
    is_selected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["request", "supplier"]
        unique_together = ["request", "supplier"]

    def __str__(self):
        return f"{self.quotation_number} - {self.supplier}"

    @property
    def total_amount(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="items")
    request_item = models.ForeignKey(RequestItem, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def line_total(self):
        return self.request_item.quantity * self.unit_price

    def __str__(self):
        return f"{self.request_item.product} @ {self.unit_price}"


class PurchaseOrder(models.Model):
    request = models.OneToOneField(ProcurementRequest, on_delete=models.CASCADE, related_name="purchase_order")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    po_number = models.CharField(max_length=60)
    issued_date = models.DateField()
    document = models.FileField(upload_to="purchase_orders/", blank=True)
    confirmed_by_supplier = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.po_number


class DeliveryNote(models.Model):
    request = models.OneToOneField(ProcurementRequest, on_delete=models.CASCADE, related_name="delivery_note")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    delivery_number = models.CharField(max_length=60)
    delivered_date = models.DateField()
    document = models.FileField(upload_to="delivery_notes/", blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.delivery_number


class GoodsReceivedNote(models.Model):
    request = models.OneToOneField(ProcurementRequest, on_delete=models.CASCADE, related_name="grn")
    grn_number = models.CharField(max_length=60)
    received_date = models.DateField()
    received_by = models.CharField(max_length=120)
    condition_notes = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.grn_number


class Invoice(models.Model):
    request = models.OneToOneField(ProcurementRequest, on_delete=models.CASCADE, related_name="invoice")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    invoice_number = models.CharField(max_length=60)
    invoice_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    document = models.FileField(upload_to="invoices/", blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.invoice_number


class PaymentRecord(models.Model):
    STATUS_PROCESSING = "PROCESSING"
    STATUS_PAID = "PAID"
    STATUS_CHOICES = [
        (STATUS_PROCESSING, "Processing"),
        (STATUS_PAID, "Paid"),
    ]

    request = models.OneToOneField(ProcurementRequest, on_delete=models.CASCADE, related_name="payment")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROCESSING)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_reference = models.CharField(max_length=100, blank=True)
    paid_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.request.reference} - {self.get_status_display()}"


class Notice(models.Model):
    AUDIENCE_ALL = "ALL"
    AUDIENCE_SCHOOLS = "SCHOOLS"
    AUDIENCE_SUPPLIERS = "SUPPLIERS"
    AUDIENCE_VIEWERS = "VIEWERS"
    AUDIENCE_CHOICES = [
        (AUDIENCE_ALL, "All users"),
        (AUDIENCE_SCHOOLS, "Schools"),
        (AUDIENCE_SUPPLIERS, "Suppliers"),
        (AUDIENCE_VIEWERS, "Ministry/DEBS/PEO viewers"),
    ]

    title = models.CharField(max_length=180)
    body = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default=AUDIENCE_ALL)
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title


class ClarificationMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_clarifications")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_clarifications")
    request = models.ForeignKey(ProcurementRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="clarifications")
    subject = models.CharField(max_length=180)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject


class EmailNotification(models.Model):
    recipient = models.EmailField()
    subject = models.CharField(max_length=180)
    body = models.TextField()
    sent_successfully = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject
