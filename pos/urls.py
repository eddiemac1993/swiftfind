from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logouts/', views.custom_logout, name='logouts'),
    path('products/add/', views.add_product, name='add_product'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('view-cart/', views.view_cart, name='view_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('process-sale/', views.process_sale, name='process_sale'),
    path('receipt/<int:order_id>/', views.receipt, name='receipt'),
    path('receipt/<int:order_id>/pdf/', views.receipt_pdf, name='receipt_pdf'),
]