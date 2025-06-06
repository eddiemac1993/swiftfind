from django.db import models
from django.contrib.auth.models import User
from directory.models import Business

class ProductCategory(models.Model):
    name = models.CharField(max_length=50)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='pos_system_product_categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Product Categories"
        unique_together = ('name', 'business')

class Product(models.Model):
    STOCK_STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    stock_status = models.CharField(max_length=20, choices=STOCK_STATUS_CHOICES, default='in_stock')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='pos_system_products')
    image = models.ImageField(upload_to='pos_system_product_images/', blank=True, null=True)
    barcode = models.CharField(max_length=50, blank=True, null=True)
    sku = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.business.name}"

    def save(self, *args, **kwargs):
        # Update stock status based on quantity
        if self.stock_quantity > 10:
            self.stock_status = 'in_stock'
        elif self.stock_quantity > 0:
            self.stock_status = 'low_stock'
        else:
            self.stock_status = 'out_of_stock'
        super().save(*args, **kwargs)

    @property
    def get_stock_status_class(self):
        if self.stock_quantity > 10:
            return ''
        if self.stock_quantity > 0:
            return 'warning'
        return 'danger'

    @property
    def get_stock_icon(self):
        if self.stock_quantity > 10:
            return 'check-circle'
        if self.stock_quantity > 5:
            return 'exclamation-circle'
        return 'times-circle'

class Sale(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='pos_system_sales')
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_id = models.CharField(max_length=50, unique=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    is_paid = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pos_system_sales_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Sale #{self.transaction_id} - {self.business.name}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='pos_system_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)