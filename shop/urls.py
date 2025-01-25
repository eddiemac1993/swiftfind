from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Item List URLs
    path('items/', views.item_list, name='item_list'),
    path('items/<slug:category_slug>/', views.item_list, name='item_list_by_category'),

    # Cart URLs
    path('cart/', views.view_cart, name='view_cart'),
    path('add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Request URLs
    path('view-request/', views.view_request, name='view_request'),
    path('download-request-pdf/', views.download_request_pdf, name='download_request_pdf'),
    path('create-request/', views.create_request, name='create_request'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),

    # Payment URLs
    path('make-payment/<int:request_id>/', views.make_payment, name='make_payment'),
    path('profile/', views.profile, name='profile'),
]