from django.db import models


class DjangoSyncState(models.Model):
    """Django ORM model for sync state - tracks each follower's sync progress."""

    node_id = models.CharField(max_length=100, primary_key=True, verbose_name="Unique identifier of follower node")
    last_synced_id = models.BigIntegerField(default=0, verbose_name="Last sync_log ID successfully applied")
    last_sync_time = models.DateTimeField(auto_now=True, verbose_name="Timestamp of last successful sync")

    class Meta:
        db_table = "sync_state"
        verbose_name = "Sync State"
        verbose_name_plural = "Sync States"

    def __str__(self):
        return f"SyncState(node={self.node_id}, last_id={self.last_synced_id})"
