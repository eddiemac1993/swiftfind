from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import random
import string
from decimal import Decimal

def generate_unique_paper_number(prefix):
    """Generate a unique and random numeric paper number."""
    while True:
        # Generate a random 6-digit number
        random_part = ''.join(random.choices(string.digits, k=3))
        paper_number = f"{prefix}-{random_part}"
        if not Paper.objects.filter(paper_number=paper_number).exists():
            return paper_number

class Paper(models.Model):
    company_name = models.CharField(max_length=255, default="Unknown Company")
    company_address = models.TextField(default="Unknown Address")
    company_email = models.EmailField(default="unknown@example.com")
    phone_number = models.CharField(max_length=50, default="000-000-0000")

    PAPER_TYPE_CHOICES = [
        ('QUOTATION', 'Quotation'),
        ('RECEIPT', 'Receipt'),
        ('DELIVERY_NOTE', 'Delivery Note'),
    ]

    VAT_RATE_CHOICES = [
        (0, 'No VAT (0%)'),
        (5, 'VAT 5%'),
        (10, 'VAT 10%'),
        (16, 'VAT 16%'),
        (20, 'VAT 20%'),
    ]

    customer_name = models.CharField(max_length=255, default="Unknown Customer")
    date = models.DateField()
    paper_type = models.CharField(max_length=20, choices=PAPER_TYPE_CHOICES)
    paper_number = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    prepared_by = models.CharField(max_length=255, default="Unknown Preparer")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)

    # New VAT-related fields
    vat_rate = models.IntegerField(
        choices=VAT_RATE_CHOICES,
        default=0,
        help_text="Select the applicable VAT rate"
    )

    def clean(self):
        if self.paper_type not in dict(self.PAPER_TYPE_CHOICES).keys():
            raise ValidationError({'paper_type': 'Invalid paper type.'})

    def save(self, *args, **kwargs):
        if not self.paper_number:
            prefix_mapping = {
                'QUOTATION': 'QTN',
                'RECEIPT': 'RCP',
                'DELIVERY_NOTE': 'DLN',
            }
            prefix = prefix_mapping.get(self.paper_type, 'PPR')
            self.paper_number = generate_unique_paper_number(prefix)
        super().save(*args, **kwargs)


    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def vat_amount(self):
        # Ensure both values are Decimal
        subtotal = Decimal(str(self.subtotal))
        vat_rate = Decimal(str(self.vat_rate)) / Decimal('100')
        return subtotal * vat_rate

    @property
    def total_amount(self):
        # Ensure both values are Decimal
        subtotal = Decimal(str(self.subtotal))
        vat = Decimal(str(self.vat_amount))
        return subtotal + vat

    def __str__(self):
        return f"{self.get_paper_type_display()} - {self.paper_number} ({self.customer_name})"

class PaperItem(models.Model):
    paper = models.ForeignKey(Paper, related_name='items', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.price}"

    class Meta:
        ordering = ['id']

from django.db import models, IntegrityError
from django.utils import timezone
from django.utils.text import slugify
import uuid

def generate_unique_slug(name):
    slug = slugify(name)
    unique_slug = slug
    while Guest.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{slug}-{uuid.uuid4().hex[:6]}"
    return unique_slug

class Guest(models.Model):
    STATUS_CHOICES = [
        ('in', 'In Venue'),
        ('out', 'Not in Venue'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='out')

    def save(self, *args, **kwargs):
        if not self.slug or self.name != getattr(self, '_original_name', None):
            self.slug = generate_unique_slug(self.name)
        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            self.slug = generate_unique_slug(self.name)
            super().save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_name = self.name

    def __str__(self):
        return f"{self.name} ({self.slug}) - {self.get_status_display()}"
