from django.urls import path
from . import views

urlpatterns = [
    path('', views.business_list, name='business-list'),
    path('about/', views.about, name='about'),
    path('business/add/', views.add_business, name='add-business'),
    path('<int:pk>/', views.business_detail, name='business-detail'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('business/<int:business_id>/upload-image/', views.upload_business_image, name='upload_business_image'),
]