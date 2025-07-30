from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.conversation_list, name='conversation_list'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),  # Changed from UUID to int
    path('start/<int:business_id>/', views.start_conversation, name='start_conversation'),
    path('unread_count/', views.unread_count, name='unread_count'),
    path('mark_read/', views.mark_notifications_read, name='mark_notifications_read'),
]