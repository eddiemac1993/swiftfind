from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('directory/', include('directory.urls')),
    path('paper/', include('paper.urls')),
    path('pos/', include('pos.urls')),
    path('posts/', include('posts.urls')),
    path('', include('order.urls')),

    path('accounts/', include('django.contrib.auth.urls')),

]
# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
