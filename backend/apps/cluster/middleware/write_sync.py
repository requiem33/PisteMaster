import asyncio
import logging
from typing import Callable, Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from backend.apps.cluster.services.sync_manager import sync_manager

logger = logging.getLogger(__name__)


class SyncWriteMiddleware(MiddlewareMixin):
    """
    Middleware for handling synchronous write operations in cluster mode.

    When running as master node:
    1. Intercepts write requests (POST, PUT, DELETE)
    2. After the view completes, waits for ACKs from followers
    3. Returns response only after confirmation (or timeout)

    When running as follower node:
    1. Rejects or proxies write requests to master

    Configuration (in settings):
        CLUSTER_CONFIG = {
            'mode': 'single' or 'cluster',  # default: 'single'
            'is_master': False,             # default: False
            'master_url': None,             # URL of master node
            'replica_ack_required': 1,      # minimum ACKs required
            'ack_timeout_ms': 5000,         # timeout for ACK wait
        }
    """

    SYNC_EXEMPT_PATHS = [
        "/api/sync/",
        "/api/cluster/",
        "/admin/",
        "/static/",
        "/media/",
    ]

    WRITE_METHODS = ["POST", "PUT", "DELETE", "PATCH"]

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self._load_config()

    def _load_config(self) -> None:
        """Load cluster configuration from Django settings."""
        config = getattr(settings, "CLUSTER_CONFIG", {})

        self.mode = config.get("mode", "single")
        self.is_master = config.get("is_master", False)
        self.master_url = config.get("master_url")
        self.replica_ack_required = config.get("replica_ack_required", 1)
        self.ack_timeout_ms = config.get("ack_timeout_ms", 5000)

        sync_manager.ack_queue.set_nodes_required(self.replica_ack_required)

        logger.info(
            f"SyncWriteMiddleware initialized: mode={self.mode}, " f"is_master={self.is_master}, ack_required={self.replica_ack_required}"
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Pre-process incoming requests."""
        if self.mode == "single":
            return None
        if self._is_exempt_path(request.path):
            return None

        if request.method in self.WRITE_METHODS:
            if not self.is_master:
                return self._handle_follower_write(request)

        return None

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Post-process response after view execution."""
        if self.mode == "single":
            return response

        if not self.is_master:
            return response

        if request.method not in self.WRITE_METHODS:
            return response

        if self._is_exempt_path(request.path):
            return response

        if response.status_code >= 400:
            return response

        sync_log_id = getattr(request, "_sync_log_id", None)
        if sync_log_id is None:
            return response

        confirmed = self._wait_for_acks(sync_log_id)

        if confirmed:
            logger.debug(f"Write confirmed: sync_log_id={sync_log_id}")
            return response
        else:
            logger.warning(f"Write partial: sync_log_id={sync_log_id}, waiting for ACKs timed out")
            return JsonResponse(
                {
                    "detail": "Write accepted but replication pending",
                    "sync_log_id": sync_log_id,
                    "confirmed": False,
                },
                status=202,
            )

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from sync handling."""
        for exempt in self.SYNC_EXEMPT_PATHS:
            if path.startswith(exempt):
                return True
        return False

    def _handle_follower_write(self, request: HttpRequest) -> HttpResponse:
        """Handle write request on follower node."""
        proxy_enabled = getattr(settings, "PROXY_WRITES_TO_MASTER", False)

        if proxy_enabled and self.master_url:
            return self._proxy_to_master(request)

        return JsonResponse(
            {"detail": "This node is read-only. Writes must be sent to master.", "is_master": False},
            status=503,
        )

    def _proxy_to_master(self, request: HttpRequest) -> HttpResponse:
        """Proxy write request to master node."""
        import requests

        if not self.master_url:
            return JsonResponse(
                {"detail": "Master URL not configured"},
                status=503,
            )

        try:
            url = f"{self.master_url.rstrip('/')}{request.path}"

            headers = {}
            for key, value in request.META.items():
                if key.startswith("HTTP_") and key != "HTTP_HOST":
                    headers[key[5:].replace("_", "-")] = value

            body = request.body

            response = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=body,
                timeout=10,
                allow_redirects=False,
            )

            return HttpResponse(
                content=response.content,
                status=response.status_code,
                content_type=response.headers.get("Content-Type", "application/json"),
            )

        except requests.RequestException as e:
            logger.error(f"Failed to proxy request to master: {e}")
            return JsonResponse(
                {"detail": "Failed to communicate with master node"},
                status=503,
            )

    def _wait_for_acks(self, sync_log_id: int) -> bool:
        """Wait for ACKs from followers."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                event = sync_manager.ack_queue.register(sync_log_id, self.replica_ack_required)

                future = asyncio.wait_for(event.wait(), timeout=self.ack_timeout_ms / 1000.0)

                loop.run_until_complete(future)
                return True

            except asyncio.TimeoutError:
                confirmed_nodes = sync_manager.ack_queue.get_confirmed_nodes(sync_log_id)
                logger.warning(
                    f"ACK timeout for sync_log_id={sync_log_id}, " f"confirmed={len(confirmed_nodes)}, required={self.replica_ack_required}"
                )
                return len(confirmed_nodes) >= self.replica_ack_required

            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Error waiting for ACKs: {e}")
            return False


class ClusterModeMiddleware(MiddlewareMixin):
    """
    Middleware for setting cluster context on requests.

    Adds the following attributes to request:
    - cluster_mode: 'single' or 'cluster'
    - is_master: bool
    - is_follower: bool
    """

    def __init__(self, get_response: Callable):
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
