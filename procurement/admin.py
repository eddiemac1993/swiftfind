from django.contrib import admin

from .models import (
    ApprovalStep,
    ClarificationMessage,
    DeliveryNote,
    DocumentNumberSetting,
    EmailNotification,
    GoodsReceivedNote,
    Invoice,
    Notice,
    PaymentRecord,
    ProcurementRequest,
    Product,
    ProductCategory,
    PurchaseOrder,
    Quotation,
    QuotationItem,
    Receipt,
    RequestItem,
    School,
    Supplier,
    UserProfile,
)


class RequestItemInline(admin.TabularInline):
    model = RequestItem
    extra = 1


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "school", "supplier")
    list_filter = ("role",)
    search_fields = ("user__username", "school__name", "supplier__name")


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "province", "contact_person", "phone")
    search_fields = ("name", "district", "province")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "contact_person", "phone", "is_active")
    list_filter = ("is_active", "district", "categories")
    search_fields = ("name", "district", "contact_person")
    filter_horizontal = ("categories",)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "guide_price", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")


@admin.register(ProcurementRequest)
class ProcurementRequestAdmin(admin.ModelAdmin):
    list_display = ("reference", "title", "school", "status", "selected_supplier", "created_at")
    list_filter = ("status", "school__district", "selected_supplier")
    search_fields = ("reference", "title", "school__name")
    readonly_fields = ("reference", "created_at", "updated_at")
    inlines = [RequestItemInline]


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("quotation_number", "request", "supplier", "total_amount", "is_selected")
    list_filter = ("is_selected", "supplier")
    inlines = [QuotationItemInline]


admin.site.register(PurchaseOrder)
admin.site.register(DeliveryNote)
admin.site.register(GoodsReceivedNote)
admin.site.register(Invoice)
admin.site.register(PaymentRecord)
admin.site.register(Receipt)
admin.site.register(Notice)
admin.site.register(ClarificationMessage)
admin.site.register(ApprovalStep)
admin.site.register(DocumentNumberSetting)
admin.site.register(EmailNotification)
