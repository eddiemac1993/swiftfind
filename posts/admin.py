from django.contrib import admin
from .models import Post, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1  # Number of empty comment forms to display
    fields = ('name', 'content', 'created_at')  # Fields to display in the inline
    readonly_fields = ('created_at',)  # Make created_at read-only

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'phone_number', 'views', 'votes', 'created_at')  # Fields to display in the list view
    list_filter = ('category', 'created_at')  # Filters for the right sidebar
    search_fields = ('title', 'description', 'phone_number')  # Searchable fields
    prepopulated_fields = {'slug': ('title',)}  # Automatically populate slug from title
    inlines = [CommentInline]  # Add comments as inline

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'category', 'phone_number')
        }),
        ('Statistics', {
            'fields': ('views', 'votes'),
            'classes': ('collapse',)  # Collapsible section
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)  # Collapsible section
        }),
    )

    readonly_fields = ('created_at',)  # Make created_at read-only

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'post', 'content', 'created_at')  # Fields to display in the list view
    list_filter = ('created_at', 'post')  # Filters for the right sidebar
    search_fields = ('name', 'content', 'post__title')  # Searchable fields

    fieldsets = (
        (None, {
            'fields': ('post', 'name', 'content')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)  # Collapsible section
        }),
    )

    readonly_fields = ('created_at',)  # Make created_at read-only