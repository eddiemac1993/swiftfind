from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="analytics_dashboard"),
    path('dashboard/export-csv/', views.export_dashboard_csv, name='export_dashboard_csv'),
    path("user-growth/", views.user_growth, name="user_growth"),
    path("business-growth/", views.business_members_growth, name="business_growth"),
    path("top-referrers/", views.top_referrers, name="top_referrers"),
]
