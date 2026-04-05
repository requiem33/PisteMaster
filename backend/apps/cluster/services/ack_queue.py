import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Set, List
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class PendingAck:
    """Represents a pending ACK for a sync log entry."""

    sync_log_id: int
    created_at: float = field(default_factory=time.time)
    confirmed_nodes: Set[str] = field(default_factory=set)
    event: asyncio.Event = field(default_factory=asyncio.Event)

    def to_dict(self) -> dict:
        return {
            "sync_log_id": self.sync_log_id,
            "created_at": self.created_at,
            "confirmed_nodes": list(self.confirmed_nodes),
        }


class AckQueue:
    """Tracks pending ACKs from followers for synchronous write confirmation."""

    DEFAULT_TIMEOUT_MS = 5000
    CLEANUP_INTERVAL_S = 60
    MAX_AGE_S = 300

    def __init__(self):
        self._pending: Dict[int, PendingAck] = {}
        self._lock = Lock()
        self._nodes_required = 1
        self._last_cleanup = time.time()

    def set_nodes_required(self, count: int) -> None:
        """Set the minimum number of node confirmations required."""
        if count < 1:
            raise ValueError("nodes_required must be at least 1")
        self._nodes_required = count
        logger.info(f"ACK queue configured: {count} node(s) required for confirmation")

    def register(self, sync_log_id: int, replicas_required: int = 1) -> "asyncio.Event":
        """
        Register a pending ACK for a sync log entry.
        Returns an Event that will be set when required ACKs are received.
        """
        with self._lock:
            if sync_log_id in self._pending:
                logger.warning(f"Sync log {sync_log_id} already registered")
                return self._pending[sync_log_id].event

            pending_ack = PendingAck(sync_log_id=sync_log_id)
            self._pending[sync_log_id] = pending_ack

            self._cleanup_old_entries()

            logger.debug(f"Registered pending ACK for sync_log_id={sync_log_id}")
            return pending_ack.event

    def acknowledge(self, sync_log_id: int, node_id: str) -> bool:
        """
        Record an ACK from a follower node.
        Returns True if the ACK was processed, False if not found.
        """
        with self._lock:
            if sync_log_id not in self._pending:
                logger.debug(f"Received ACK for unknown sync_log_id={sync_log_id} from node={node_id}")
                return False

            pending_ack = self._pending[sync_log_id]
            pending_ack.confirmed_nodes.add(node_id)

            confirmed_count = len(pending_ack.confirmed_nodes)
            required = self._nodes_required

            logger.debug(f"ACK received for sync_log_id={sync_log_id} from node={node_id} " f"({confirmed_count}/{required})")

            if confirmed_count >= required:
                pending_ack.event.set()
                logger.info(f"Sync log {sync_log_id} confirmed by {confirmed_count} node(s)")
                del self._pending[sync_log_id]

            return True

    def is_confirmed(self, sync_log_id: int) -> bool:
        """Check if a sync log entry has been confirmed."""
        with self._lock:
            if sync_log_id not in self._pending:
                return True
            pending_ack = self._pending[sync_log_id]
            return len(pending_ack.confirmed_nodes) >= self._nodes_required

    def get_confirmed_nodes(self, sync_log_id: int) -> List[str]:
        """Get the list of nodes that have confirmed a sync log entry."""
        with self._lock:
            if sync_log_id not in self._pending:
                return []
            return list(self._pending[sync_log_id].confirmed_nodes)

    def get_pending_count(self) -> int:
        """Get the number of pending ACKs."""
        with self._lock:
            return len(self._pending)

    def get_min_confirmed_id(self) -> int:
        """
        Get the minimum sync log ID that is confirmed (all pending ACKs resolved).

        If no pending ACKs, returns 0 (all entries confirmed).
        If pending ACKs exist, returns min(pending_ids) - 1 (last confirmed ID).
        """
        with self._lock:
            if not self._pending:
                return 0
            min_pending = min(self._pending.keys())
            return max(0, min_pending - 1)

    def get_pending_ids(self) -> List[int]:
        """Get all pending sync log IDs."""
        with self._lock:
            return list(self._pending.keys())

    def get_pending_details(self) -> List[dict]:
        """Get details of all pending ACKs."""
        with self._lock:
            return [ack.to_dict() for ack in self._pending.values()]

    def remove(self, sync_log_id: int) -> bool:
        """Remove a pending ACK entry."""
        with self._lock:
            if sync_log_id in self._pending:
                del self._pending[sync_log_id]
                logger.debug(f"Removed pending ACK for sync_log_id={sync_log_id}")
                return True
            return False

    def clear_all(self) -> int:
        """Clear all pending ACKs. Returns count of cleared entries."""
        with self._lock:
            count = len(self._pending)
            self._pending.clear()
            logger.info(f"Cleared {count} pending ACKs")
            return count

    def _cleanup_old_entries(self) -> None:
        """Remove entries older than MAX_AGE_S."""
        now = time.time()
        if now - self._last_cleanup < self.CLEANUP_INTERVAL_S:
            return

        expired = [sync_id for sync_id, ack in self._pending.items() if now - ack.created_at > self.MAX_AGE_S]

        for sync_id in expired:
            del self._pending[sync_id]
            logger.warning(f"Removed expired pending ACK for sync_log_id={sync_id}")

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired ACK entries")

        self._last_cleanup = now
