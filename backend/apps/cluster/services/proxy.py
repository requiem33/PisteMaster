import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    host: str
    port: int
    timeout: int = 10
    retry_count: int = 3
    retry_delay: float = 1.0


class MasterProxy:
    """
    Proxy service for forwarding write requests from follower to master node.

    This service handles:
    1. Forwarding write requests (POST/PUT/DELETE/PATCH) to master
    2. Retrying on transient failures
    3. Timeout handling
    4. Response transformation

    Usage:
        proxy = MasterProxy(master_url="http://192.168.1.100:8000")
        response = proxy.forward_request(request)
    """

    EXCLUDED_HEADERS = {
        "HTTP_HOST",
        "HTTP_CONTENT_LENGTH",
        "HTTP_TRANSFER_ENCODING",
        "HTTP_CONNECTION",
    }

    WRITE_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

    def __init__(self, master_url: Optional[str] = None, timeout: int = 10):
        self.master_url = master_url
        self.timeout = timeout
        self._session: Optional[requests.Session] = None

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({"X-Cluster-Proxy": "follower"})
        return self._session

    def forward_request(self, request: HttpRequest) -> HttpResponse:
        if not self.master_url:
            return JsonResponse(
                {"detail": "Master URL not configured", "error_code": "MASTER_NOT_CONFIGURED"},
                status=503,
            )

        if request.method not in self.WRITE_METHODS:
            return JsonResponse(
                {"detail": "Only write requests can be proxied", "error_code": "INVALID_METHOD"},
                status=400,
            )

        url = self._build_target_url(request.path, request.META.get("QUERY_STRING", ""))

        headers = self._extract_headers(request)

        body = self._get_request_body(request)

        try:
            response = self.session.request(
                method=request.method,
                url=url,
                headers=headers,
                data=body,
                timeout=self.timeout,
                allow_redirects=False,
            )

            return self._transform_response(response)

        except requests.Timeout:
            logger.error(f"Proxy request timed out: {url}")
            return JsonResponse(
                {"detail": "Master node timeout", "error_code": "MASTER_TIMEOUT"},
                status=504,
            )

        except requests.ConnectionError as e:
            logger.error(f"Proxy connection error: {e}")
            return JsonResponse(
                {"detail": "Cannot connect to master node", "error_code": "MASTER_UNREACHABLE"},
                status=503,
            )

        except requests.RequestException as e:
            logger.error(f"Proxy request failed: {e}")
            return JsonResponse(
                {"detail": f"Proxy request failed: {str(e)}", "error_code": "PROXY_ERROR"},
                status=502,
            )

    def forward_with_retry(
        self,
        request: HttpRequest,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ) -> HttpResponse:
        import time

        last_error_response = None

        for attempt in range(retry_count):
            response = self.forward_request(request)

            if response.status_code < 500:
                return response

            if response.status_code in (502, 503, 504):
                last_error_response = response
                if attempt < retry_count - 1:
                    time.sleep(retry_delay * (attempt + 1))
                continue

            return response

        return last_error_response or JsonResponse(
            {"detail": "All retry attempts failed", "error_code": "RETRY_EXHAUSTED"},
            status=503,
        )

    def _build_target_url(self, path: str, query_string: str) -> str:
        base = self.master_url.rstrip("/")
        full_path = path
        if query_string:
            full_path = f"{path}?{query_string}"
        return f"{base}{full_path}"

    def _extract_headers(self, request: HttpRequest) -> Dict[str, str]:
        headers = {}

        for key, value in request.META.items():
            if key.startswith("HTTP_") and key not in self.EXCLUDED_HEADERS:
                header_name = key[5:].replace("_", "-")
                headers[header_name] = value

        if request.META.get("CONTENT_TYPE"):
            headers["Content-Type"] = request.META["CONTENT_TYPE"]

        if request.META.get("CONTENT_LENGTH"):
            headers["Content-Length"] = request.META["CONTENT_LENGTH"]

        return headers

    def _get_request_body(self, request: HttpRequest) -> bytes:
        return request.body

    def _transform_response(self, response: requests.Response) -> HttpResponse:
        excluded_headers = {"Transfer-Encoding", "Connection"}

        headers = {}
        for key, value in response.headers.items():
            if key not in excluded_headers:
                headers[key] = value

        return HttpResponse(
            content=response.content,
            status=response.status_code,
            headers=headers,
        )


class FollowerProxy:
    """
    Proxy for master to coordinate with followers.

    This service handles:
    1. Broadcasting sync changes to followers
    2. Collecting ACKs from followers
    3. Managing follower health status
    """

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self._session: Optional[requests.Session] = None

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({"X-Cluster-Source": "master"})
        return self._session

    def broadcast_sync(self, follower_urls: list, sync_log_id: int, table_name: str, record_id: str) -> Dict[str, Any]:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {
            "sync_log_id": sync_log_id,
            "total_followers": len(follower_urls),
            "successful": [],
            "failed": [],
        }

        with ThreadPoolExecutor(max_workers=min(len(follower_urls), 10)) as executor:
            future_to_url = {
                executor.submit(self._send_sync_notification, url, sync_log_id, table_name, record_id): url for url in follower_urls
            }

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success = future.result()
                    if success:
                        results["successful"].append(url)
                    else:
                        results["failed"].append({"url": url, "reason": "sync_failed"})
                except Exception as e:
                    results["failed"].append({"url": url, "reason": str(e)})

        return results

    def _send_sync_notification(self, follower_url: str, sync_log_id: int, table_name: str, record_id: str) -> bool:
        url = f"{follower_url.rstrip('/')}/api/sync/notify"

        payload = {
            "sync_log_id": sync_log_id,
            "table_name": table_name,
            "record_id": record_id,
        }

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            return response.status_code == 200

        except requests.RequestException as e:
            logger.warning(f"Failed to notify follower {follower_url}: {e}")
            return False

    def check_follower_health(self, follower_url: str) -> Dict[str, Any]:
        url = f"{follower_url.rstrip('/')}/api/cluster/health"

        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return {
                    "url": follower_url,
                    "healthy": True,
                    "node_id": data.get("node_id"),
                    "last_sync_id": data.get("last_sync_id"),
                }
            return {
                "url": follower_url,
                "healthy": False,
                "reason": f"HTTP {response.status_code}",
            }

        except requests.RequestException as e:
            return {
                "url": follower_url,
                "healthy": False,
                "reason": str(e),
            }


master_proxy: Optional[MasterProxy] = None
follower_proxy: Optional[FollowerProxy] = None


def get_master_proxy() -> MasterProxy:
    global master_proxy
    if master_proxy is None:
        config = getattr(settings, "CLUSTER_CONFIG", {})
        master_url = config.get("master_url")
        timeout = config.get("proxy_timeout", 10)
        master_proxy = MasterProxy(master_url=master_url, timeout=timeout)
    return master_proxy


def get_follower_proxy() -> FollowerProxy:
    global follower_proxy
    if follower_proxy is None:
        config = getattr(settings, "CLUSTER_CONFIG", {})
        timeout = config.get("proxy_timeout", 5)
        follower_proxy = FollowerProxy(timeout=timeout)
    return follower_proxy


def reset_proxies():
    global master_proxy, follower_proxy
    master_proxy = None
    follower_proxy = None
