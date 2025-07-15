from django.urls import path
from .views import chat
urlpatterns = [
    path('chat/', chat, name='chat'),
    path('chat/api/', chat, name='chat_api'),
]
