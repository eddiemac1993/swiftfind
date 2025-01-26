from django.contrib import admin
from .models import Shop, Item, Request, Payment, Balance, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}

# Register the Balance model
@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('shop', 'total_amount', 'amount_paid', 'amount_due', 'created_at', 'updated_at')
    search_fields = ('shop__name',)
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

# Register Shop model
@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'user__username', 'address')
    readonly_fields = ('created_at', 'updated_at')

# Register Item model
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

# Register Request model
@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('shop', 'item', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('shop__name', 'item__name')
    readonly_fields = ('created_at', 'updated_at')

# Register Payment model
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('request', 'amount_paid', 'payment_type', 'payment_date')
    list_filter = ('payment_type', 'payment_date')
    search_fields = ('request__shop__name', 'request__item__name')
    readonly_fields = ('payment_date', 'created_at', 'updated_at')
