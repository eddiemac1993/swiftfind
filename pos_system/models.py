from django.db import models
from django.contrib.auth.models import User
from directory.models import Business
from django.db.models import Q
from django.urls import reverse

class ProductCategory(models.Model):
    name = models.CharField(max_length=50)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='pos_system_product_categories')
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Physical location of this category (e.g., Aisle 3, Section B)")
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

    UNIT_CHOICES = [
        ('piece', 'Piece'),
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('litre', 'Litre'),
        ('ml', 'Millilitre'),
        ('dozen', 'Dozen'),
        ('packet', 'Packet'),
        ('box', 'Box'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)

    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')  # 👈 Added

    stock_status = models.CharField(max_length=20, choices=STOCK_STATUS_CHOICES, default='in_stock')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='pos_system_products')
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Physical location of the product (e.g., Shelf 4, Warehouse A)")
    image = models.ImageField(upload_to='pos_system_product_images/', default='business_logos/default.jpg', blank=True, null=True)
    barcode = models.CharField(max_length=50, blank=True, null=True)
    sku = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.unit}) - {self.business.name}"

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

    def get_absolute_url(self):
        return reverse("pos_system:product_detail", args=[self.id])

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
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Location where the sale was made")
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
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Location where the item was stored")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

# In your pos_system/models.py

# pos_system/models.py (updated)
class ProductView(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    is_organic = models.BooleanField(default=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    referrer = models.TextField(blank=True, null=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)
    view_duration = models.PositiveIntegerField(default=0)  # in seconds
    claimed = models.BooleanField(default=False)
    claimed_at = models.DateTimeField(null=True, blank=True)
    claim = models.ForeignKey('RewardClaim', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'viewer'],
                name='unique_product_viewer',
                condition=Q(viewer__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['product', 'session_key'],
                name='unique_product_session',
                condition=Q(session_key__isnull=False)
            )
        ]
        indexes = [
            models.Index(fields=['product', 'viewed_at']),
            models.Index(fields=['session_key']),
            models.Index(fields=['viewed_at']),
            models.Index(fields=['claimed']),
            models.Index(fields=['product', 'viewer']),
            models.Index(fields=['product', 'session_key']),
        ]
        ordering = ['-viewed_at']

    def __str__(self):
        return f"View of {self.product.name} at {self.viewed_at}"

    def save(self, *args, **kwargs):
        # Set device type based on user agent
        if self.user_agent:
            if 'Mobile' in self.user_agent:
                self.device_type = 'mobile'
            elif 'Tablet' in self.user_agent:
                self.device_type = 'tablet'
            else:
                self.device_type = 'desktop'
        super().save(*args, **kwargs)

class RewardClaim(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='reward_claims')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    views_count = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_claims')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-requested_at']

# models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid

class Order(models.Model):
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    # Identification
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order_number = models.CharField(max_length=20, unique=True, blank=True)

    # Relationships
    business = models.ForeignKey(
        'directory.Business',
        on_delete=models.PROTECT,  # Prevent deletion if orders exist
        related_name='pos_orders'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    is_read = models.BooleanField(default=False)
    is_read_business = models.BooleanField(default=False)
    # Customer information
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True)
    customer_notes = models.TextField(blank=True)

    # Order details
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    delivery_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS,
        default='pending'
    )
    status_changed = models.DateTimeField(auto_now_add=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['business', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        if not self.uuid:
            self.uuid = uuid.uuid4()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        date_part = timezone.now().strftime('%y%m%d')
        last_order = Order.objects.filter(
            order_number__startswith=date_part
        ).order_by('-id').first()

        seq = 1
        if last_order and last_order.order_number:
            try:
                seq = int(last_order.order_number[-4:]) + 1
            except (ValueError, IndexError):
                pass

        return f"{date_part}{seq:04d}"

    def update_status(self, new_status, commit=True):
        if new_status != self.status:
            self.status = new_status
            self.status_changed = timezone.now()
            if commit:
                self.save()
            return True
        return False

    @property
    def items_total(self):
        """Backward-compatible alias for total calculation"""
        return sum(item.subtotal for item in self.items.all())

    def __str__(self):
        return f"Order #{self.order_number} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.PROTECT,  # Prevent deletion if ordered
        related_name='order_items'
    )

    # Snapshot of product details at time of order
    product_name = models.CharField(max_length=255)
    product_code = models.CharField(max_length=50, blank=True)
    product_description = models.TextField(blank=True)
    business_name = models.CharField(max_length=255)

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

class ChatLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat at {self.created_at} - {self.user if self.user else 'Guest'}"

# In your Order model
class OrderStatusUpdate(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=20, choices=Order.ORDER_STATUS)
    notes = models.TextField(blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order} - {self.get_status_display()} at {self.created_at}"