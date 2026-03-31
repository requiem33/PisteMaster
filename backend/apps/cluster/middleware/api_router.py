import logging
from typing import Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from backend.apps.cluster.services.proxy import get_master_proxy

logger = logging.getLogger(__name__)


class ApiRouterMiddleware(MiddlewareMixin):
    """
    API Router Middleware for cluster mode.

    Routes requests based on node role (master/follower):

    Master Node:
    - All requests processed locally
    - Write operations are replicated to followers

    Follower Node:
    - GET requests: Processed locally (read-only)
    - POST/PUT/DELETE/PATCH: Either rejected (503) or proxied to master

    This middleware should be placed before SyncWriteMiddleware
    in the MIDDLEWARE configuration.

    Configuration (in settings.py):
        MIDDLEWARE = [
            ...
            'backend.apps.cluster.middleware.api_router.ApiRouterMiddleware',
            'backend.apps.cluster.middleware.write_sync.SyncWriteMiddleware',
            ...
        ]

        CLUSTER_CONFIG = {
            'mode': 'single' or 'cluster',
            'is_master': False,
            'master_url': 'http://192.168.1.100:8000',
            'proxy_writes': True,  # IfTrue, proxy writes to master
            'proxy_timeout': 10,   # Timeout for proxy requests
        }
    """

    SYNC_EXEMPT_PATHS = [
        "/api/sync/",
        "/api/cluster/",
        "/admin/",
        "/static/",
        "/media/",
        "/swagger/",
        "/redoc/",
        "/__debug__/",
    ]

    WRITE_METHODS = ["POST", "PUT", "DELETE", "PATCH"]

    def __init__(self, get_response):
        self.get_response = get_response
        self._load_config()

    def _load_config(self) -> None:
        config = getattr(settings, "CLUSTER_CONFIG", {})

        self.mode = config.get("mode", "single")
        self.is_master = config.get("is_master", False)
        self.master_url = config.get("master_url")
        self.proxy_writes = config.get("proxy_writes", False)
        self.proxy_timeout = config.get("proxy_timeout", 10)

        self._is_cluster_mode = self.mode == "cluster"
        self._is_follower = self._is_cluster_mode and not self.is_master

        logger.info(f"ApiRouterMiddleware initialized: mode={self.mode}, " f"is_master={self.is_master}, proxy_writes={self.proxy_writes}")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        if not self._is_cluster_mode:
            return None

        request.cluster_mode = self.mode
        request.is_master = self.is_master
        request.is_follower = self._is_follower
        request.master_url = self.master_url

        if self._is_exempt_path(request.path):
            return None

        if request.method in self.WRITE_METHODS and self._is_follower:
            return self._handle_follower_write(request)

        return None

    def _is_exempt_path(self, path: str) -> bool:
        for exempt in self.SYNC_EXEMPT_PATHS:
            if path.startswith(exempt):
                return True
        return False

    def _handle_follower_write(self, request: HttpRequest) -> HttpResponse:
        if not self.proxy_writes:
            return self._create_readonly_response()

        if not self.master_url:
            logger.error("Proxy writes enabled but master_url not configured")
            return self._create_readonly_response()

        proxy = get_master_proxy()

        retry_count = getattr(settings, "PROXY_RETRY_COUNT", 3)
        retry_delay = getattr(settings, "PROXY_RETRY_DELAY", 1.0)

        response = proxy.forward_with_retry(
            request=request,
            retry_count=retry_count,
            retry_delay=retry_delay,
        )

        return response

    def _create_readonly_response(self) -> JsonResponse:
        return JsonResponse(
            {
                "detail": "This node is a read-only follower. Direct write requests to the master node.",
                "error_code": "READONLY_FOLLOWER",
                "is_master": False,
                "mode": self.mode,
            },
            status=503,
        )


class NodeRoleMiddleware(MiddlewareMixin):
    """
    Simplified middleware that only sets node role context on the request.

    Use this when you want role information available but don't need
    the full routing logic.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._load_config()

    def _load_config(self) -> None:
        config = getattr(settings, "CLUSTER_CONFIG", {})
        self.mode = config.get("mode", "single")
        self.is_master = config.get("is_master", False)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_request(self, request: HttpRequest) -> None:
        request.cluster_mode = self.mode
        request.is_master = self.is_master
        request.is_follower = self.mode == "cluster" and not self.is_master


def get_node_role(request: HttpRequest) -> dict:
    """
    Utility function to get node role information from request.

    Returns:
        dict with keys: mode, is_master, is_follower
    """
    return {
        "mode": getattr(request, "cluster_mode", "single"),
        "is_master": getattr(request, "is_master", False),
        "is_follower": getattr(request, "is_follower", False),
    }


def is_master_node(request: HttpRequest) -> bool:
    """Check ifcurrent node is master."""
    return getattr(request, "is_master", True)


def is_follower_node(request: HttpRequest) -> bool:
    """Check if current node is follower."""
    return getattr(request, "is_follower", False)
