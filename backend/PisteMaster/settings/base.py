"""
Base Django settings for PisteMaster project.

Common settings shared across all environments.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TRUE_BASE_DIR = BASE_DIR.parent
sys.path.insert(0, str(TRUE_BASE_DIR))

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "backend.apps.users.apps.UsersConfig",
    "backend.apps.fencing_organizer.apps.ApiConfig",
    "backend.apps.cluster.apps.ClusterConfig",
    "rest_framework",
    "django_filters",
]

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "PisteMaster.urls"

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

WSGI_APPLICATION = "PisteMaster.wsgi.application"

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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "backend.apps.fencing_organizer.authentication.CsrfExemptSessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "TEST_REQUEST_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

CORS_ALLOW_CREDENTIALS = True

CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"

CLUSTER_CONFIG = {
    "mode": os.environ.get("CLUSTER_MODE", "single"),
    "udp_port": int(os.environ.get("CLUSTER_UDP_PORT", 9000)),
    "api_port": int(os.environ.get("CLUSTER_API_PORT", 8000)),
    "node_id": os.environ.get("NODE_ID"),
    "heartbeat_interval": float(os.environ.get("CLUSTER_HEARTBEAT_INTERVAL", "5.0")),
    "heartbeat_timeout": float(os.environ.get("CLUSTER_HEARTBEAT_TIMEOUT", "15.0")),
    "election_timeout": float(os.environ.get("CLUSTER_ELECTION_TIMEOUT", "10.0")),
    "node_expiry_timeout": float(os.environ.get("CLUSTER_NODE_EXPIRY_TIMEOUT", "30.0")),
    "replica_ack_required": int(os.environ.get("CLUSTER_REPLICA_ACK", "1")),
    "ack_timeout_ms": int(os.environ.get("CLUSTER_ACK_TIMEOUT", "5000")),
    "is_master": False,
    "master_url": None,
    "proxy_writes": os.environ.get("CLUSTER_PROXY_WRITES", "true").lower() == "true",
}
