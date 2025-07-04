from django.contrib import admin
from django.contrib.sessions.models import Session
from django.db.models import Q
from .models import PageVisit
from django.contrib.admin.sites import NotRegistered
from django.utils.html import format_html

@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = (
        'visitor_info', 
        'path', 
        'device_type_display', 
        'browser_display', 
        'os_display',
        'method', 
        'ip_address', 
        'timestamp', 
        'is_authenticated'
    )
    list_filter = (
        'method', 
        'timestamp', 
        'is_authenticated', 
        'user',
    )
    search_fields = (
        'path', 
        'user__username', 
        'ip_address', 
        'session__session_key',
        'user_agent'
    )
    readonly_fields = (
        'visitor_info', 
        'path', 
        'method', 
        'ip_address', 
        'referrer',
        'user_agent', 
        'timestamp', 
        'is_authenticated',
        'device_details'
    )
    date_hierarchy = 'timestamp'
    list_per_page = 50

    def device_type_display(self, obj):
        info = obj.device_info
        if info['is_bot']:
            return format_html('<span style="color: #ff6b6b;">🤖 Bot</span>')
        elif info['is_mobile']:
            return format_html('<span style="color: #4ecdc4;">📱 Mobile</span>')
        elif info['is_tablet']:
            return format_html('<span style="color: #45aaf2;">⌨️ Tablet</span>')
        elif info['is_pc']:
            return format_html('<span style="color: #a55eea;">💻 Desktop</span>')
        return format_html('<span>❓ Unknown</span>')
    device_type_display.short_description = 'Device'

    def browser_display(self, obj):
        info = obj.device_info
        browser = info['browser']
        if 'Chrome' in browser:
            return format_html('<span style="color: #feca57;">🟡 {}</span>', browser)
        elif 'Firefox' in browser:
            return format_html('<span style="color: #ff9ff3;">🦊 {}</span>', browser)
        elif 'Safari' in browser:
            return format_html('<span style="color: #1dd1a1;">🟦 {}</span>', browser)
        elif 'Edge' in browser:
            return format_html('<span style="color: #54a0ff;">🔵 {}</span>', browser)
        return format_html('<span>🌐 {}</span>', browser)
    browser_display.short_description = 'Browser'

    def os_display(self, obj):
        info = obj.device_info
        os = info['os']
        if 'Windows' in os:
            return format_html('<span style="color: #2e86de;">🪟 {}</span>', os)
        elif 'Mac' in os or 'iOS' in os:
            return format_html('<span style="color: #26de81;">🍏 {}</span>', os)
        elif 'Android' in os:
            return format_html('<span style="color: #10ac84;">🤖 {}</span>', os)
        elif 'Linux' in os:
            return format_html('<span style="color: #f368e0;">🐧 {}</span>', os)
        return format_html('<span>💻 {}</span>', os)
    os_display.short_description = 'OS'

    def device_details(self, obj):
        info = obj.device_info
        details = [
            f"<strong>Device:</strong> {info['device']}",
            f"<strong>OS:</strong> {info['os']}",
            f"<strong>Browser:</strong> {info['browser']}",
            f"<strong>Type:</strong> {'Bot' if info['is_bot'] else 'Mobile' if info['is_mobile'] else 'Tablet' if info['is_tablet'] else 'Desktop'}",
            f"<strong>User Agent:</strong> {obj.user_agent}",
        ]
        return format_html('<br>'.join(details))
    device_details.short_description = 'Device Details'

    def visitor_info(self, obj):
        if obj.user:
            return format_html(
                '<span style="color: #2ecc71;">👤 User: {}</span>', 
                obj.user.username
            )
        elif obj.session:
            return format_html(
                '<span style="color: #3498db;">👤 Anonymous: {}...</span>', 
                obj.session.session_key[:8]
            )
        return format_html(
            '<span style="color: #e74c3c;">👤 Unknown visitor</span>'
        )
    visitor_info.short_description = 'Visitor'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(
            Q(path__startswith='/static/') |
            Q(path__startswith='/media/') |
            Q(path__startswith='/admin/')
        )

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
    readonly_fields = ('session_key', 'session_data', 'expire_date')

    def user(self, obj):
        if '_auth_user_id' in obj.get_decoded():
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(pk=obj.get_decoded()['_auth_user_id'])
                return format_html(
                    '<a href="/admin/{}/{}/{}/change/">{}</a>',
                    user._meta.app_label,
                    user._meta.model_name,
                    user.pk,
                    user.username
                )
            except User.DoesNotExist:
                return "Unknown user"
        return None

    def session_data_short(self, obj):
        decoded = obj.get_decoded()
        return format_html(
            '<pre style="max-height: 100px; overflow: auto;">{}</pre>',
            str({k: v for k, v in decoded.items() if not k.startswith('_')})
        )
    session_data_short.short_description = 'Session Data'