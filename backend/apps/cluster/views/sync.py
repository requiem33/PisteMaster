from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Max

from backend.apps.cluster.models import DjangoSyncLog, DjangoSyncState
from backend.apps.cluster.serializers import (
    SyncLogSerializer,
    SyncLogCreateSerializer,
    SyncStateSerializer,
)


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
