from django.urls import path
from . import views

urlpatterns = [
    path('create-paper/', views.create_paper, name='create_paper'),
    path('paper/<int:paper_id>/', views.view_paper, name='view_paper'),
    path('paper/<int:paper_id>/add-items/', views.add_items, name='add_items'),
    path('item/<int:item_id>/edit/', views.edit_item, name='edit_item'),
    path('item/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('paper/<int:paper_id>/download/', views.download_paper, name='download_paper'),
]