from django.contrib import admin
from .models import Category, Item, Cart, CartItem

class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'selling_price', 'source', 'location')
    list_filter = ('category', 'source', 'location')
    search_fields = ('name', 'description', 'source', 'location')

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
