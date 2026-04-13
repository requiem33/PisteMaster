"""
Desktop settings for PisteMaster project.

SQLite database in user data directory, for bundled Electron app.
Usage: DJANGO_SETTINGS_MODULE=PisteMaster.settings.desktop
"""

import os
import sys
from pathlib import Path
from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = "django-insecure-desktop-key-change-in-production-build"


def get_desktop_db_path() -> Path:
    """Get platform-specific user data directory for SQLite database."""
    app_name = "PisteMaster"

    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"

    data_dir = base / app_name / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "pistemaster.db"


ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": get_desktop_db_path(),
    }
}

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "file://",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
]

REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = [  # noqa: F405
    "rest_framework.permissions.AllowAny",
]
