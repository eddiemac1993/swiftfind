from django.contrib import admin
from .models import Category, Business, Review, BusinessImage, Advertisement
from django import forms
from django.utils.text import slugify
from django.shortcuts import redirect
from .models import SearchQuery
from .models import NewsFeed
from django.utils.html import format_html

class NewsFeedAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at', 'preview_content')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'content')

    def preview_content(self, obj):
        """ Show a short preview of the content with HTML rendering """
        return format_html(obj.content[:100] + "...")  # Show first 100 characters safely
    preview_content.short_description = "Content Preview"

admin.site.register(NewsFeed, NewsFeedAdmin)

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'slot', 'start_time', 'end_time', 'is_active', 'is_running')
    list_filter = ('is_active', 'slot')
    search_fields = ('title', 'small_text')

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'city', 'category', 'sort_by', 'timestamp', 'count')  # Include 'count' in list_display
    list_filter = ('timestamp', 'city', 'category')  # Filters for the right sidebar
    search_fields = ('query', 'city', 'category')  # Enable search functionality
    readonly_fields = ('timestamp',)  # Make timestamp non-editable
    ordering = ('-count',)  # Sort by count (highest to lowest) by default

class MultipleCategoryForm(forms.Form):
    names = forms.CharField(
        widget=forms.Textarea,
        help_text="Enter one category per line.",
        required=False  # Make this field optional
    )

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    add_form_template = 'admin/directory/category_add_form.html'  # Use the custom template

    def add_view(self, request, form_url='', extra_context=None):
        if request.method == 'POST':
            # Check if the bulk creation form was submitted
            if 'names' in request.POST:
                form = MultipleCategoryForm(request.POST)
                if form.is_valid():
                    names = form.cleaned_data['names'].splitlines()
                    for name in names:
                        name = name.strip()
                        if name:
                            slug = slugify(name)
                            counter = 1
                            while Category.objects.filter(slug=slug).exists():
                                slug = f"{slugify(name)}-{counter}"
                                counter += 1
                            Category.objects.create(name=name, slug=slug)
                    self.message_user(request, f"Added {len(names)} categories.")
                    # Redirect to the category list page after bulk creation
                    return redirect('admin:directory_category_changelist')
            else:
                # Handle the default single category creation form
                return super().add_view(request, form_url, extra_context)
        else:
            form = MultipleCategoryForm()

        extra_context = extra_context or {}
        extra_context['form'] = form
        return super().add_view(request, form_url, extra_context)

admin.site.register(Category, CategoryAdmin)

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
    list_display = ('business', 'rating', 'title', 'comment_preview', 'status', 'created_at', 'user_or_session')
    list_filter = ('status', 'rating', 'created_at', 'business')
    search_fields = ('business__name', 'title', 'comment', 'user__username', 'session_key')
    list_editable = ('status',)  # Allow editing the status directly from the list view
    raw_id_fields = ('business', 'user')  # Use raw_id_fields for better performance with large datasets
    date_hierarchy = 'created_at'  # Add a date hierarchy for easy filtering by date
    actions = ['approve_reviews', 'reject_reviews']  # Custom actions for bulk approval/rejection

    def comment_preview(self, obj):
        """Display a shortened preview of the comment."""
        return obj.comment[:50] + '...' if obj.comment else ''
    comment_preview.short_description = 'Comment Preview'

    def user_or_session(self, obj):
        """Display the user or session key for the review."""
        return obj.user.username if obj.user else f"Anonymous ({obj.session_key})"
    user_or_session.short_description = 'User/Session'

    def approve_reviews(self, request, queryset):
        """Custom action to approve selected reviews."""
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} reviews were approved.")
    approve_reviews.short_description = "Approve selected reviews"

    def reject_reviews(self, request, queryset):
        """Custom action to reject selected reviews."""
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} reviews were rejected.")
    reject_reviews.short_description = "Reject selected reviews"

@admin.register(BusinessImage)
class BusinessImageAdmin(admin.ModelAdmin):
    list_display = ['business', 'image', 'caption', 'created_at']
    list_filter = ['business']
    search_fields = ['business__name', 'caption']