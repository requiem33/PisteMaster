import logging
from typing import Optional

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from backend.apps.cluster.models.cluster_config import DjangoClusterConfig
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
    - POST/PUT/DELETE/PATCH: Proxied to master

    When a proxied request arrives at the master (identified by the
    X-Cluster-Proxy header), CSRF validation is skipped because the
    follower already validated the original request and both nodes
    share the same trusted origin configuration.

    This middleware should be placed before SyncWriteMiddleware
    in the MIDDLEWARE configuration.
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
        try:
            config = DjangoClusterConfig.get_config()
            self.mode = config.mode
            self.is_master = config.is_master
            self.master_url = config.master_url
            self._is_cluster_mode = self.mode == "cluster"
            self._is_follower = self._is_cluster_mode and not self.is_master
        except Exception:
            self.mode = "single"
            self.is_master = False
            self.master_url = None
            self._is_cluster_mode = False
            self._is_follower = False

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        self._load_config()

        if self._is_cluster_mode and request.META.get("HTTP_X_CLUSTER_PROXY") == "follower":
            setattr(request, "_dont_enforce_csrf_checks", True)

        if not self._is_cluster_mode:
            return None

        request.cluster_mode = self.mode
        request.is_master = self.is_master
        request.is_follower = self._is_follower
        request.master_url = self.master_url

        if self._is_exempt_path(request.path):
            return None

        if request.method in self.WRITE_METHODS and self._is_follower:
            if self.master_url:
                return self._handle_follower_write(request)
            logger.warning("Follower node has no master_url configured, rejecting write")
            return self._create_readonly_response()

        return None

    def _is_exempt_path(self, path: str) -> bool:
        for exempt in self.SYNC_EXEMPT_PATHS:
            if path.startswith(exempt):
                return True
        return False

    def _handle_follower_write(self, request: HttpRequest) -> HttpResponse:
        if not self.master_url:
            logger.error("Follower write but master_url not configured")
            return self._create_readonly_response()

        proxy = get_master_proxy()

        retry_count = 3
        retry_delay = 1.0

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
    """Simplified middleware that only sets node role context on the request."""

    def __init__(self, get_response):
        self.get_response = get_response
        self._load_config()

    def _load_config(self) -> None:
        try:
            config = DjangoClusterConfig.get_config()
            self.mode = config.mode
            self.is_master = config.is_master
        except Exception:
            self.mode = "single"
            self.is_master = False

    def process_request(self, request: HttpRequest) -> None:
        self._load_config()
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
