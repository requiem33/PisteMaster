"""
Django settings entry point for PisteMaster project.

This file loads settings from the appropriate settings module
based on the DJANGO_SETTINGS_MODULE environment variable.

For development, the default is development settings (SQLite).
For production, set DJANGO_SETTINGS_MODULE=PisteMaster.settings.production
For desktop/Electron, set DJANGO_SETTINGS_MODULE=PisteMaster.settings.desktop

Usage:
    # Development (default)
    python manage.py runserver

    # Production
    DJANGO_SETTINGS_MODULE=PisteMaster.settings.production python manage.py runserver

    # Desktop
    DJANGO_SETTINGS_MODULE=PisteMaster.settings.desktop python manage.py runserver
"""

import os
import warnings

settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "PisteMaster.settings.development")

try:
    module = __import__(settings_module, fromlist=[""])
    globals().update({k: v for k, v in module.__dict__.items() if not k.startswith("_")})
except ImportError as e:
    warnings.warn(f"Could not import settings module '{settings_module}': {e}")
    from PisteMaster.settings.development import *