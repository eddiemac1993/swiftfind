from django.db import models
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Item(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)  # Supplier price
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Price with 30% markup
    source = models.CharField(max_length=200, default="Unknown", help_text="Brand, restaurant, manufacturer, or shop name")
    image = models.ImageField(upload_to='item_images/', blank=True, null=True, help_text="Optional image for the item")

    def save(self, *args, **kwargs):
        self.selling_price = self.base_price * Decimal("1.30")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.source})"


class Cart(models.Model):
    items = models.ManyToManyField(Item, through='CartItem')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    referred_by = models.CharField(max_length=15, blank=True, null=True, help_text="Optional phone number of the person who recommended the items")

    def update_total(self):
        self.total_amount = sum(item.total_price for item in self.cartitem_set.all())
        self.save()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.total_price = self.item.selling_price * self.quantity
        super().save(*args, **kwargs)
        self.cart.update_total()

    def __str__(self):
        return f"{self.quantity} x {self.item.name}"