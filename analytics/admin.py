from django.contrib import admin
from django.contrib.sessions.models import Session
from django.db.models import Q
from .models import PageVisit
from django.contrib.admin.sites import NotRegistered

@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ('visitor_info', 'path', 'method', 'ip_address', 'timestamp', 'is_authenticated')
    list_filter = ('method', 'timestamp', 'is_authenticated', 'user')
    search_fields = ('path', 'user__username', 'ip_address', 'session__session_key')
    readonly_fields = ('visitor_info', 'path', 'method', 'ip_address', 'referrer', 
                      'user_agent', 'timestamp', 'is_authenticated')
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Exclude common static/media files and admin assets
        return qs.exclude(
            Q(path__startswith='/static/') |
            Q(path__startswith='/media/') |
            Q(path__contains='.css') |
            Q(path__contains='.js') |
            Q(path__contains='.png') |
            Q(path__contains='.jpg') |
            Q(path__contains='.jpeg') |
            Q(path__contains='.gif') |
            Q(path__contains='.ico') |
            Q(path__startswith='/admin/')  # Exclude admin page views if desired
        )
    
    def visitor_info(self, obj):
        if obj.user:
            return f"User: {obj.user.username}"
        elif obj.session:
            return f"Anonymous: {obj.session.session_key[:8]}..."
        return "Unknown visitor"
    visitor_info.short_description = 'Visitor'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

# Unregister Session admin safely
try:
    admin.site.unregister(Session)
except NotRegistered:
    pass

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'user', 'session_data_short', 'expire_date')
    list_filter = ('expire_date',)
    search_fields = ('session_key',)
    
    def user(self, obj):
        if '_auth_user_id' in obj.get_decoded():
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                return User.objects.get(pk=obj.get_decoded()['_auth_user_id'])
            except User.DoesNotExist:
                return "Unknown user"
        return None
    
    def session_data_short(self, obj):
        decoded = obj.get_decoded()
        return str({k: v for k, v in decoded.items() if not k.startswith('_')})
    session_data_short.short_description = 'Session Data'