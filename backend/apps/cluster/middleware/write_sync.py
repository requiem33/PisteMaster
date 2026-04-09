import logging
import threading
from typing import Callable, Optional

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from backend.apps.cluster.models.cluster_config import DjangoClusterConfig
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
        """Load cluster configuration from database."""
        try:
            config = DjangoClusterConfig.get_config()
            self.mode = config.mode
            self.is_master = config.is_master
            self.master_url = config.master_url
            self.replica_ack_required = config.replica_ack_required
            self.ack_timeout_ms = config.ack_timeout_ms
        except Exception:
            self.mode = "single"
            self.is_master = False
            self.master_url = None
            self.replica_ack_required = 1
            self.ack_timeout_ms = 5000

        sync_manager.ack_queue.set_nodes_required(self.replica_ack_required)

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Pre-process incoming requests."""
        self._load_config()

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
        self._load_config()

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

        self._notify_followers(sync_log_id)

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
        """Handle write request on follower node by proxying to master."""
        if self.master_url:
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
        """Wait for ACKs from followers using threading.Event."""
        event = sync_manager.ack_queue.register(sync_log_id, self.replica_ack_required)

        confirmed = event.wait(timeout=self.ack_timeout_ms / 1000.0)

        if confirmed:
            return True

        if sync_manager.ack_queue.is_confirmed(sync_log_id):
            return True

        logger.warning(
            f"ACK timeout for sync_log_id={sync_log_id}, "
            f"confirmed={len(sync_manager.ack_queue.get_confirmed_nodes(sync_log_id))}, "
            f"required={self.replica_ack_required}"
        )
        return False

    def _notify_followers(self, sync_log_id: int) -> None:
        """Notify followers of a new sync_log entry via HTTP POST (fire-and-forget)."""
        from backend.apps.cluster.models.sync_log import DjangoSyncLog
        from backend.apps.cluster.models.sync_state import DjangoSyncState
        from backend.apps.cluster.services.proxy import get_follower_proxy

        try:
            sync_log = DjangoSyncLog.objects.get(id=sync_log_id)
        except DjangoSyncLog.DoesNotExist:
            logger.warning(f"SyncLog {sync_log_id} not found, skipping follower notification")
            return

        follower_states = DjangoSyncState.objects.exclude(url__isnull=True).exclude(url="")
        follower_urls = [state.url for state in follower_states]

        if not follower_urls:
            logger.debug("No follower URLs registered, skipping notification")
            return

        proxy = get_follower_proxy()

        def _send():
            proxy.broadcast_sync(follower_urls, sync_log_id, sync_log.table_name, sync_log.record_id)

        thread = threading.Thread(target=_send, daemon=True, name="notify-followers")
        thread.start()


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
