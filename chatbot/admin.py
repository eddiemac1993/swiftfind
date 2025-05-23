from django.contrib import admin
from .models import UserQuery

@admin.register(UserQuery)
class UserQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'intent', 'user', 'timestamp', 'ip_address')
    list_filter = ('intent', 'timestamp')
    search_fields = ('query', 'response', 'user__username')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    fieldsets = (
        (None, {
            'fields': ('query', 'response', 'intent', 'entities')
        }),
        ('User Information', {
            'fields': ('user', 'session_key', 'ip_address', 'timestamp')
        }),
    )