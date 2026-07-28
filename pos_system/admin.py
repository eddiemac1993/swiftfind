from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from .models import (
    FiscalEvent, FiscalInvoiceSequence, ProductCategory, Product, Sale,
    SaleItem, ZRAConfiguration,
)
from .models import RewardClaim
from django.utils import timezone
from .models import ProductView  # Add this import at the top

from .models import ChatLog
from django.contrib import admin
from .models import Order, OrderItem  # Import your models
from django.contrib import admin
from .models import Order, OrderItem


@admin.register(ZRAConfiguration)
class ZRAConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'business', 'tpin', 'branch_id', 'environment', 'device_initialized',
        'enabled', 'updated_at',
    )
    list_filter = ('enabled', 'device_initialized', 'environment')
    search_fields = ('business__name', 'tpin', 'cis_number', 'sdc_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FiscalInvoiceSequence)
class FiscalInvoiceSequenceAdmin(admin.ModelAdmin):
    list_display = (
        'business', 'invoice_type', 'transaction_type', 'last_number', 'updated_at',
    )
    readonly_fields = (
        'business', 'invoice_type', 'transaction_type', 'last_number', 'updated_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FiscalEvent)
class FiscalEventAdmin(admin.ModelAdmin):
    list_display = ('sale', 'event_type', 'created_at')
    search_fields = ('sale__transaction_id', 'event_type', 'message')
    readonly_fields = ('sale', 'event_type', 'message', 'payload', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # No empty extra forms
    readonly_fields = ('product', 'quantity', 'price', 'get_subtotal_display')  # Use the method

    # Optional: If you want to show subtotal in the inline
    fields = ('product', 'quantity', 'price', 'get_subtotal_display')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'created_at', 'total', 'status', 'get_payment_status_display')
    list_filter = ('status', 'created_at', 'business')
    search_fields = ('customer__username', 'customer__email', 'id', 'order_number')
    readonly_fields = ('created_at', 'updated_at', 'order_number', 'uuid')
    inlines = [OrderItemInline]

    # Add this method to display payment status (if you want to show it)
    def get_payment_status_display(self, obj):
        # If you have a payment_status field, use it here
        # Otherwise, you might want to remove this
        return "Paid"  # Placeholder - adjust based on your actual field
    get_payment_status_display.short_description = 'Payment Status'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'price', 'get_subtotal_display')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'product_name')
    readonly_fields = ('get_subtotal_display',)  # Make subtotal read-only

    # If you want to show the calculated subtotal in list view
    def get_subtotal_display(self, obj):
        return f"ZMW {obj.subtotal():.2f}"
    get_subtotal_display.short_description = 'Subtotal'
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
        ('ZRA Smart Invoice', {
            'fields': (
                'zra_item_code', 'zra_item_class_code', 'zra_item_type',
                'zra_origin_country_code', 'zra_package_unit_code',
                'zra_quantity_unit_code', 'zra_tax_category',
                'zra_registered', 'zra_last_response',
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = [
        'activate_products', 'deactivate_products', 'update_stock_status',
        'register_products_with_zra',
    ]

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

    def register_products_with_zra(self, request, queryset):
        from django.core.exceptions import ValidationError
        from pos_system.services.fiscal import build_item_payload
        from pos_system.services.zra_vsdc import VSDCClient, VSDCError

        registered = 0
        failures = []
        for product in queryset.select_related('business'):
            try:
                configuration = product.business.zra_configuration
                if not (
                    configuration.tpin and configuration.vsdc_base_url
                    and configuration.device_initialized
                ):
                    raise ValidationError(
                        'TPIN, initialized device and VSDC URL are required.'
                    )
                payload = build_item_payload(product, configuration, request.user)
                client = VSDCClient(configuration)
                response = (
                    client.update_item(payload)
                    if product.zra_registered
                    else client.save_item(payload)
                )
                product.zra_registered = True
                product.zra_last_response = response
                product.save(update_fields=('zra_registered', 'zra_last_response', 'updated_at'))
                registered += 1
            except (AttributeError, ValidationError, VSDCError) as exc:
                failures.append(f"{product.name}: {exc}")
        if registered:
            self.message_user(request, f"{registered} product(s) registered with ZRA VSDC.")
        if failures:
            self.message_user(request, ' | '.join(failures), level=messages.ERROR)
    register_products_with_zra.short_description = "Register/update selected products with ZRA VSDC"

# Sale Item Inline
class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('unit_price', 'total_price', 'created_at')
    fields = ('product', 'quantity', 'unit_price', 'total_price', 'location', 'created_at')
    autocomplete_fields = ('product',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if obj and obj.fiscal_status == 'CERTIFIED':
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
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
    actions = ('retry_zra_stock_sync',)
    list_display = (
        'transaction_id',
        'business',
        'customer_display',
        'total',
        'payment_method_display',
        'fiscal_status',
        'zra_receipt_number',
        'is_paid',
        'created_at',
        'items_count',
        'created_by_display'
    )
    list_filter = (
        'business',
        'is_paid',
        'payment_method',
        'fiscal_status',
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
        'customer',
        'cis_invoice_number', 'invoice_type', 'transaction_type',
        'original_sale', 'customer_name_snapshot', 'customer_tpin',
        'customer_phone', 'currency_code', 'exchange_rate', 'fiscal_status',
        'zra_receipt_number', 'zra_internal_data', 'zra_receipt_signature',
        'zra_sdc_id', 'zra_machine_registration_number', 'zra_qr_code_url',
        'zra_publication_datetime', 'zra_request', 'zra_response',
        'fiscalized_at', 'stock_sync_status', 'stock_sync_error',
    )

    def has_delete_permission(self, request, obj=None):
        if obj and obj.fiscal_status == 'CERTIFIED':
            return False
        return super().has_delete_permission(request, obj)

    def retry_zra_stock_sync(self, request, queryset):
        from pos_system.services.fiscal import build_stock_payloads
        from pos_system.services.zra_vsdc import VSDCClient, VSDCError

        synchronized = 0
        failures = []
        for sale in queryset.select_related('business', 'created_by'):
            if sale.fiscal_status != 'CERTIFIED' or sale.stock_sync_status != 'FAILED':
                continue
            try:
                configuration = sale.business.zra_configuration
                movement, master = build_stock_payloads(sale, configuration)
                client = VSDCClient(configuration)
                client.save_stock_items(movement)
                client.save_stock_master(master)
                sale.stock_sync_status = 'SYNCED'
                sale.stock_sync_error = ''
                sale.save(update_fields=('stock_sync_status', 'stock_sync_error', 'updated_at'))
                FiscalEvent.objects.create(
                    sale=sale, event_type='STOCK_SYNC_RETRIED',
                    message='Stock synchronization completed from Django admin.',
                )
                synchronized += 1
            except (AttributeError, VSDCError) as exc:
                failures.append(f"{sale.transaction_id}: {exc}")
        if synchronized:
            self.message_user(request, f"{synchronized} sale(s) synchronized with ZRA stock.")
        if failures:
            self.message_user(request, ' | '.join(failures), level=messages.ERROR)
    retry_zra_stock_sync.short_description = "Retry ZRA stock sync for selected certified sales"
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
        ('ZRA Smart Invoice', {
            'fields': (
                'cis_invoice_number', 'invoice_type', 'transaction_type',
                'original_sale', 'customer_name_snapshot', 'customer_tpin',
                'customer_phone', 'currency_code', 'exchange_rate',
                'fiscal_status', 'zra_receipt_number', 'zra_sdc_id',
                'zra_machine_registration_number', 'zra_publication_datetime',
                'zra_qr_code_url', 'zra_internal_data',
                'zra_receipt_signature', 'fiscalized_at',
                'stock_sync_status', 'stock_sync_error',
                'zra_request', 'zra_response',
            ),
            'classes': ('collapse',),
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

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.sale.fiscal_status == 'CERTIFIED':
            return tuple(field.name for field in self.model._meta.fields)
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.sale.fiscal_status == 'CERTIFIED':
            return False
        return super().has_delete_permission(request, obj)

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
