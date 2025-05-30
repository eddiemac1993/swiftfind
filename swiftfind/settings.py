"""
Django settings for swiftfind project.

Generated by 'django-admin startproject' using Django 5.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-=udh)je!ql09a_n0_g353ixb6qc=g+8y#$kgysq&yo7zj#bvxn"

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the API key
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["swiftfindzm.com", "www.swiftfindzm.com", '*']

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'directory',
    'chatbot',
    'taggit',
    'imagekit',
    'paper',
    'django.contrib.humanize',
    'analytics',
    'pos',
    'posts',
    'order',
    'taxi',
    'tracking',
    'import_export',
    'django_admin_listfilter_dropdown',
    'rangefilter',
]

# settings.py
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Full',
        'height': 300,
        'width': '100%',
    },
}

# Specify the ASGI application
ASGI_APPLICATION = 'swiftfind.asgi.application'

# Configure channel layers (for development, use in-memory layer)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    'analytics.middleware.PageVisitMiddleware',
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

ROOT_URLCONF = "swiftfind.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "swiftfind.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Lusaka"

USE_I18N = True

USE_TZ = True


import os

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'  # URL prefix for static files
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # Additional directories for static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Directory for collected static files
# Media files (User-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Where media files are stored

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# settings.py

LOGIN_URL = 'login'  # This should match the name of the login URL
# Redirect to this URL after login
LOGIN_REDIRECT_URL = '/'

# Redirect to this URL after logout
LOGOUT_REDIRECT_URL = 'login'  # Redirect to the login page after logout
