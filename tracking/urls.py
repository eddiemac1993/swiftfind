from django.urls import path
from . import views

urlpatterns = [
    path('track/', views.track_order, name='order_tracking'),
]
