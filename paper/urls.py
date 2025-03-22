from django.urls import path
from . import views

urlpatterns = [
    path('create-paper/', views.create_paper, name='create_paper'),
    path('add_guest/', views.add_guest, name='add_guest'),
    path('qrcode/<slug:slug>/', views.guest_qr_code, name='guest_qr_code'),
    path('guests/', views.guest_list, name='guest_list'),
    path('guest/edit/<slug:slug>/', views.edit_guest, name='edit_guest'),
    path('guest/delete/<slug:slug>/', views.delete_guest, name='delete_guest'),
    path('guest_invitation/<slug:slug>/', views.guest_invitation, name='guest_invitation'),
    path('paper/<int:paper_id>/add-items/', views.add_items, name='add_items'),
    path('item/<int:item_id>/edit/', views.edit_item, name='edit_item'),
    path('item/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('paper/<int:paper_id>/download/', views.download_paper, name='download_paper'),
]