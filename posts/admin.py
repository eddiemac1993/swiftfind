from django.contrib import admin
from .models import Post, Comment

# Define a custom admin class for Post
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at', 'votes', 'views')  # List columns to display
    search_fields = ('title', 'description')  # Enable search by title and description
    list_filter = ('category', 'created_at')  # Filter posts by category and creation date
    ordering = ('-created_at',)  # Order posts by creation date, descending

# Define a custom admin class for Comment
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'content', 'created_at', 'parent')  # List columns for comments
    search_fields = ('content',)  # Enable search by comment content
    list_filter = ('created_at',)  # Filter comments by creation date

# Register the models with custom admin classes
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
