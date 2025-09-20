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

from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['content', 'user', 'post', 'created_at']  # Use actual field names
    list_filter = ['created_at', 'user']
    search_fields = ['content', 'user__username', 'post__title']
    raw_id_fields = ['post']