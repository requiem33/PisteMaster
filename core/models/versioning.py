"""
Version tracking for conflict resolution in distributed clusters.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class VersionedModel:
    """
    Mixin for models that need version tracking for conflict resolution.

    Attributes:
        version: Incremented on each update
        last_modified_node: ID of the node that last modified this record
        last_modified_at: Timestamp of last modification
    """

    version: int = field(default=1, kw_only=True)
    last_modified_node: str = field(default="", kw_only=True)
    last_modified_at: Optional[datetime] = field(default_factory=datetime.now, kw_only=True)

    def increment_version(self, node_id: str) -> None:
        """Increment version and update modification metadata."""
        self.version += 1
        self.last_modified_node = node_id
        self.last_modified_at = datetime.now()

    def get_version_info(self) -> dict:
        """Get version information for sync log."""
        return {
            "version": self.version,
            "last_modified_node": self.last_modified_node,
            "last_modified_at": self.last_modified_at.isoformat() if self.last_modified_at else None,
        }
