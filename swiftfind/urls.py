from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('directory/', include('directory.urls')),
    path('paper/', include('paper.urls')),
    path('pos/', include('pos.urls')),
    path('posts/', include('posts.urls')),
    path('', include('order.urls')),
    path('bot/', include('chatbot.urls')),
    path('taxi/', include('taxi.urls')),
    path('tracking/', include('tracking.urls')),
    path('accounts/', include('django.contrib.auth.urls')),

    # Redirect /4/ to /directory/4/
    re_path(r'^(?P<pk>\d+)/$', RedirectView.as_view(pattern_name='business-detail', permanent=True)),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
