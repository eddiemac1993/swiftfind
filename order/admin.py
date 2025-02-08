from django.contrib import admin
from .models import Category, Item, Cart, CartItem

class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'selling_price')
    list_filter = ('category',)
    search_fields = ('name',)

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_amount')
    inlines = [CartItemInline]

admin.site.register(Category)
admin.site.register(Item, ItemAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem)
