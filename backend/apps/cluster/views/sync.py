import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.db.models import Max
from django.views.decorators.csrf import csrf_exempt

from backend.apps.cluster.models import DjangoSyncLog, DjangoSyncState
from backend.apps.cluster.serializers import (
    SyncLogSerializer,
    SyncLogCreateSerializer,
    SyncStateSerializer,
)
from backend.apps.cluster.models.cluster_config import DjangoClusterConfig
from backend.apps.cluster.services.sync_manager import sync_manager
from backend.apps.cluster.services.sync_worker import sync_worker

logger = logging.getLogger(__name__)


class SyncLogViewSet(viewsets.GenericViewSet):
    """Sync log API - Handles synchronization log records for cluster replication."""

    queryset = DjangoSyncLog.objects.all()
    serializer_class = SyncLogSerializer
    lookup_field = "id"

    def list(self, request):
        """Get sync log entries with optional filters."""
        queryset = self.queryset

        table_name = request.query_params.get("table_name")
        if table_name:
            queryset = queryset.filter(table_name=table_name)

        record_id = request.query_params.get("record_id")
        if record_id:
            queryset = queryset.filter(record_id=record_id)

        since_id = request.query_params.get("since")
        if since_id:
            try:
                since_id = int(since_id)
                queryset = queryset.filter(id__gt=since_id)
            except ValueError:
                return Response({"detail": "Invalid since ID"}, status=status.HTTP_400_BAD_REQUEST)

        limit = request.query_params.get("limit", 100)
        try:
            limit = min(int(limit), 500)
        except ValueError:
            limit = 100

        queryset = queryset[:limit]
        serializer = self.get_serializer(queryset, many=True)

        last_id = queryset.aggregate(max_id=Max("id"))["max_id"] or since_id or 0

        return Response(
            {
                "last_id": last_id,
                "has_more": len(queryset) == limit,
                "changes": serializer.data,
            }
        )

    def retrieve(self, request, id=None):
        """Get a single sync log entry."""
        try:
            sync_log = self.queryset.get(id=id)
        except DjangoSyncLog.DoesNotExist:
            return Response({"detail": "Sync log not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(sync_log)
        return Response(serializer.data)

    def create(self, request):
        """Create a new sync log entry."""
        serializer = SyncLogCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sync_log = DjangoSyncLog.objects.create(**serializer.validated_data)
        response_serializer = SyncLogSerializer(sync_log)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def latest(self, request):
        """Get the latest sync log ID."""
        latest_id = DjangoSyncLog.objects.aggregate(max_id=Max("id"))["max_id"] or 0
        return Response({"latest_id": latest_id})

    @action(detail=False, methods=["get"])
    def tables(self, request):
        """Get list of all tables with sync log entries."""
        tables = DjangoSyncLog.objects.values_list("table_name", flat=True).distinct()
        return Response({"tables": list(tables)})


class SyncStateViewSet(viewsets.GenericViewSet):
    """Sync state API - Tracks each follower's replication progress."""

    queryset = DjangoSyncState.objects.all()
    serializer_class = SyncStateSerializer
    lookup_field = "node_id"

    def list(self, request):
        """Get all follower sync states."""
        states = self.queryset
        serializer = self.get_serializer(states, many=True)
        return Response(serializer.data)

    def retrieve(self, request, node_id=None):
        """Get a specific follower's sync state."""
        try:
            sync_state = self.queryset.get(node_id=node_id)
        except DjangoSyncState.DoesNotExist:
            return Response({"detail": "Sync state not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(sync_state)
        return Response(serializer.data)

    def create(self, request):
        """Create or update a follower's sync state."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        node_id = serializer.validated_data["node_id"]
        last_synced_id = serializer.validated_data.get("last_synced_id", 0)

        sync_state, created = DjangoSyncState.objects.update_or_create(node_id=node_id, defaults={"last_synced_id": last_synced_id})

        response_serializer = self.get_serializer(sync_state)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_serializer.data, status=status_code)

    def update(self, request, node_id=None):
        """Update a follower's sync state."""
        try:
            sync_state = self.queryset.get(node_id=node_id)
        except DjangoSyncState.DoesNotExist:
            return Response({"detail": "Sync state not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(sync_state, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if "last_synced_id" in serializer.validated_data:
            sync_state.last_synced_id = serializer.validated_data["last_synced_id"]
            sync_state.save()

        response_serializer = self.get_serializer(sync_state)
        return Response(response_serializer.data)


class SyncViewSet(viewsets.GenericViewSet):
    """Sync API - Handles data synchronization between cluster nodes."""

    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"], url_path="changes")
    def get_changes(self, request):
        """
        Get incremental changes since the given sync log ID.
        Used by followers to pull changes from master.

        Query params:
        - since: Last sync log ID the follower has applied (default: 0)
        - limit: Maximum number of changes to return (default: 100, max: 500)
        - tables: Comma-separated list of tables to filter (optional)
        """
        since_id = request.query_params.get("since", "0")
        try:
            since_id = int(since_id)
        except ValueError:
            return Response({"detail": "Invalid 'since' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        limit = request.query_params.get("limit", "100")
        try:
            limit = min(int(limit), 500)
        except ValueError:
            return Response({"detail": "Invalid 'limit' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        tables_param = request.query_params.get("tables")
        tables = None
        if tables_param:
            tables = [t.strip() for t in tables_param.split(",") if t.strip()]

        try:
            if tables:
                result = sync_manager.get_changes_for_tables(since_id, tables, limit)
            else:
                result = sync_manager.get_changes_since(since_id, limit)

            logger.debug(
                f"Sync changes request: since={since_id}, limit={limit}, " f"returned={len(result.changes)}, has_more={result.has_more}"
            )

            return Response(result.to_dict())

        except Exception as e:
            logger.error(f"Failed to get changes: {e}")
            return Response({"detail": "Failed to get changes"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="full")
    def get_full_sync(self, request):
        """
        Get full data export for initial sync.
        Used by new followers to get complete dataset.

        Query params:
        - page: Page number (default: 1)
        - page_size: Records per page (default: 1000, max: 5000)
        - tables: Comma-separated list of tables to export (optional)
        """
        page = request.query_params.get("page", "1")
        try:
            page = int(page)
            if page < 1:
                page = 1
        except ValueError:
            return Response({"detail": "Invalid 'page' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        page_size = request.query_params.get("page_size", "1000")
        try:
            page_size = min(int(page_size), 5000)
            if page_size < 1:
                page_size = 1000
        except ValueError:
            return Response({"detail": "Invalid 'page_size' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        tables_param = request.query_params.get("tables")
        tables = None
        if tables_param:
            tables = [t.strip() for t in tables_param.split(",") if t.strip()]

        try:
            result = sync_manager.export_full_data(tables=tables, page=page, page_size=page_size)

            logger.info(f"Full sync request: page={page}, page_size={page_size}, " f"tables={tables}, records={result['total_records']}")

            return Response(result)

        except Exception as e:
            logger.error(f"Failed to export full data: {e}")
            return Response({"detail": "Failed to export data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="ack")
    def acknowledge(self, request):
        """
        Acknowledge receipt of sync changes.
        Used by followers to confirm they have applied changes.

        Request body:
        - node_id: Identifier of the follower node
        - sync_id: The last sync log ID that was applied
        """
        node_id = request.data.get("node_id")
        sync_id = request.data.get("sync_id")

        if not node_id:
            return Response({"detail": "node_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if sync_id is None:
            return Response({"detail": "sync_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            sync_id = int(sync_id)
        except ValueError:
            return Response({"detail": "Invalid sync_id"}, status=status.HTTP_400_BAD_REQUEST)

        sync_manager.ack_queue.acknowledge(sync_id, node_id)
        url = request.data.get("url")
        sync_manager.update_sync_state(node_id, sync_id, url=url)

        logger.debug(f"ACK received from node={node_id} for sync_id={sync_id}")

        return Response({"status": "acknowledged", "node_id": node_id, "sync_id": sync_id})

    @action(detail=False, methods=["post"], url_path="apply")
    def apply_changes(self, request):
        """
        Apply a batch of sync changes.
        Used by followers to apply received changes to local DB.
        Also updates local sync state tracking progress.

        Request body:
        - changes: List of change objects from sync/changes endpoint
        - node_id: (optional) Identifier of the follower node
        - url: (optional) HTTP endpoint URL of this follower node
        """
        changes = request.data.get("changes", [])

        if not isinstance(changes, list):
            return Response({"detail": "changes must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        if len(changes) > 500:
            return Response({"detail": "Maximum 500 changes per batch"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from backend.apps.cluster.services.sync_manager import SyncChange

            sync_changes = []
            for c in changes:
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

            results = sync_manager.apply_changes_batch(sync_changes)

            if sync_changes:
                last_id = max(c.id for c in sync_changes)
                node_id = request.data.get("node_id") or getattr(settings, "CLUSTER_CONFIG", {}).get("node_id", "unknown")
                url = request.data.get("url")
                sync_manager.update_sync_state(node_id, last_id, url=url)

            return Response(
                {
                    "status": "applied",
                    "total": len(changes),
                    "success": results["success"],
                    "failed": results["failed"],
                    "skipped": results["skipped"],
                }
            )

        except Exception as e:
            logger.error(f"Failed to apply changes: {e}")
            return Response({"detail": "Failed to apply changes"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="notify")
    def notify_sync(self, request):
        """
        Receive push notification from master about new sync_log entry.
        Triggers immediate sync on this follower's SyncWorker.
        Returns 200 immediately (non-blocking).
        """
        config = DjangoClusterConfig.get_config()
        if config.is_master:
            return Response({"status": "ignored", "reason": "master_node"})

        sync_worker.trigger_immediate_sync()

        sync_log_id = request.data.get("sync_log_id")
        table_name = request.data.get("table_name")
        record_id = request.data.get("record_id")
        logger.info(
            "Push notification received: sync_log_id=%s, table=%s, record=%s",
            sync_log_id,
            table_name,
            record_id,
        )

        return Response({"status": "notified"})


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def sync_ack(request):
    """
    Standalone endpoint for ACK messages.
    Alternative to the viewset action.
    """
    node_id = request.data.get("node_id")
    sync_id = request.data.get("sync_id")

    if not node_id or sync_id is None:
        return Response({"detail": "node_id and sync_id are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        sync_id = int(sync_id)
    except ValueError:
        return Response({"detail": "Invalid sync_id"}, status=status.HTTP_400_BAD_REQUEST)

    sync_manager.ack_queue.acknowledge(sync_id, node_id)
    url = request.data.get("url")
    sync_manager.update_sync_state(node_id, sync_id, url=url)

    return Response({"status": "acknowledged", "node_id": node_id, "sync_id": sync_id})
