# cv_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.template_selection, name='template_selection'),
    path('create/<int:template_id>/', views.create_cv, name='create_cv'),
    path('preview/<int:cv_id>/', views.preview_cv, name='preview_cv'),
    path('download/<int:cv_id>/', views.download_cv, name='download_cv'),
]