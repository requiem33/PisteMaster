"""
Settings module __init__.py.

This module provides Django settings for different environments.
The default is development settings for backward compatibility.
"""

from PisteMaster.settings.development import *

__all__ = [
    "BASE_DIR",
    "TRUE_BASE_DIR",
    "SECRET_KEY",
    "DEBUG",
    "ALLOWED_HOSTS",
    "INSTALLED_APPS",
    "MIDDLEWARE",
    "ROOT_URLCONF",
    "TEMPLATES",
    "WSGI_APPLICATION",
    "DATABASES",
    "AUTH_PASSWORD_VALIDATORS",
    "LANGUAGE_CODE",
    "TIME_ZONE",
    "USE_I18N",
    "USE_TZ",
    "STATIC_URL",
    "DEFAULT_AUTO_FIELD",
    "REST_FRAMEWORK",
    "CORS_ALLOWED_ORIGINS",
    "CSRF_TRUSTED_ORIGINS",
    "CORS_ALLOW_CREDENTIALS",
]