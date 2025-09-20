# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add_animal/', views.add_animal, name='add_animal'),
    path('manage_equipment/', views.manage_equipment, name='manage_equipment'),
    path('add_equipment/', views.add_equipment, name='add_equipment'),
    path('edit_equipment/<int:pk>/', views.edit_equipment, name='edit_equipment'),
    path('delete_equipment/<int:pk>/', views.delete_equipment, name='delete_equipment'),
    path('stock_management/', views.stock_management, name='stock_management'),
    path('add_stock_item/', views.add_stock_item, name='add_stock_item'),
    path('edit_stock_item/<int:pk>/', views.edit_stock_item, name='edit_stock_item'),
    path('delete_stock_item/<int:pk>/', views.delete_stock_item, name='delete_stock_item'),
    path('manage_employees/', views.manage_employees, name='manage_employees'),
    path('add_employee/', views.add_employee, name='add_employee'),
    path('edit_employee/<int:pk>/', views.edit_employee, name='edit_employee'),
    path('delete_employee/<int:pk>/', views.delete_employee, name='delete_employee'),
]