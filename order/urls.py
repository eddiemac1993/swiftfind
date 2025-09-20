from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('sw.js', views.service_worker),
    path('api/push-subscribe/', views.save_push_subscription, name='save-push-subscription'),
    path('save-subscription/', views.save_subscription, name='save-subscription'),

    path('todos/', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('<int:pk>/', views.task_detail, name='task_detail'),
    path('<int:pk>/update/', views.task_update, name='task_update'),
    path('<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('<int:pk>/toggle-complete/', views.task_toggle_complete, name='task_toggle_complete'),
    path('games/', views.games_hub, name='games_hub'),
    path('matchmemory/', views.match_memory_view, name='word_craze'),
    path('nsolo/', views.nsolo_game, name='nsolo'),
    path('quiz/', views.quiz_view, name='quiz'),
    path('submit-score/', views.submit_score_view, name='submit_score'),
    path('games/mobile/', views.mobile_view, name='mobile'),
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('', views.discover, name='discover'),
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('generate-quotation/', views.generate_quotation, name='generate_quotation'),
    path('accounts/password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('accounts/password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('accounts/reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]