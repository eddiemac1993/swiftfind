from django.contrib import admin
from .models import Guest

class GuestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'slug', 'created_at')  # Customize this as needed
    search_fields = ('name', 'phone_number')  # Allow searching by name or phone number
    prepopulated_fields = {'slug': ('name',)}  # Automatically generate slug from name
    list_filter = ('created_at',)  # Optional: Add filter by creation date
    
    # Optionally, customize how the form looks when adding/editing a guest
    fieldsets = (
        (None, {
            'fields': ('name', 'phone_number', 'slug', 'created_at')
        }),
    )
    
    # Make slug field read-only since it's prepopulated
    readonly_fields = ('slug',)

admin.site.register(Guest, GuestAdmin)
