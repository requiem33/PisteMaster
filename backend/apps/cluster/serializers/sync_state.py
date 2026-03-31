from rest_framework import serializers

from backend.apps.cluster.serializers.base import DomainModelSerializer
from backend.apps.cluster.models import DjangoSyncState


class SyncStateSerializer(DomainModelSerializer):
    """Serializer for SyncState - handles both Django ORM and domain models."""

    node_id = serializers.CharField(max_length=100, required=True)
    last_synced_id = serializers.IntegerField(required=False, default=0)
    last_sync_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = DjangoSyncState
        fields = ["node_id", "last_synced_id", "last_sync_time"]

    def validate_node_id(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Node ID cannot be empty")
        return value.strip()
