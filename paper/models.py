from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
import random
import string

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
        # ('INVOICE', 'Invoice'),  # Invoice commented out
        ('RECEIPT', 'Receipt'),
        ('DELIVERY_NOTE', 'Delivery Note'),
    ]

    customer_name = models.CharField(max_length=255, default="Unknown Customer")
    date = models.DateField()
    paper_type = models.CharField(max_length=20, choices=PAPER_TYPE_CHOICES)
    paper_number = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    prepared_by = models.CharField(max_length=255, default="Unknown Preparer")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)

    def clean(self):
        if self.paper_type not in dict(self.PAPER_TYPE_CHOICES).keys():
            raise ValidationError({'paper_type': 'Invalid paper type.'})

    def save(self, *args, **kwargs):
        if not self.paper_number:
            prefix_mapping = {
                'QUOTATION': 'QTN',
                # 'INVOICE': 'INV',  # Invoice prefix commented out
                'RECEIPT': 'RCP',
                'DELIVERY_NOTE': 'DLN',
            }
            prefix = prefix_mapping.get(self.paper_type, 'PPR')
            self.paper_number = generate_unique_paper_number(prefix)
        super().save(*args, **kwargs)

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())

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
