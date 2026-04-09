import logging
import socket
import threading
from typing import Optional

import requests

from backend.apps.cluster.models.cluster_config import DjangoClusterConfig
from backend.apps.cluster.services.sync_manager import sync_manager, SyncChange

logger = logging.getLogger(__name__)


def _get_own_url() -> str:
    """Derive this node's own HTTP URL from api_port and local IP."""
    try:
        config = DjangoClusterConfig.get_config()
        api_port = config.api_port or 8000
    except Exception:
        api_port = 8000

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"

    return f"http://{ip}:{api_port}"


SKIP_FIELDS = {"id", "created_at", "updated_at", "last_modified_at"}


class SyncWorker:
    """Background sync thread running on follower nodes.

    Pulls incremental/full changes from the master node and applies them
    to the local database. Also sends ACKs back to the master.

    The worker is started from ClusterConfig.ready() only when the node
    is in cluster mode and is NOT the master.
    """

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._sync_event = threading.Event()
        self._sync_interval = 3.0
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start the sync worker if this node is a cluster follower."""
        try:
            config = DjangoClusterConfig.get_config()
        except Exception:
            logger.debug("SyncWorker: cluster config not available, skipping start")
            return

        if config.mode != "cluster" or config.is_master:
            logger.info("SyncWorker: not starting (mode=%s, is_master=%s)", config.mode, config.is_master)
            return

        if self.is_running:
            logger.info("SyncWorker: already running")
            return

        self._running = True
        self._stop_event.clear()
        self._sync_event.clear()
        self._thread = threading.Thread(target=self._sync_loop, daemon=True, name="sync-worker")
        self._thread.start()
        logger.info("SyncWorker: started (node_id=%s, master_url=%s)", config.node_id, config.master_url)

        self._announce_to_master(config)

    def stop(self) -> None:
        """Stop the background sync thread."""
        logger.info("SyncWorker: stopping")
        self._stop_event.set()
        self._sync_event.set()
        if self._thread:
            self._thread.join(timeout=10)
        self._running = False
        self._thread = None
        logger.info("SyncWorker: stopped")

    def trigger_immediate_sync(self) -> None:
        """Called by /sync/notify/ endpoint to trigger immediate pull."""
        self._sync_event.set()

    def _sync_loop(self) -> None:
        """Main sync loop: pull changes from master, apply, ACK."""
        logger.info("SyncWorker: entering sync loop")

        while not self._stop_event.is_set():
            try:
                self._do_sync_cycle()
            except Exception as e:
                logger.error("SyncWorker: sync cycle error: %s", e)

            self._sync_event.wait(timeout=self._sync_interval)
            self._sync_event.clear()

        logger.info("SyncWorker: exiting sync loop")

    def _do_sync_cycle(self) -> None:
        """One iteration of the sync loop."""
        try:
            config = DjangoClusterConfig.get_config()
        except Exception:
            return

        if config.mode != "cluster" or config.is_master or not config.master_url:
            if config.is_master and self._running:
                logger.info("SyncWorker: node promoted to master, stopping worker")
                self._running = False
                self._stop_event.set()
            return

        master_url = config.master_url
        node_id = config.node_id
        self._sync_interval = config.sync_interval

        sync_state = sync_manager.get_sync_state(node_id)
        last_synced_id = sync_state.last_synced_id if sync_state else 0

        self._do_incremental_sync(master_url, node_id, last_synced_id)

    def _do_incremental_sync(self, master_url: str, node_id: str, last_synced_id: int) -> None:
        """Pull and apply incremental changes from master."""
        try:
            response = requests.get(
                f"{master_url.rstrip('/')}/api/cluster/sync/changes/",
                params={"since": last_synced_id, "limit": 100},
                timeout=10,
            )
        except requests.RequestException as e:
            logger.error("SyncWorker: incremental sync request failed: %s", e)
            return

        if response.status_code != 200:
            logger.error("SyncWorker: incremental sync failed: HTTP %d", response.status_code)
            return

        data = response.json()
        changes = data.get("changes", [])
        has_more = data.get("has_more", False)
        master_latest_id = data.get("last_id", 0)

        if not changes:
            if master_latest_id > 0:
                sync_manager.update_sync_state(node_id, last_synced_id, master_latest_sync_id=master_latest_id)
            return

        sync_changes = []
        for c in changes:
            try:
                sync_changes.append(
                    SyncChange(
                        id=c["id"],
                        table_name=c["table_name"],
                        record_id=c["record_id"],
                        operation=c["operation"],
                        data=c["data"],
                        version=c.get("version", 1),
                        created_at=c.get("created_at"),
                    )
                )
            except (KeyError, TypeError) as e:
                logger.warning("SyncWorker: skipping malformed change: %s", e)

        if not sync_changes:
            return

        results = sync_manager.apply_changes_batch(sync_changes)

        last_success_id = results.get("last_success_id", 0)

        if last_success_id > 0:
            sync_manager.update_sync_state(node_id, last_success_id, master_latest_sync_id=master_latest_id)
            self._send_ack(master_url, node_id, last_success_id)
        else:
            logger.warning(
                "SyncWorker: no changes applied successfully out of %d, " "not advancing sync state",
                len(sync_changes),
            )

        logger.info(
            "SyncWorker: incremental sync applied %d/%d changes (last_success_id=%d)",
            results["success"],
            len(sync_changes),
            last_success_id,
        )

        if has_more:
            self._sync_event.set()

    def _do_full_sync(self, master_url: str, node_id: str) -> None:
        """Initial full sync when node has no sync state (last_synced_id == 0)."""
        logger.info("SyncWorker: starting full sync from %s", master_url)

        try:
            response = requests.get(
                f"{master_url.rstrip('/')}/api/cluster/sync/full/",
                params={"page": 1, "page_size": 1000},
                timeout=30,
            )
        except requests.RequestException as e:
            logger.error("SyncWorker: full sync request failed: %s", e)
            return

        if response.status_code != 200:
            logger.error("SyncWorker: full sync failed: HTTP %d", response.status_code)
            return

        data = response.json()
        latest_sync_id = data.get("latest_sync_id", 0)

        for table_name, records in data.get("data", {}).items():
            if table_name not in sync_manager._model_registry:
                logger.warning("SyncWorker: skipping unknown table '%s' in full sync", table_name)
                continue

            model_class = sync_manager._model_registry[table_name].model_class
            for record in records:
                try:
                    defaults = {k: v for k, v in record.items() if k not in SKIP_FIELDS}
                    model_class.objects.update_or_create(id=record["id"], defaults=defaults)
                except Exception as e:
                    logger.error("SyncWorker: failed to import record %s/%s: %s", table_name, record.get("id"), e)

        sync_manager.update_sync_state(node_id, latest_sync_id, master_latest_sync_id=latest_sync_id)

        logger.info("SyncWorker: full sync complete (last_sync_id=%d)", latest_sync_id)

        self._send_ack(master_url, node_id, latest_sync_id)

    def _send_ack(self, master_url: str, node_id: str, sync_id: int) -> None:
        """Send ACK to master after applying changes, including this node's URL."""
        own_url = _get_own_url()
        try:
            requests.post(
                f"{master_url.rstrip('/')}/api/cluster/sync/ack/",
                json={"node_id": node_id, "sync_id": sync_id, "url": own_url},
                timeout=5,
            )
        except requests.RequestException as e:
            logger.warning("SyncWorker: ACK to master failed: %s", e)

    def _announce_to_master(self, config: DjangoClusterConfig) -> None:
        """Announce this follower's presence to the master so it can send push notifications."""
        if not config.master_url or not config.node_id:
            return
        own_url = _get_own_url()
        try:
            requests.post(
                f"{config.master_url.rstrip('/')}/api/cluster/status/announce/",
                json={
                    "node_id": config.node_id,
                    "url": own_url,
                    "is_master": False,
                },
                timeout=5,
            )
            logger.info("SyncWorker: announced presence to master at %s (url=%s)", config.master_url, own_url)
        except requests.RequestException as e:
            logger.warning("SyncWorker: failed to announce to master: %s", e)


sync_worker = SyncWorker()
