from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("requests/", views.requests_list, name="requests_list"),
    path("schools/", views.schools_list, name="schools_list"),
    path("suppliers/", views.suppliers_list, name="suppliers_list"),
    path("catalogue/", views.product_catalogue, name="product_catalogue"),
    path("requests/new/", views.procurement_request_create, name="request_create"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("quotations/new/", views.quotation_create, name="quotation_create"),
    path("quotations/<int:pk>/edit/", views.quotation_edit, name="quotation_edit"),
    path("quotations/compare/<int:pk>/", views.compare_quotations, name="compare_quotations"),
    path("quotations/select/<int:pk>/", views.select_quotation, name="select_quotation"),
    path("purchase-orders/upload/", views.purchase_order_upload, name="purchase_order_upload"),
    path("purchase-orders/<int:pk>/confirm/", views.confirm_purchase_order, name="confirm_purchase_order"),
    path("delivery-notes/", views.delivery_note_page, name="delivery_note_page"),
    path("goods-received/", views.goods_received_page, name="goods_received_page"),
    path("invoices/", views.invoice_page, name="invoice_page"),
    path("payments/", views.payment_tracking_page, name="payment_tracking_page"),
    path("reports/", views.reports_page, name="reports_page"),
    path("reports/export/<str:export_type>/", views.reports_export, name="reports_export"),
    path("approvals/<int:pk>/", views.approval_update, name="approval_update"),
    path("settings/document-numbers/", views.document_number_settings, name="document_number_settings"),
    path("manual/", views.user_manual_page, name="user_manual_page"),
    path("noticeboard/", views.noticeboard_page, name="noticeboard_page"),
    path("messages/", views.messages_page, name="messages_page"),
    path("messages/new/", views.message_create, name="message_create"),
    path("messages/<int:pk>/", views.message_detail, name="message_detail"),
    path("pdf/<str:document_type>/<int:pk>/", views.document_pdf, name="document_pdf"),
]
