from django.contrib import admin
from django.contrib.sessions.models import Session
from django.contrib.admin.sites import NotRegistered
from django.db import models
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth, TruncDay, TruncHour
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from django.contrib.admin.views.decorators import staff_member_required
import json
from datetime import timedelta
import csv

from .models import PageVisit
from directory.models import Referral

User = get_user_model()

# --- Device parser ---
def get_device_info_from_user_agent(user_agent):
    if not user_agent:
        return {'is_bot': False, 'is_mobile': False, 'is_tablet': False,
                'is_pc': False, 'device': 'Unknown', 'os': 'Unknown', 'browser': 'Unknown'}

    user_agent = user_agent.lower()
    is_bot = any(bot in user_agent for bot in ['bot', 'crawler', 'spider', 'googlebot'])
    is_mobile = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipod'])
    is_tablet = any(tablet in user_agent for tablet in ['tablet', 'ipad'])
    is_pc = not (is_bot or is_mobile or is_tablet)

    os = 'Unknown'
    if 'windows' in user_agent: os = 'Windows'
    elif 'mac' in user_agent: os = 'Mac OS'
    elif 'linux' in user_agent: os = 'Linux'
    elif 'android' in user_agent: os = 'Android'
    elif 'ios' in user_agent: os = 'iOS'

    browser = 'Unknown'
    if 'chrome' in user_agent and 'edg' not in user_agent: browser = 'Chrome'
    elif 'firefox' in user_agent: browser = 'Firefox'
    elif 'safari' in user_agent and 'chrome' not in user_agent: browser = 'Safari'
    elif 'edg' in user_agent: browser = 'Edge'
    elif 'opera' in user_agent: browser = 'Opera'

    return {
        'is_bot': is_bot, 'is_mobile': is_mobile, 'is_tablet': is_tablet, 'is_pc': is_pc,
        'device': 'Bot' if is_bot else 'Mobile' if is_mobile else 'Tablet' if is_tablet else 'Desktop',
        'os': os, 'browser': browser
    }

# --- Analytics Dashboard ---
@staff_member_required
def analytics_dashboard(request):
    cache_key = f"analytics_dashboard_{timezone.now().strftime('%Y-%m-%d')}"
    cached_data = cache.get(cache_key)

    if cached_data and not request.GET.get('refresh'):
        context = {**admin.site.each_context(request), 'title': "📊 Advanced Analytics Dashboard", **cached_data}
    else:
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)

        # --- User Analytics ---
        monthly_users = (
            User.objects.annotate(month=TruncMonth('date_joined'))
            .values('month').annotate(count=Count('id')).order_by('month')[:12]
        )

        daily_registrations = (
            User.objects.filter(date_joined__date__gte=thirty_days_ago)
            .annotate(day=TruncDay('date_joined'))
            .values('day').annotate(count=Count('id')).order_by('day')
        )

        cumulative_users = (
            User.objects.annotate(day=TruncDay('date_joined'))
            .values('day').annotate(count=Count('id')).order_by('day')
        )
        total = 0
        cumulative_users_data = []
        cumulative_users_labels = []
        cumulative_users_values = []
        for entry in cumulative_users:
            total += entry["count"]
            cumulative_users_data.append({"day": entry["day"].strftime("%Y-%m-%d"), "total_users": total})
            cumulative_users_labels.append(entry["day"].strftime("%Y-%m-%d"))
            cumulative_users_values.append(total)

        # --- User Demographics ---
        total_users = User.objects.count()
        users_with_business = User.objects.filter(
            Q(owned_businesses__isnull=False) |
            Q(business_memberships__isnull=False)
        ).distinct().count()
        users_without_business = total_users - users_with_business
        business_owners = User.objects.filter(owned_businesses__isnull=False).distinct().count()

        # Active users in last 30 days
        active_users_30_days = User.objects.filter(
            Q(last_login__gte=thirty_days_ago) |
            Q(date_joined__gte=thirty_days_ago)
        ).distinct().count()

        # --- Traffic Analytics ---
        daily_visits = (
            PageVisit.objects.filter(timestamp__date__gte=thirty_days_ago)
            .annotate(day=TruncDay('timestamp'))
            .values('day').annotate(visits=Count('id')).order_by('day')
        )

        total_visits_today = PageVisit.objects.filter(timestamp__date=today).count()
        unique_visitors_today = PageVisit.objects.filter(timestamp__date=today).values('session').distinct().count()

        # --- Top Metrics ---
        top_referrers = (
            Referral.objects.values('referrer__username')
            .annotate(total=Count('id'), conversions=Count('id', filter=Q(referred_user__isnull=False)))
            .order_by('-total')[:10]
        )
        top_pages = (
            PageVisit.objects.exclude(Q(path__startswith='/static/') | Q(path__startswith='/media/') | Q(path__startswith='/admin/'))
            .values('path').annotate(visits=Count('id'), unique_visitors=Count('session', distinct=True))
            .order_by('-visits')[:10]
        )

        # --- Device Analytics ---
        device_stats = PageVisit.objects.values('user_agent').annotate(count=Count('id')).order_by('-count')[:1000]
        device_breakdown = {'mobile': 0, 'desktop': 0, 'tablet': 0, 'bot': 0, 'unknown': 0}
        for visit in device_stats:
            info = get_device_info_from_user_agent(visit['user_agent'])
            if info['is_bot']: device_breakdown['bot'] += visit['count']
            elif info['is_mobile']: device_breakdown['mobile'] += visit['count']
            elif info['is_tablet']: device_breakdown['tablet'] += visit['count']
            elif info['is_pc']: device_breakdown['desktop'] += visit['count']
            else: device_breakdown['unknown'] += visit['count']

        cacheable_data = {
            'monthly_labels': [u['month'].strftime('%b %Y') for u in monthly_users],
            'monthly_counts': [u['count'] for u in monthly_users],
            'daily_labels': [v['day'].strftime('%b %d') for v in daily_visits],
            'daily_counts': [v['visits'] for v in daily_visits],
            'daily_registrations': list(daily_registrations),
            'cumulative_users': cumulative_users_data,
            'cumulative_users_labels': cumulative_users_labels,
            'cumulative_users_data': cumulative_users_values,
            'top_referrers': list(top_referrers),
            'top_pages': list(top_pages),
            'total_visits_today': total_visits_today,
            'unique_visitors_today': unique_visitors_today,
            'device_breakdown': device_breakdown,
            'active_users': User.objects.filter(is_active=True).count(),
            'total_referrals': Referral.objects.count(),
            'successful_referrals': Referral.objects.filter(referred_user__isnull=False).count(),
            'user_stats': {
                'total_users': total_users,
                'users_with_business': users_with_business,
                'users_without_business': users_without_business,
                'business_owners': business_owners,
                'active_users_30_days': active_users_30_days,
            },
        }
        cache.set(cache_key, cacheable_data, timeout=3600)

        context = {**admin.site.each_context(request), 'title': "📊 Advanced Analytics Dashboard", **cacheable_data}

    return TemplateResponse(request, "analytics/dashboard.html", context)

# --- API for AJAX charts ---
@staff_member_required
def analytics_api(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    daily_visits = (
        PageVisit.objects.filter(timestamp__date__gte=thirty_days_ago)
        .annotate(day=TruncDay('timestamp')).values('day')
        .annotate(count=Count('id')).order_by('day')
    )
    daily_registrations = (
        User.objects.filter(date_joined__date__gte=thirty_days_ago)
        .annotate(day=TruncDay('date_joined')).values('day')
        .annotate(count=Count('id')).order_by('day')
    )
    cumulative_users = (
        User.objects.annotate(day=TruncDay('date_joined'))
        .values('day').annotate(count=Count('id')).order_by('day')
    )
    total = 0
    cumulative_users_data = []
    for entry in cumulative_users:
        total += entry["count"]
        cumulative_users_data.append({"day": entry["day"].strftime("%Y-%m-%d"), "total_users": total})

    return JsonResponse({
        "daily_visits": [{"day": d["day"].strftime("%Y-%m-%d"), "visits": d["count"]} for d in daily_visits],
        "daily_registrations": [{"day": r["day"].strftime("%Y-%m-%d"), "registrations": r["count"]} for r in daily_registrations],
        "cumulative_users": cumulative_users_data,
    })

# --- CSV Export ---
@staff_member_required
def analytics_export(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    monthly_users = (
        User.objects.annotate(month=TruncMonth('date_joined'))
        .values('month').annotate(count=Count('id')).order_by('month')[:12]
    )
    daily_visits = (
        PageVisit.objects.filter(timestamp__date__gte=thirty_days_ago)
        .annotate(day=TruncDay('timestamp')).values('day')
        .annotate(visits=Count('id')).order_by('day')
    )
    daily_registrations = (
        User.objects.filter(date_joined__date__gte=thirty_days_ago)
        .annotate(day=TruncDay('date_joined')).values('day')
        .annotate(count=Count('id')).order_by('day')
    )
    cumulative_users = (
        User.objects.annotate(day=TruncDay('date_joined'))
        .values('day').annotate(count=Count('id')).order_by('day')
    )
    total = 0
    cumulative_users_data = []
    for entry in cumulative_users:
        total += entry["count"]
        cumulative_users_data.append({"day": entry["day"].strftime("%Y-%m-%d"), "total_users": total})

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="analytics_export.csv"'
    writer = csv.writer(response)

    # Monthly Users
    writer.writerow(["--- Monthly New Users ---"])
    writer.writerow(["Month", "Users"])
    for row in monthly_users:
        writer.writerow([row["month"].strftime("%Y-%m"), row["count"]])
    writer.writerow([])

    # Daily Visits
    writer.writerow(["--- Daily Visits (Last 30 Days) ---"])
    writer.writerow(["Date", "Visits"])
    for row in daily_visits:
        writer.writerow([row["day"].strftime("%Y-%m-%d"), row["visits"]])
    writer.writerow([])

    # Daily Registrations
    writer.writerow(["--- Daily User Registrations (Last 30 Days) ---"])
    writer.writerow(["Date", "Registrations"])
    for row in daily_registrations:
        writer.writerow([row["day"].strftime("%Y-%m-%d"), row["count"]])
    writer.writerow([])

    # Cumulative Users
    writer.writerow(["--- Cumulative User Growth (All Time) ---"])
    writer.writerow(["Date", "Total Users"])
    for row in cumulative_users_data:
        writer.writerow([row["day"], row["total_users"]])
    writer.writerow([])

    return response

# --- Sidebar link ---
class AnalyticsDashboardLink(models.Model):
    class Meta:
        verbose_name = "📊 Analytics Dashboard"
        verbose_name_plural = "📊 Analytics Dashboard"
        managed = False

class AnalyticsDashboardAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('api/', self.admin_site.admin_view(analytics_api), name='analytics_api'),
            path('export/', self.admin_site.admin_view(analytics_export), name='analytics_export'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None): return analytics_dashboard(request)
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

admin.site.register(AnalyticsDashboardLink, AnalyticsDashboardAdmin)
# --- Enhanced PageVisit admin ---
@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = (
        'visitor_info',
        'path_display',
        'device_type_display',
        'browser_display',
        'os_display',
        'method_badge',
        'ip_address',
        'timestamp_short',
        'is_authenticated_badge'
    )
    list_filter = (
        'method',
        'timestamp',
        'is_authenticated',
        'user',
        ('timestamp', admin.DateFieldListFilter),
    )
    search_fields = (
        'path', 'user__username', 'user__email',
        'ip_address', 'session__session_key', 'user_agent'
    )
    readonly_fields = (
        'visitor_info', 'path', 'method', 'ip_address', 'referrer',
        'user_agent', 'timestamp', 'is_authenticated', 'device_details',
        'session_info', 'geo_info'
    )
    date_hierarchy = 'timestamp'
    list_per_page = 25
    list_select_related = ('user', 'session')
    show_full_result_count = False
    actions = ['export_as_csv', 'mark_as_reviewed']

    fieldsets = (
        ('Visit Information', {
            'fields': ('timestamp', 'path', 'method', 'ip_address', 'referrer')
        }),
        ('Visitor Information', {
            'fields': ('visitor_info', 'is_authenticated', 'session_info', 'geo_info')
        }),
        ('Technical Details', {
            'fields': ('user_agent', 'device_details')
        }),
    )

    def path_display(self, obj):
        shortened = obj.path[:50] + '...' if len(obj.path) > 50 else obj.path
        return format_html('<code>{}</code>', shortened)
    path_display.short_description = 'Path'
    path_display.admin_order_field = 'path'

    def method_badge(self, obj):
        colors = {
            'GET': 'blue', 'POST': 'green', 'PUT': 'orange',
            'DELETE': 'red', 'PATCH': 'purple'
        }
        color = colors.get(obj.method, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.method
        )
    method_badge.short_description = 'Method'

    def is_authenticated_badge(self, obj):
        if obj.is_authenticated:
            return format_html(
                '<span style="background: #10ac84; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">✓ Authenticated</span>'
            )
        return format_html(
            '<span style="background: #ff6b6b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Anonymous</span>'
        )
    is_authenticated_badge.short_description = 'Auth'

    def timestamp_short(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M')
    timestamp_short.short_description = 'Timestamp'
    timestamp_short.admin_order_field = 'timestamp'

    def device_type_display(self, obj):
        info = get_device_info_from_user_agent(obj.user_agent)
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
        info = get_device_info_from_user_agent(obj.user_agent)
        browser = info['browser']
        colors = {'Chrome':'#feca57','Firefox':'#ff9ff3','Safari':'#1dd1a1','Edge':'#54a0ff','Opera':'#ff6b6b'}
        emoji = {'Chrome':'🟡','Firefox':'🦊','Safari':'🟦','Edge':'🔵','Opera':'🔴'}
        for b, color in colors.items():
            if b in browser:
                return format_html('<span style="color: {};">{} {}</span>', color, emoji.get(b, '🌐'), browser)
        return format_html('<span>🌐 {}</span>', browser)
    browser_display.short_description = 'Browser'

    def os_display(self, obj):
        info = get_device_info_from_user_agent(obj.user_agent)
        os = info['os']
        if 'Windows' in os: return format_html('<span style="color: #2e86de;">🪟 {}</span>', os)
        elif 'Mac' in os or 'iOS' in os: return format_html('<span style="color: #26de81;">🍏 {}</span>', os)
        elif 'Android' in os: return format_html('<span style="color: #10ac84;">🤖 {}</span>', os)
        elif 'Linux' in os: return format_html('<span style="color: #f368e0;">🐧 {}</span>', os)
        return format_html('<span>💻 {}</span>', os)
    os_display.short_description = 'OS'

    def device_details(self, obj):
        info = get_device_info_from_user_agent(obj.user_agent)
        details = [
            f"<strong>Device:</strong> {info['device']}",
            f"<strong>OS:</strong> {info['os']}",
            f"<strong>Browser:</strong> {info['browser']}",
            f"<strong>Type:</strong> {'Bot' if info['is_bot'] else 'Mobile' if info['is_mobile'] else 'Tablet' if info['is_tablet'] else 'Desktop'}",
            f"<strong>User Agent:</strong> {obj.user_agent}",
        ]
        return format_html('<br>'.join(details))
    device_details.short_description = 'Device Details'

    def session_info(self, obj):
        if obj.session:
            decoded = obj.session.get_decoded()
            session_data = {k: v for k, v in decoded.items() if not k.startswith('_')}
            return format_html(
                '<strong>Session Key:</strong> {}<br><strong>Data:</strong> <pre style="max-height: 100px; overflow: auto;">{}</pre>',
                obj.session.session_key[:15] + '...',
                json.dumps(session_data, indent=2)
            )
        return "No session"
    session_info.short_description = 'Session Information'

    def geo_info(self, obj):
        # Placeholder for future geoIP integration
        return "GeoIP data not configured"
    geo_info.short_description = 'Geolocation'

    def visitor_info(self, obj):
        if obj.user:
            return format_html(
                '<span style="color: #2ecc71;">👤 User: {}</span><br><small>{}</small>',
                obj.user.username, obj.user.email
            )
        elif obj.session:
            return format_html(
                '<span style="color: #3498db;">👤 Anonymous: {}...</span>',
                obj.session.session_key[:8]
            )
        return format_html('<span style="color: #e74c3c;">👤 Unknown visitor</span>')
    visitor_info.short_description = 'Visitor'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'session').exclude(
            Q(path__startswith='/static/') |
            Q(path__startswith='/media/') |
            Q(path__startswith='/admin/')
        )

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta}_export.csv'

        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response
    export_as_csv.short_description = "Export selected as CSV"

    def mark_as_reviewed(self, request, queryset):
        # Placeholder for future functionality
        self.message_user(request, f"{queryset.count()} visits marked as reviewed")
    mark_as_reviewed.short_description = "Mark as reviewed"

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False

# --- Enhanced Session admin ---
try:
    admin.site.unregister(Session)
except NotRegistered:
    pass

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('session_key_short', 'user', 'session_data_preview', 'expire_date', 'is_active')
    list_filter = ('expire_date',)
    search_fields = ('session_key',)
    readonly_fields = ('session_key', 'session_data', 'expire_date', 'user_info')
    list_per_page = 50

    def session_key_short(self, obj):
        return obj.session_key[:15] + '...' if len(obj.session_key) > 15 else obj.session_key
    session_key_short.short_description = 'Session Key'

    def session_data_preview(self, obj):
        decoded = obj.get_decoded()
        preview_data = {k: v for k, v in decoded.items() if not k.startswith('_')}
        return format_html('<pre style="max-height: 50px; overflow: hidden; font-size: 10px;">{}</pre>',
                           json.dumps(preview_data)[:100] + '...')
    session_data_preview.short_description = 'Session Data'

    def user_info(self, obj):
        return self.user(obj)
    user_info.short_description = 'User Information'

    def is_active(self, obj):
        return obj.expire_date > timezone.now()
    is_active.boolean = True
    is_active.short_description = 'Active'

    def user(self, obj):
        if '_auth_user_id' in obj.get_decoded():
            try:
                user = User.objects.get(pk=obj.get_decoded()['_auth_user_id'])
                return format_html(
                    '<a href="/admin/{}/{}/{}/change/">{}</a><br><small>{}</small>',
                    user._meta.app_label, user._meta.model_name, user.pk,
                    user.username, user.email
                )
            except User.DoesNotExist:
                return "User deleted"
        return "Anonymous"