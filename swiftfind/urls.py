from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from swiftfind.embedded_urls import urlpatterns as embedded_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    *embedded_urlpatterns,
]
# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
