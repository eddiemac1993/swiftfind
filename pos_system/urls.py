from django.urls import path
from . import views

app_name = 'pos_system'

urlpatterns = [
    # Main views
    path('', views.dashboard, name='dashboard'),
    path('store/', views.public_store_all, name='public_store_all'),
    path('store/<slug:business_slug>/', views.public_store, name='public_store'),
    path('pos/', views.pos_view, name='pos'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('reports/', views.reports_view, name='reports'),
    path('sales-report/', views.sales_report, name='sales_report'),

    # Product management
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),

    # Category management
    path('categories/', views.category_list, name='category_list'),
    path('add-category/', views.add_category, name='add_category'),
    path('edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('delete-category/<int:category_id>/', views.confirm_delete_category, name='confirm_delete_category'),

    # AJAX endpoints
    path('ajax/search-products/', views.search_products, name='search_products'),
    path('ajax/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('ajax/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('ajax/process-sale/', views.process_sale, name='process_sale'),
    path('ajax/get-cart/', views.get_cart, name='get_cart'),
    path('ajax/update-cart-item/', views.update_cart_item, name='update_cart_item'),
]