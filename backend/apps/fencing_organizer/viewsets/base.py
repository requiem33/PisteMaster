"""
Base viewsets with automatic sync logging support.
"""

import logging
from typing import Optional

from rest_framework.viewsets import ModelViewSet

from backend.apps.cluster.decorators.transaction import SyncTransaction

logger = logging.getLogger(__name__)


class SyncWriteViewSetMeta(type):
    """
    Metaclass that automatically adds sync logging to create/update/destroy methods.

    Wraps these methods with SyncTransaction and records changes to sync_log.
    """

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        # Get table name from class attribute
        table_name = namespace.get("sync_table_name")

        # Only wrap if table_name is defined
        if not table_name:
            return cls

        # Store table name
        cls._sync_table_name = table_name

        # Wrap CRUD methods with sync logging
        for method_name in ("create", "update", "destroy"):
            if hasattr(cls, method_name):
                original_method = getattr(cls, method_name)
                wrapped_method = cls._wrap_with_sync(method_name, original_method, table_name)
                setattr(cls, method_name, wrapped_method)

        return cls

    @staticmethod
    def _wrap_with_sync(method_name: str, original_method, table_name: str):
        """
        Wrap a viewset method with SyncTransaction.

        Args:
            method_name: Name of method ('create', 'update', 'destroy')
            original_method: Original method to wrap
            table_name: Table name for sync log

        Returns:
            Wrapped method
        """

        def wrapper(self, request, *args, **kwargs):
            # For destroy, we need to get the object first
            if method_name == "destroy":
                instance = self.get_object()
                record_id = str(instance.id)

                with SyncTransaction() as sync_tx:
                    sync_tx.record_delete(
                        table_name=table_name,
                        record_id=record_id,
                    )
                    request._sync_log_id = sync_tx.last_sync_id

                    result = original_method(self, request, *args, **kwargs)

                return result

            # For create/update, do operation first then record
            with SyncTransaction() as sync_tx:
                result = original_method(self, request, *args, **kwargs)

                # Extract instance from result
                if hasattr(result, "data") and hasattr(self, "get_object"):
                    try:
                        if method_name == "create":
                            # Get the created instance
                            instance_id = result.data.get("id")
                            if instance_id and hasattr(self, "queryset"):
                                instance = self.queryset.get(id=instance_id)
                                sync_tx.record_insert(table_name=table_name, instance=instance, data=result.data)
                        else:  # update
                            instance = self.get_object()
                            sync_tx.record_update(table_name=table_name, instance=instance, data=result.data)
                    except Exception as e:
                        logger.warning(f"Failed to record sync log: {e}")

                request._sync_log_id = sync_tx.last_sync_id

            return result

        wrapper.__name__ = original_method.__name__
        wrapper.__doc__ = original_method.__doc__
        return wrapper


class SyncWriteModelViewSet(ModelViewSet, metaclass=SyncWriteViewSetMeta):
    """
    ModelViewSet with automatic sync logging for cluster replication.

    Usage:
        class TournamentViewSet(SyncWriteModelViewSet):
            sync_table_name = 'tournament'  # Set this to enable sync logging
            queryset = DjangoTournament.objects.all()
            serializer_class = TournamentSerializer

    The metaclass automatically wraps create/update/destroy methods with
    SyncTransaction, recording changes to the sync log for replication.
    """

    sync_table_name: Optional[str] = None

    def get_serializer_context(self):
        """Add sync_table_name to serializer context."""
        context = super().get_serializer_context()
        context["sync_table_name"] = getattr(self, "_sync_table_name", None)
        return context
