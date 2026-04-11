import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID

from django.db import transaction

from backend.apps.cluster.services.sync_manager import sync_manager

logger = logging.getLogger(__name__)


class SyncTransaction:
    """
    Context manager for sync-aware database transactions.

    Automatically records changes to sync_log when the transaction commits.

    Usage:
        with SyncTransaction() as sync_tx:
            tournament = Tournament.objects.create(...)
            sync_tx.record(
                table_name="tournament",
                record_id=tournament.id,
                operation="INSERT",
                data={"name": tournament.name, ...}
            )
    """

    @staticmethod
    def _make_json_serializable(data):
        """Recursively convert Python objects to JSON-serializable types.

        Handles datetime, date, UUID, Decimal, and nested dicts/lists.
        """
        if isinstance(data, (datetime, date)):
            return data.isoformat()
        if isinstance(data, UUID):
            return str(data)
        if isinstance(data, Decimal):
            return str(data)
        if isinstance(data, dict):
            return {k: SyncTransaction._make_json_serializable(v) for k, v in data.items()}
        if isinstance(data, (list, tuple)):
            return [SyncTransaction._make_json_serializable(item) for item in data]
        return data

    def __init__(self, using: Optional[str] = None):
        self.using = using
        self._records: list = []
        self._atomic = None
        self.last_sync_id: Optional[int] = None

    def __enter__(self) -> "SyncTransaction":
        self._atomic = transaction.atomic(using=self.using)
        self._atomic.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            for record in self._records:
                try:
                    sync_log = sync_manager.record_change(
                        table_name=record["table_name"],
                        record_id=record["record_id"],
                        operation=record["operation"],
                        data=record["data"],
                        version=record.get("version", 1),
                    )
                    self.last_sync_id = sync_log.id

                    logger.debug(
                        f"Sync recorded: {record['operation']} on "
                        f"{record['table_name']}/{record['record_id']}, "
                        f"sync_log_id={sync_log.id}"
                    )
                except Exception as e:
                    logger.error(f"Failed to record sync: {e}")

        self._atomic.__exit__(exc_type, exc_val, exc_tb)
        return False

    def record(
        self,
        table_name: str,
        record_id: str,
        operation: str,
        data: Dict[str, Any],
        version: int = 1,
    ) -> None:
        """
        Queue a sync record to be written after transaction commits.

        Args:
            table_name: Name of the table/model
            record_id: ID of the affected record
            operation: INSERT, UPDATE, or DELETE
            data: JSON-serializable data of the change
            version: Version number for conflict resolution
        """
        serialized_data = self._make_json_serializable(data)
        self._records.append(
            {
                "table_name": table_name,
                "record_id": str(record_id),
                "operation": operation,
                "data": serialized_data,
                "version": version,
            }
        )

    def record_insert(
        self,
        table_name: str,
        instance: any,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Shorthand for recording an INSERT operation."""
        record_id = str(getattr(instance, "id", instance))
        version = getattr(instance, "version", 1)
        self.record(
            table_name=table_name,
            record_id=record_id,
            operation="INSERT",
            data=data or {},
            version=version,
        )

    def record_update(
        self,
        table_name: str,
        instance: any,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Shorthand for recording an UPDATE operation."""
        record_id = str(getattr(instance, "id", instance))
        version = getattr(instance, "version", 1)
        self.record(
            table_name=table_name,
            record_id=record_id,
            operation="UPDATE",
            data=data or {},
            version=version,
        )

    def record_delete(
        self,
        table_name: str,
        record_id: str,
    ) -> None:
        """Shorthand for recording a DELETE operation."""
        self.record(
            table_name=table_name,
            record_id=record_id,
            operation="DELETE",
            data={},
            version=0,
        )


def sync_write(table_name: str):
    """
    Decorator for service methods that perform write operations.

    Wraps the method in a SyncTransaction and passes it as first argument.

    Usage:
        @sync_write("tournament")
        def create_tournament(self, sync_tx, tournament_data):
            tournament = Tournament.objects.create(**tournament_data)
            sync_tx.record_insert("tournament", tournament)
            return tournament
    """

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            with SyncTransaction() as sync_tx:
                return func(self, sync_tx, *args, **kwargs)

        return wrapper

    return decorator
