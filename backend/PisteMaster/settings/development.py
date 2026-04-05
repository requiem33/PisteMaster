"""
Development settings for PisteMaster project.

SQLite database, debug mode enabled.
Usage: DJANGO_SETTINGS_MODULE=PisteMaster.settings.development
"""

import os

from .base import *  # noqa: F403

DEBUG = True

SECRET_KEY = "django-insecure-@wzj3@2ga2hwhu)*-^*%qx_g$$r@!60%j7h%_*_+o5vs7x9&lk"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "testserver",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH", str(BASE_DIR / "db.sqlite3")),  # noqa: F405
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = [  # noqa: F405
    "rest_framework.permissions.AllowAny",
]
