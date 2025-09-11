from django.contrib import admin
from django.urls import path, include, re_path, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from pos_system.views import order_details
urlpatterns = [
    path('admin/', admin.site.urls),
    path('webpush/', include('webpush.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('directory/', include('directory.urls')),
    path('paper/', include('paper.urls')),
    path('pos/', include('pos.urls')),
    path('pos1/', include('pos_system.urls')),
    path('orders/<int:order_id>/', order_details, name='order_details_root'),
    path('posts/', include('posts.urls')),
    path('', include('order.urls')),
    path('bot/', include('chatbot.urls')),
    path('taxi/', include('taxi.urls')),
    path('tracking/', include('tracking.urls')),
    path('messages/', include('messaging.urls')),
    path('cv/', include('cv_app.urls')),
    path("analytics/", include("analytics.urls")),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done')
        ),
        name='password_reset'
    ),
    path('accounts/password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete')
        ),
        name='password_reset_confirm'),
    path('accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'),

    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'images/favicon.ico')),
    path('robots.txt', RedirectView.as_view(url=settings.STATIC_URL + 'robots.txt'), name='robots'),
    # Redirect /4/ to /directory/4/
    re_path(r'^(?P<pk>\d+)/$', RedirectView.as_view(pattern_name='business-detail', permanent=True)),
]
# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)