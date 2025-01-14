from django.contrib import admin
from .models import Category, Business, Review

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'address', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'address', 'owner__username')
    raw_id_fields = ('owner', 'category')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('business', 'rating', 'title', 'status', 'created_at')
    list_filter = ('status', 'rating', 'created_at')
    search_fields = ('business__name', 'title', 'comment')
    list_editable = ('status',)
    raw_id_fields = ('business', 'user')
    date_hierarchy = 'created_at'