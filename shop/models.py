from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Shop(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Save the Shop object
        super().save(*args, **kwargs)

        # Create a Balance object for the Shop if it doesn't exist
        if not hasattr(self, 'balance'):
            Balance.objects.create(shop=self, total_amount=0, amount_paid=0, amount_due=0)

class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True)  # Make it nullable
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name



class Request(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
    ]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)  # Add a default value
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.shop.name} - {self.item.name}"

class RequestItem(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity} x {self.item.name} in {self.request}"

from django.db import models
from django.conf import settings
from django.db.models import Sum

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def total_items(self):
        """
        Calculate the total number of items in the cart.
        """
        return self.items.aggregate(total_items=Sum('quantity'))['total_items'] or 0

    def total_price(self):
        """
        Calculate the total price of all items in the cart.
        """
        return sum(item.total_price() for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.item.name} in {self.cart}"

    def total_price(self):
        """
        Calculate the total price for this cart item.
        """
        return self.item.price * self.quantity

class Payment(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_type = models.CharField(max_length=50, choices=[('partial', 'Partial'), ('full', 'Full')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.request.shop.name} - {self.amount_paid}"

class Balance(models.Model):
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.shop.name} - {self.amount_due}"

    def update_balance(self):
        self.amount_due = self.total_amount - self.amount_paid
        self.save()

    def make_payment(self, amount, payment_type):
        if payment_type == 'partial':
            self.amount_paid += amount
        elif payment_type == 'full':
            self.amount_paid = self.total_amount
        self.update_balance()

    def get_payment_intervals(self):
        intervals = {
            'initial': self.total_amount * 0.4,
            'after_one_week': self.total_amount * 0.3,
            'after_two_weeks': self.total_amount * 0.3,
        }
        return intervals