from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),

    # Business-specific URLs
    path('business/<slug:business_slug>/', views.business_dashboard, name='business_dashboard'),
    path('business/<slug:business_slug>/login/', views.business_login, name='business_login'),
    path('business/<slug:business_slug>/members/add/', views.add_business_member, name='add_business_member'),
    path('business/<slug:business_slug>/roles/', views.manage_roles, name='manage_roles'),
    path('business/<slug:business_slug>/departments/', views.manage_departments, name='manage_departments'),

    path('business/<int:pk>/post/add/', views.add_business_post, name='add-business-post'),
    path('business/post/<int:pk>/edit/', views.edit_business_post, name='edit-business-post'),
    path('business/post/<int:pk>/delete/', views.delete_business_post, name='delete-business-post'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('', views.business_list, name='business-list'),
    path('newsfeed/', views.newsfeed_list, name='newsfeed-list'),
    path('newsfeed/<int:pk>/', views.newsfeed_detail, name='newsfeed_detail'),
    path('become-partner/', views.become_partner, name='become-partner'),
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