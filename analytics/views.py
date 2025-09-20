from django.contrib.auth.models import User
from django.db.models.functions import TruncDate
from django.db.models import Count
from django.http import JsonResponse
from directory.models import BusinessMember, Referral
from django.db.models import Count, Case, When, IntegerField, F
import csv
from django.http import HttpResponse
from .models import PageVisit

from django.db.models import Count
import csv
from django.http import HttpResponse
from directory.models import Referral  # or wherever Referral is located
from .models import PageVisit

def export_dashboard_csv(request):
    # Create HTTP response with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dashboard_data.csv"'

    writer = csv.writer(response)

    # Write Referrers Data
    writer.writerow(['Top Referrers'])
    writer.writerow(['Referrer', 'Total Referrals', 'Conversions', 'Conversion Rate (%)'])

    # Annotate with total referrals count and calculate conversions
    referrers = Referral.objects.values(
        'referrer__username'
    ).annotate(
        total=Count('id'),
        conversions=Count(Case(When(is_paid=True, then=1), output_field=IntegerField()))
    ).order_by('-total')[:50]  # top 50

    for r in referrers:
        rate = (r['conversions'] / r['total'] * 100) if r['total'] else 0
        writer.writerow([
            r['referrer__username'] if r['referrer__username'] else 'Anonymous',
            r['total'],
            r['conversions'],
            f'{rate:.2f}'
        ])

    writer.writerow([])  # empty line

    # Write Page Visits - AGGREGATE BY PATH
    writer.writerow(['Top Pages'])
    writer.writerow(['Page', 'Total Visits', 'Unique Visitors'])

    # Aggregate page visits by path
    pages = PageVisit.objects.values('path').annotate(
        total_visits=Count('id'),
        unique_visitors=Count('ip_address', distinct=True)
    ).order_by('-total_visits')[:50]  # top 50

    for p in pages:
        writer.writerow([p['path'], p['total_visits'], p['unique_visitors']])

    return response


def user_growth(request):
    data = (
        User.objects.annotate(join_date=TruncDate("date_joined"))
        .values("join_date")
        .annotate(count=Count("id"))
        .order_by("join_date")
    )
    return JsonResponse(list(data), safe=False)


def business_members_growth(request):
    data = (
        BusinessMember.objects.annotate(join_date=TruncDate("date_joined"))
        .values("join_date")
        .annotate(count=Count("id"))
        .order_by("join_date")
    )
    return JsonResponse(list(data), safe=False)


def top_referrers(request):
    data = (
        Referral.objects.values("referrer__username")
        .annotate(total=Count("referred_user"))
        .order_by("-total")[:10]
    )
    return JsonResponse(list(data), safe=False)

from django.shortcuts import render

def dashboard(request):
    return render(request, "analytics/dashboard.html")
