from django.db import models


class DjangoSyncLog(models.Model):
    """Django ORM model for sync log - records changes for cluster replication."""

    id = models.BigAutoField(primary_key=True)
    table_name = models.CharField(max_length=100, verbose_name="Table/entity name")
    record_id = models.CharField(max_length=100, verbose_name="Primary key of changed record")
    operation = models.CharField(
        max_length=10,
        verbose_name="Operation type",
        help_text="INSERT, UPDATE, or DELETE",
    )
    data = models.JSONField(verbose_name="JSON data of the change")
    version = models.BigIntegerField(default=1, verbose_name="Version number for conflict resolution")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp when log was created")

    class Meta:
        db_table = "sync_log"
        verbose_name = "Sync Log"
        verbose_name_plural = "Sync Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["table_name"], name="idx_sync_log_table"),
            models.Index(fields=["record_id"], name="idx_sync_log_record"),
            models.Index(fields=["created_at"], name="idx_sync_log_created"),
            models.Index(fields=["table_name", "record_id"], name="idx_sync_log_table_record"),
        ]

    def __str__(self):
        return f"SyncLog({self.id}: {self.operation} {self.table_name}.{self.record_id})"
