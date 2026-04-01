import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Type

from django.db import transaction
from django.db.models import Model, Max

from backend.apps.cluster.models import DjangoSyncLog, DjangoSyncState
from backend.apps.cluster.services.ack_queue import AckQueue

logger = logging.getLogger(__name__)


class SyncOperation(str, Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class SyncChange:
    """Represents a single sync change."""

    id: int
    table_name: str
    record_id: str
    operation: str
    data: Dict[str, Any]
    version: int
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "operation": self.operation,
            "data": self.data,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class SyncResult:
    """Result of a sync operation."""

    last_id: int
    has_more: bool
    changes: List[SyncChange]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "last_id": self.last_id,
            "has_more": self.has_more,
            "changes": [c.to_dict() for c in self.changes],
        }


@dataclass
class ModelRegistryEntry:
    """Entry in the model registry for sync."""

    model_class: Type[Model]
    serializer_class: Any
    version_field: str = "version"
    last_modified_field: str = "updated_at"


class SyncManager:
    """Manages data synchronization for cluster replication."""

    DEFAULT_BATCH_SIZE = 100
    MAX_BATCH_SIZE = 500

    def __init__(self):
        self._ack_queue = AckQueue()
        self._model_registry: Dict[str, ModelRegistryEntry] = {}
        self._initialized = False

    def register_model(
        self,
        table_name: str,
        model_class: Type[Model],
        serializer_class: Any,
        version_field: str = "version",
        last_modified_field: str = "updated_at",
    ) -> None:
        """Register a model for synchronization."""
        self._model_registry[table_name] = ModelRegistryEntry(
            model_class=model_class,
            serializer_class=serializer_class,
            version_field=version_field,
            last_modified_field=last_modified_field,
        )
        logger.debug(f"Registered model for sync: {table_name}")

    def get_registered_tables(self) -> List[str]:
        """Get list of all registered table names."""
        return list(self._model_registry.keys())

    @property
    def ack_queue(self) -> AckQueue:
        """Get the ACK queue instance."""
        return self._ack_queue

    @ack_queue.setter
    def ack_queue(self, value: AckQueue) -> None:
        """Set the ACK queue instance."""
        self._ack_queue = value

    def record_change(
        self,
        table_name: str,
        record_id: str,
        operation: str,
        data: Dict[str, Any],
        version: int = 1,
    ) -> DjangoSyncLog:
        """
        Record a change in the sync log.
        Should be called within a transaction.
        """
        if operation not in [SyncOperation.INSERT.value, SyncOperation.UPDATE.value, SyncOperation.DELETE.value]:
            raise ValueError(f"Invalid operation: {operation}")

        sync_log = DjangoSyncLog.objects.create(
            table_name=table_name,
            record_id=str(record_id),
            operation=operation,
            data=data,
            version=version,
        )

        logger.debug(f"Recorded sync log: id={sync_log.id}, table={table_name}, " f"record_id={record_id}, operation={operation}")

        return sync_log

    @transaction.atomic
    def record_write(
        self,
        table_name: str,
        record_id: str,
        operation: str,
        data: Dict[str, Any],
        version: int = 1,
    ) -> DjangoSyncLog:
        """
        Record a write operation atomically.
        This is the preferred method for recording changes.
        """
        return self.record_change(table_name, record_id, operation, data, version)

    def get_changes_since(self, since_id: int, limit: int = DEFAULT_BATCH_SIZE) -> SyncResult:
        """
        Get incremental changes since the given sync log ID.
        Used by followers to pull changes from master.
        """
        limit = min(limit, self.MAX_BATCH_SIZE)

        queryset = DjangoSyncLog.objects.filter(id__gt=since_id).order_by("id")[: limit + 1]

        changes = []
        for log in queryset:
            changes.append(
                SyncChange(
                    id=log.id,
                    table_name=log.table_name,
                    record_id=log.record_id,
                    operation=log.operation,
                    data=log.data,
                    version=log.version,
                    created_at=log.created_at,
                )
            )

        has_more = len(changes) > limit
        if has_more:
            changes = changes[:limit]

        last_id = changes[-1].id if changes else since_id

        return SyncResult(last_id=last_id, has_more=has_more, changes=changes)

    def get_changes_for_tables(
        self,
        since_id: int,
        tables: List[str],
        limit: int = DEFAULT_BATCH_SIZE,
    ) -> SyncResult:
        """Get changes for specific tables since the given ID."""
        limit = min(limit, self.MAX_BATCH_SIZE)

        queryset = DjangoSyncLog.objects.filter(id__gt=since_id, table_name__in=tables).order_by("id")[: limit + 1]

        changes = []
        for log in queryset:
            changes.append(
                SyncChange(
                    id=log.id,
                    table_name=log.table_name,
                    record_id=log.record_id,
                    operation=log.operation,
                    data=log.data,
                    version=log.version,
                    created_at=log.created_at,
                )
            )

        has_more = len(changes) > limit
        if has_more:
            changes = changes[:limit]

        last_id = changes[-1].id if changes else since_id

        return SyncResult(last_id=last_id, has_more=has_more, changes=changes)

    def get_latest_sync_id(self) -> int:
        """Get the latest sync log ID."""
        result = DjangoSyncLog.objects.aggregate(max_id=Max("id"))
        return result["max_id"] or 0

    def get_sync_state(self, node_id: str) -> Optional[DjangoSyncState]:
        """Get the sync state for a follower node."""
        try:
            return DjangoSyncState.objects.get(node_id=node_id)
        except DjangoSyncState.DoesNotExist:
            return None

    def update_sync_state(self, node_id: str, last_synced_id: int) -> DjangoSyncState:
        """Update the sync state for a follower node."""
        sync_state, created = DjangoSyncState.objects.update_or_create(node_id=node_id, defaults={"last_synced_id": last_synced_id})

        if created:
            logger.info(f"Created sync state for node={node_id}")
        else:
            logger.debug(f"Updated sync state for node={node_id}: last_id={last_synced_id}")

        return sync_state

    def apply_change(self, change: SyncChange) -> bool:
        """
        Apply a sync change to the local database.
        Used by followers to apply changes from master.

        Returns True if successful, False if conflict or error.
        """
        table_name = change.table_name

        if table_name not in self._model_registry:
            logger.warning(f"Unknown table: {table_name}")
            return False

        registry_entry = self._model_registry[table_name]
        model_class = registry_entry.model_class

        try:
            with transaction.atomic():
                if change.operation == SyncOperation.INSERT.value:
                    return self._apply_insert(model_class, change, registry_entry)
                elif change.operation == SyncOperation.UPDATE.value:
                    return self._apply_update(model_class, change, registry_entry)
                elif change.operation == SyncOperation.DELETE.value:
                    return self._apply_delete(model_class, change)
                else:
                    logger.error(f"Unknown operation: {change.operation}")
                    return False
        except Exception as e:
            logger.error(f"Failed to apply change {change.id}: {e}")
            return False

    def _apply_insert(
        self,
        model_class: Type[Model],
        change: SyncChange,
        registry_entry: ModelRegistryEntry,
    ) -> bool:
        """Apply an INSERT operation."""
        try:
            if model_class.objects.filter(id=change.record_id).exists():
                logger.warning(f"Record already exists for INSERT: {change.record_id}")
                return self._apply_update(model_class, change, registry_entry)

            model_class.objects.create(id=change.record_id, **change.data)
            logger.debug(f"Applied INSERT: {change.table_name}/{change.record_id}")
            return True
        except Exception as e:
            logger.error(f"INSERT failed for {change.table_name}/{change.record_id}: {e}")
            return False

    def _apply_update(
        self,
        model_class: Type[Model],
        change: SyncChange,
        registry_entry: ModelRegistryEntry,
    ) -> bool:
        """Apply an UPDATE operation with conflict resolution."""
        try:
            record = model_class.objects.filter(id=change.record_id).first()

            if not record:
                logger.warning(f"Record not found for UPDATE: {change.record_id}, creating instead")
                model_class.objects.create(id=change.record_id, **change.data)
                return True

            existing_version = getattr(record, registry_entry.version_field, 1)
            if existing_version > change.version:
                logger.info(
                    f"Skipping UPDATE - existingversion {existing_version} > " f"incoming version {change.version} for {change.record_id}"
                )
                return True

            if existing_version == change.version:
                existing_modified = getattr(record, registry_entry.last_modified_field, None)
                incoming_modified = change.created_at

                if existing_modified and incoming_modified:
                    if existing_modified >= incoming_modified:
                        logger.info(f"Skipping UPDATE - existing is newer for {change.record_id}")
                        return True

            for key, value in change.data.items():
                setattr(record, key, value)

            if hasattr(record, registry_entry.version_field):
                setattr(record, registry_entry.version_field, change.version)

            record.save(update_fields=list(change.data.keys()) + [registry_entry.version_field])

            logger.debug(f"Applied UPDATE: {change.table_name}/{change.record_id}")
            return True

        except Exception as e:
            logger.error(f"UPDATE failed for {change.table_name}/{change.record_id}: {e}")
            return False

    def _apply_delete(self, model_class: Type[Model], change: SyncChange) -> bool:
        """Apply a DELETE operation."""
        try:
            deleted, _ = model_class.objects.filter(id=change.record_id).delete()

            if deleted:
                logger.debug(f"Applied DELETE: {change.table_name}/{change.record_id}")
            else:
                logger.debug(f"DELETE - record already gone: {change.table_name}/{change.record_id}")

            return True
        except Exception as e:
            logger.error(f"DELETE failed for {change.table_name}/{change.record_id}: {e}")
            return False

    def apply_changes_batch(self, changes: List[SyncChange]) -> Dict[str, int]:
        """
        Apply a batch of changes.
        Returns summary of successes/failures.
        """
        results = {"success": 0, "failed": 0, "skipped": 0}

        for change in changes:
            result = self.apply_change(change)
            if result is True:
                results["success"] += 1
            elif result is False:
                results["failed"] += 1
            else:
                results["skipped"] += 1

        logger.info(f"Batch apply complete: {results['success']} success, " f"{results['failed']} failed, {results['skipped']} skipped")

        return results

    def export_full_data(
        self,
        tables: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 1000,
    ) -> Dict[str, Any]:
        """
        Export full data for all or specified tables.
        Used for full sync operations.
        """
        if tables is None:
            tables = list(self._model_registry.keys())

        exported_data = {}
        total_records = 0

        for table_name in tables:
            if table_name not in self._model_registry:
                continue

            registry_entry = self._model_registry[table_name]
            model_class = registry_entry.model_class
            serializer_class = registry_entry.serializer_class

            queryset = model_class.objects.all()
            offset = (page - 1) * page_size
            records = queryset[offset : offset + page_size]

            serializer = serializer_class(records, many=True)
            exported_data[table_name] = serializer.data
            total_records += len(records)

        latest_sync_id = self.get_latest_sync_id()

        return {
            "page": page,
            "page_size": page_size,
            "tables": tables,
            "total_records": total_records,
            "latest_sync_id": latest_sync_id,
            "data": exported_data,
        }

    def needs_manual_review(self, table_name: str) -> bool:
        """
        Check if a table requires manual review for conflicts.
        Critical tables like scores need human verification.
        """
        critical_tables = [
            "score",
            "ranking",
            "elimination",
            "pool_bout",
            "poolassignment",
        ]
        return table_name.lower() in critical_tables


sync_manager = SyncManager()
