from django.urls import path
from . import views

app_name = 'pos_system'

urlpatterns = [
    # Main views
    path('', views.dashboard, name='dashboard'),
    path('marketplace/', views.marketplace_view, name='marketplace'),
    path('store/', views.public_store_all, name='public_store_all'),
    path('orders/<int:order_id>/submit/', views.submit_order, name='submit_order'),
    path('orders/', views.customer_orders, name='customer_orders'),
    path('business/orders/', views.business_orders, name='business_orders'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('orders/<int:order_id>/update/<str:status>/', views.direct_status_update, name='direct_status_update'),
    path('api/orders/create/', views.create_order, name='create_order'),
    path('orders/<int:order_id>/', views.order_details, name='order_details'),
    path('store/<slug:business_slug>/', views.public_store, name='public_store'),
    path('pos/', views.pos_view, name='pos'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/product-performance/', views.product_performance_report, name='product_performance_report'),
    path('reports/sale/<int:sale_id>/', views.sale_detail, name='sale_detail'),
    path('reports/print-receipt/<int:sale_id>/', views.print_receipt, name='print_receipt'),

    path('track-view/<int:product_id>/', views.track_product_view, name='track_product_view'),
    path('analytics/', views.product_analytics, name='product_analytics'),
    path('claim-rewards/', views.claim_rewards, name='claim_rewards'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

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
    path('sale/<int:sale_id>/', views.sale_detail, name='sale_detail'),
]