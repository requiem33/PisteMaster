"""
Base models with version tracking support.
"""

from django.db import models


class VersionedModel(models.Model):
    """
    Abstract base model with version tracking for conflict resolution.
    All syncable models should inherit from this.
    """

    version = models.BigIntegerField(default=1)
    last_modified_node = models.CharField(max_length=100, blank=True, default="")
    last_modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def increment_version(self, node_id: str) -> None:
        """Increment version and track modification."""
        self.version += 1
        self.last_modified_node = node_id
        self.save(update_fields=["version", "last_modified_node", "last_modified_at"])

    def get_version_info(self) -> dict:
        """Get version information for sync log."""
        return {
            "version": self.version,
            "last_modified_node": self.last_modified_node,
            "last_modified_at": self.last_modified_at.isoformat() if self.last_modified_at else None,
        }
