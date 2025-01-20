from django.urls import path
from . import views

urlpatterns = [
    path('', views.business_list, name='business-list'),
    path('about/', views.about, name='about'),
    path('offline/', views.offline, name='offline'),
    path('business/add/', views.add_business, name='add-business'),
    path('<int:pk>/', views.business_detail, name='business-detail'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('business/<int:business_id>/upload-image/', views.upload_business_image, name='upload_business_image'),

    path('chat/', views.chat_room_list, name='chat_room_list'),
    path('chat/create/', views.create_chat_room, name='create_chat_room'),
    path('chat/<int:room_id>/', views.chat_room_detail, name='chat_room_detail'),
    path('chat/<int:room_id>/send/', views.send_message, name='send_message'),
]