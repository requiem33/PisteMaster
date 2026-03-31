from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SyncState:
    """Sync state domain model - tracks each follower's sync progress."""

    node_id: str = field(metadata={"max_length": 100, "description": "Unique identifier of follower node"})
    last_synced_id: int = field(default=0, metadata={"description": "Last sync_log ID successfully applied"})
    last_sync_time: datetime = field(default_factory=datetime.now, metadata={"description": "Timestamp of last successful sync"})

    id: Optional[int] = field(default=None, metadata={"description": "Auto-increment primary key (optional)"})

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "node_id": self.node_id,
            "last_synced_id": self.last_synced_id,
            "last_sync_time": (self.last_sync_time.isoformat() if self.last_sync_time else None),
        }
