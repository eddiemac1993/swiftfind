from django.db import models
import uuid
from django.core.exceptions import ValidationError
from directory.models import Business

class Product(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class Order(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = str(uuid.uuid4())[:8].upper()  # Generate a unique order number
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number} - ${self.total_amount}"

class Sale(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='sales')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='sales')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    sale_date = models.DateTimeField(auto_now_add=True)
    receipt_number = models.CharField(max_length=20, unique=True, blank=True)

    def clean(self):
        if self.quantity > self.product.stock_quantity:
            raise ValidationError(f"Not enough stock for {self.product.name}. Available: {self.product.stock_quantity}")

    def save(self, *args, **kwargs):
        self.full_clean()  # Run validation before saving
        self.total_price = self.product.price * self.quantity
        if not self.receipt_number:
            self.receipt_number = str(uuid.uuid4())[:8].upper()  # Generate a unique receipt number

        # Update the product's stock quantity
        self.product.stock_quantity -= self.quantity
        self.product.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sale of {self.quantity} x {self.product.name} on {self.sale_date}"