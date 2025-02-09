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
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Price with 20% markup

    def save(self, *args, **kwargs):
        # Convert 1.20 to a Decimal to avoid TypeError
        self.selling_price = self.base_price * Decimal("1.30")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Cart(models.Model):
    items = models.ManyToManyField(Item, through='CartItem')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

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