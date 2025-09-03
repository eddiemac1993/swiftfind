from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from .models import ProductCategory, Product, Sale, SaleItem
from .models import RewardClaim
from django.utils import timezone
from .models import ProductView  # Add this import at the top

from .models import ChatLog

@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "created_at")
    search_fields = ("question", "answer")
    list_filter = ("created_at",)


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = (
        'product_link',
        'viewer_link',
        'viewed_at',
        'ip_address',
        'is_organic',
        'device_info',
        'view_duration'
    )
    list_filter = (
        'is_organic',
        'viewed_at',
        'product__business',
        'product__category',
    )
    search_fields = (
        'product__name',
        'viewer__username',
        'viewer__email',
        'ip_address',
        'user_agent'
    )
    readonly_fields = (
        'viewed_at',
        'ip_address',
        'user_agent',
        'referrer',
        'device_type',
        'view_duration'
    )
    date_hierarchy = 'viewed_at'
    list_per_page = 50

    def product_link(self, obj):
        if obj.product:
            url = reverse('admin:pos_system_product_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return "-"
    product_link.short_description = 'Product'
    product_link.admin_order_field = 'product__name'

    def viewer_link(self, obj):
        if obj.viewer:
            url = reverse('admin:auth_user_change', args=[obj.viewer.id])
            return format_html('<a href="{}">{}</a>', url, obj.viewer.username)
        return "Anonymous"
    viewer_link.short_description = 'Viewer'
    viewer_link.admin_order_field = 'viewer__username'

    def device_info(self, obj):
        if obj.user_agent:
            return obj.user_agent[:50] + "..." if len(obj.user_agent) > 50 else obj.user_agent
        return "-"
    device_info.short_description = 'Device Info'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'product', 'product__business', 'product__category', 'viewer'
        )

    def has_add_permission(self, request):
        return False  # Prevent manual creation of view records

    def has_change_permission(self, request, obj=None):
        return False  # Make all records read-only
@admin.register(RewardClaim)
class RewardClaimAdmin(admin.ModelAdmin):
    list_display = ('business', 'amount', 'views_count', 'status', 'requested_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('business__name',)
    actions = ['approve_claims', 'reject_claims']

    def approve_claims(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='approved',
            processed_at=timezone.now(),
            processed_by=request.user
        )
        self.message_user(request, f"{updated} claims approved")

    def reject_claims(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='rejected',
            processed_at=timezone.now(),
            processed_by=request.user
        )
        self.message_user(request, f"{updated} claims rejected")

    approve_claims.short_description = "Approve selected claims"
    reject_claims.short_description = "Reject selected claims"
# Common admin settings
class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25

# Product Category Admin
@admin.register(ProductCategory)
class ProductCategoryAdmin(BaseAdmin):
    list_display = ('name', 'business', 'location', 'product_count', 'created_at')
    list_filter = ('business', 'created_at')
    search_fields = ('name', 'business__name', 'location')
    fieldsets = (
        (None, {
            'fields': ('name', 'business', 'location')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Products'

# Product Admin
class StockStatusFilter(admin.SimpleListFilter):
    title = 'stock status'
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        return [
            ('in_stock', 'In Stock'),
            ('low_stock', 'Low Stock'),
            ('out_of_stock', 'Out of Stock'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'in_stock':
            return queryset.filter(stock_quantity__gt=10)
        elif self.value() == 'low_stock':
            return queryset.filter(stock_quantity__gt=0, stock_quantity__lte=10)
        elif self.value() == 'out_of_stock':
            return queryset.filter(stock_quantity=0)

@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = (
        'name',
        'business',
        'category',
        'price',
        'stock_quantity',
        'stock_status_display',
        'barcode',
        'is_active',
        'created_at'
    )
    list_filter = (
        'business',
        'category',
        'is_active',
        StockStatusFilter,
        'created_at'
    )
    search_fields = (
        'name',
        'description',
        'barcode',
        'sku',
        'business__name',
        'category__name'
    )
    list_editable = ('price', 'is_active')
    list_select_related = ('business', 'category')
    readonly_fields = ('stock_status', 'created_at', 'updated_at', 'image_preview')
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'description',
                'business',
                'category',
                'is_active'
            )
        }),
        ('Pricing & Inventory', {
            'fields': (
                'price',
                'cost_price',
                'stock_quantity',
                'stock_status',
                'barcode',
                'sku'
            )
        }),
        ('Location & Media', {
            'fields': (
                'location',
                'image',
                'image_preview'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['activate_products', 'deactivate_products', 'update_stock_status']

    def stock_status_display(self, obj):
        status_map = {
            'in_stock': '✅ In Stock',
            'low_stock': '⚠️ Low Stock',
            'out_of_stock': '❌ Out of Stock'
        }
        return status_map.get(obj.stock_status, obj.stock_status)
    stock_status_display.short_description = 'Stock Status'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 200px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

    def activate_products(self, request, queryset):
        queryset.update(is_active=True)
    activate_products.short_description = "Activate selected products"

    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_products.short_description = "Deactivate selected products"

    def update_stock_status(self, request, queryset):
        for product in queryset:
            product.save()  # This will trigger the stock status update in the save method
    update_stock_status.short_description = "Update stock status for selected products"

# Sale Item Inline
class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('unit_price', 'total_price', 'created_at')
    fields = ('product', 'quantity', 'unit_price', 'total_price', 'location', 'created_at')
    autocomplete_fields = ('product',)

    def has_add_permission(self, request, obj=None):
        return False

# Sale Admin
class TotalSalesFilter(admin.SimpleListFilter):
    title = 'total sales amount'
    parameter_name = 'total_amount'

    def lookups(self, request, model_admin):
        return [
            ('<100', 'Less than $100'),
            ('100-500', '$100 to $500'),
            ('500-1000', '$500 to $1000'),
            ('>1000', 'More than $1000'),
        ]

    def queryset(self, request, queryset):
        if self.value() == '<100':
            return queryset.filter(total__lt=100)
        elif self.value() == '100-500':
            return queryset.filter(total__gte=100, total__lte=500)
        elif self.value() == '500-1000':
            return queryset.filter(total__gt=500, total__lte=1000)
        elif self.value() == '>1000':
            return queryset.filter(total__gt=1000)

@admin.register(Sale)
class SaleAdmin(BaseAdmin):
    list_display = (
        'transaction_id',
        'business',
        'customer_display',
        'total',
        'payment_method_display',
        'is_paid',
        'created_at',
        'items_count',
        'created_by_display'
    )
    list_filter = (
        'business',
        'is_paid',
        'payment_method',
        'created_at',
        TotalSalesFilter
    )
    search_fields = (
        'transaction_id',
        'business__name',
        'customer__username',
        'customer__first_name',
        'customer__last_name'
    )
    readonly_fields = (
        'transaction_id',
        'subtotal',
        'tax',
        'discount',
        'total',
        'created_at',
        'updated_at',
        'created_by',
        'customer'
    )
    fieldsets = (
        ('Sale Information', {
            'fields': (
                'transaction_id',
                'business',
                'customer',
                'created_by'
            )
        }),
        ('Payment Details', {
            'fields': (
                'subtotal',
                'tax',
                'discount',
                'total',
                'payment_method',
                'is_paid'
            )
        }),
        ('Additional Information', {
            'fields': (
                'location',
                'notes'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = (SaleItemInline,)

    def customer_display(self, obj):
        if obj.customer:
            return f"{obj.customer.get_full_name() or obj.customer.username}"
        return "Anonymous"
    customer_display.short_description = 'Customer'

    def payment_method_display(self, obj):
        method_map = {
            'cash': '💵 Cash',
            'card': '💳 Card',
            'mobile_money': '📱 Mobile Money',
            'bank_transfer': '🏦 Bank Transfer'
        }
        return method_map.get(obj.payment_method, obj.payment_method)
    payment_method_display.short_description = 'Payment'

    def items_count(self, obj):
        return obj.pos_system_items.count()
    items_count.short_description = 'Items'

    def created_by_display(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return "System"
    created_by_display.short_description = 'Created By'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'business', 'customer', 'created_by'
        ).annotate(
            items_count=Count('pos_system_items')
        )

# Sale Item Admin
@admin.register(SaleItem)
class SaleItemAdmin(BaseAdmin):
    list_display = (
        'sale_link',
        'product_link',
        'quantity',
        'unit_price',
        'total_price',
        'created_at'
    )
    list_filter = ('sale__business', 'created_at')
    search_fields = (
        'sale__transaction_id',
        'product__name',
        'product__barcode'
    )
    readonly_fields = ('unit_price', 'total_price', 'created_at')

    def sale_link(self, obj):
        url = reverse('admin:pos_system_sale_change', args=[obj.sale.id])
        return format_html('<a href="{}">{}</a>', url, obj.sale.transaction_id)
    sale_link.short_description = 'Sale'

    def product_link(self, obj):
        if obj.product:
            url = reverse('admin:pos_system_product_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return "Deleted Product"
    product_link.short_description = 'Product'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'sale', 'product', 'product__business'
        )

# Custom Admin Site Settings
admin.site.site_header = "Swiftfind Administration"
admin.site.site_title = "Swiftfind Admin Portal"
admin.site.index_title = "Welcome to the Swiftfind Admin Portal"