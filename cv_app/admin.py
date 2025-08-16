# cv_app/admin.py
from django.contrib import admin
from .models import CVTemplate, CV

admin.site.register(CVTemplate)
admin.site.register(CV)