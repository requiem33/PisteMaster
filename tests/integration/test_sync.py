"""
Integration tests for the sync system.
Tests cover SyncManager, AckQueue, and full sync workflows.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from backend.apps.cluster.services.sync_manager import SyncManager, SyncOperation, SyncChange, SyncResult
from backend.apps.cluster.services.ack_queue import AckQueue
from backend.apps.cluster.models import DjangoSyncLog, DjangoSyncState


@pytest.fixture
def sync_manager():
    manager = SyncManager()
    return manager


@pytest.fixture
def ack_queue():
    return AckQueue()


@pytest.fixture
def sample_change():
    return SyncChange(
        id=1,
        table_name="tournament",
        record_id="test-uuid-123",
        operation=SyncOperation.INSERT.value,
        data={"name": "Test Tournament", "status": "draft"},
        version=1,
        created_at=datetime.now(),
    )


class TestAckQueue:
    def test_set_nodes_required_valid(self, ack_queue):
        ack_queue.set_nodes_required(3)
        assert ack_queue._nodes_required == 3

    def test_set_nodes_required_invalid(self, ack_queue):
        with pytest.raises(ValueError, match="must be at least 1"):
            ack_queue.set_nodes_required(0)

    def test_register_pending_ack(self, ack_queue):
        event = ack_queue.register(100)
        assert 100 in ack_queue.get_pending_ids()
        assert not event.is_set()

    def test_register_duplicate(self, ack_queue):
        event1 = ack_queue.register(100)
        event2 = ack_queue.register(100)
        assert event1 is event2

    def test_acknowledge_sync_log(self, ack_queue):
        ack_queue.set_nodes_required(2)
        ack_queue.register(100)

        result = ack_queue.acknowledge(100, "node_001")
        assert result is True
        assert "node_001" in ack_queue.get_confirmed_nodes(100)

        result = ack_queue.acknowledge(100, "node_002")
        assert result is True

        assert 100 not in ack_queue.get_pending_ids()

    def test_acknowledge_unknown_id(self, ack_queue):
        result = ack_queue.acknowledge(999, "node_001")
        assert result is False

    def test_is_confirmed(self, ack_queue):
        ack_queue.set_nodes_required(1)
        ack_queue.register(100)

        assert not ack_queue.is_confirmed(100)

        ack_queue.acknowledge(100, "node_001")
        assert ack_queue.is_confirmed(100)

    def test_is_confirmed_not_registered(self, ack_queue):
        assert ack_queue.is_confirmed(999) is True

    def test_remove_pending_ack(self, ack_queue):
        ack_queue.register(100)
        assert ack_queue.remove(100) is True
        assert 100 not in ack_queue.get_pending_ids()
        assert ack_queue.remove(100) is False

    def test_clear_all(self, ack_queue):
        ack_queue.register(100)
        ack_queue.register(200)
        ack_queue.register(300)

        count = ack_queue.clear_all()
        assert count == 3
        assert ack_queue.get_pending_count() == 0

    def test_get_pending_details(self, ack_queue):
        ack_queue.register(100)
        ack_queue.acknowledge(100, "node_001")

        details = ack_queue.get_pending_details()
        assert len(details) == 1
        assert details[0]["sync_log_id"] == 100
        assert "node_001" in details[0]["confirmed_nodes"]


class TestSyncManager:
    def test_register_model(self, sync_manager):
        mock_model = MagicMock()
        mock_serializer = MagicMock()

        sync_manager.register_model(
            table_name="tournament",
            model_class=mock_model,
            serializer_class=mock_serializer,
        )

        assert "tournament" in sync_manager.get_registered_tables()

    def test_get_registered_tables(self, sync_manager):
        sync_manager.register_model("table_a", MagicMock(), MagicMock())
        sync_manager.register_model("table_b", MagicMock(), MagicMock())

        tables = sync_manager.get_registered_tables()
        assert "table_a" in tables
        assert "table_b" in tables

    def test_record_change_invalid_operation(self, sync_manager):
        with pytest.raises(ValueError, match="Invalid operation"):
            sync_manager.record_change(
                table_name="tournament",
                record_id="test-123",
                operation="INVALID",
                data={},
            )

    @pytest.mark.django_db
    def test_record_change_insert(self, sync_manager):
        sync_log = sync_manager.record_change(
            table_name="tournament",
            record_id="test-uuid-insert",
            operation=SyncOperation.INSERT.value,
            data={"name": "Test Tournament"},
            version=1,
        )

        assert sync_log.id is not None
        assert sync_log.table_name == "tournament"
        assert sync_log.record_id == "test-uuid-insert"
        assert sync_log.operation == "INSERT"

    @pytest.mark.django_db
    def test_record_write_atomic(self, sync_manager):
        sync_log = sync_manager.record_write(
            table_name="fencer",
            record_id="test-uuid-write",
            operation=SyncOperation.UPDATE.value,
            data={"name": "Updated Name"},
            version=2,
        )

        assert sync_log.id is not None
        assert sync_log.operation == "UPDATE"

    @pytest.mark.django_db
    def test_get_changes_since(self, sync_manager):
        sync_manager.record_change(
            table_name="tournament",
            record_id="uuid-1",
            operation=SyncOperation.INSERT.value,
            data={"name": "Tournament 1"},
        )
        sync_manager.record_change(
            table_name="tournament",
            record_id="uuid-2",
            operation=SyncOperation.INSERT.value,
            data={"name": "Tournament 2"},
        )

        result = sync_manager.get_changes_since(since_id=0, limit=10)

        assert result.last_id > 0
        assert len(result.changes) == 2

    @pytest.mark.django_db
    def test_get_changes_since_with_limit(self, sync_manager):
        for i in range(5):
            sync_manager.record_change(
                table_name="tournament",
                record_id=f"uuid-{i}",
                operation=SyncOperation.INSERT.value,
                data={"name": f"Tournament {i}"},
            )

        result = sync_manager.get_changes_since(since_id=0, limit=2)

        assert len(result.changes) == 2
        assert result.has_more is True

    @pytest.mark.django_db
    def test_get_changes_for_tables(self, sync_manager):
        sync_manager.record_change(
            table_name="tournament",
            record_id="uuid-1",
            operation=SyncOperation.INSERT.value,
            data={"name": "Tournament 1"},
        )
        sync_manager.record_change(
            table_name="fencer",
            record_id="uuid-2",
            operation=SyncOperation.INSERT.value,
            data={"name": "Fencer 1"},
        )

        result = sync_manager.get_changes_for_tables(
            since_id=0,
            tables=["fencer"],
            limit=10,
        )

        assert len(result.changes) == 1
        assert result.changes[0].table_name == "fencer"

    @pytest.mark.django_db
    def test_get_latest_sync_id(self, sync_manager):
        sync_manager.record_change(
            table_name="tournament",
            record_id="uuid-1",
            operation=SyncOperation.INSERT.value,
            data={"name": "Test"},
        )
        log2 = sync_manager.record_change(
            table_name="tournament",
            record_id="uuid-2",
            operation=SyncOperation.INSERT.value,
            data={"name": "Test 2"},
        )

        latest_id = sync_manager.get_latest_sync_id()

        assert latest_id == log2.id

    @pytest.mark.django_db
    def test_get_latest_sync_id_empty(self, sync_manager):
        latest_id = sync_manager.get_latest_sync_id()

        assert latest_id == 0

    @pytest.mark.django_db
    def test_update_sync_state(self, sync_manager):
        sync_state = sync_manager.update_sync_state("node_001", 100)

        assert sync_state.node_id == "node_001"
        assert sync_state.last_synced_id == 100

        sync_state = sync_manager.update_sync_state("node_001", 200)

        assert sync_state.last_synced_id == 200

    @pytest.mark.django_db
    def test_get_sync_state(self, sync_manager):
        sync_manager.update_sync_state("node_001", 150)

        state = sync_manager.get_sync_state("node_001")

        assert state is not None
        assert state.last_synced_id == 150

    @pytest.mark.django_db
    def test_get_sync_state_not_found(self, sync_manager):
        state = sync_manager.get_sync_state("unknown_node")

        assert state is None

    def test_needs_manual_review_critical_tables(self, sync_manager):
        assert sync_manager.needs_manual_review("score") is True
        assert sync_manager.needs_manual_review("ranking") is True
        assert sync_manager.needs_manual_review("elimination") is True
        assert sync_manager.needs_manual_review("pool_bout") is True
        assert sync_manager.needs_manual_review("poolassignment") is True

    def test_needs_manual_review_non_critical_tables(self, sync_manager):
        assert sync_manager.needs_manual_review("tournament") is False
        assert sync_manager.needs_manual_review("fencer") is False
        assert sync_manager.needs_manual_review("club") is False


class TestSyncChange:
    def test_to_dict(self, sample_change):
        result = sample_change.to_dict()

        assert result["id"] == 1
        assert result["table_name"] == "tournament"
        assert result["record_id"] == "test-uuid-123"
        assert result["operation"] == "INSERT"
        assert result["data"]["name"] == "Test Tournament"
        assert result["version"] == 1
        assert "created_at" in result


class TestSyncResult:
    def test_to_dict(self):
        changes = [
            SyncChange(
                id=1,
                table_name="tournament",
                record_id="uuid-1",
                operation="INSERT",
                data={"name": "Test"},
                version=1,
                created_at=datetime.now(),
            )
        ]
        result = SyncResult(last_id=100, has_more=False, changes=changes)

        data = result.to_dict()

        assert data["last_id"] == 100
        assert data["has_more"] is False
        assert len(data["changes"]) == 1


@pytest.mark.django_db
class TestSyncWorkflow:
    def test_full_sync_workflow(self, sync_manager, ack_queue):
        sync_manager.ack_queue = ack_queue
        sync_manager.set_nodes_required(1)
        sync_manager.register_model(
            "tournament",
            MagicMock(),
            MagicMock(),
        )

        sync_log = sync_manager.record_change(
            table_name="tournament",
            record_id="uuid-001",
            operation=SyncOperation.INSERT.value,
            data={"name": "Test Tournament"},
        )

        ack_queue.register(sync_log.id)
        ack_queue.acknowledge(sync_log.id, "node_001")

        is_confirmed = ack_queue.is_confirmed(sync_log.id)
        assert is_confirmed is True

    @pytest.mark.django_db
    def test_batch_changes_workflow(self, sync_manager):
        for i in range(10):
            sync_manager.record_change(
                table_name="tournament",
                record_id=f"uuid-{i}",
                operation=SyncOperation.INSERT.value,
                data={"name": f"Tournament {i}"},
            )

        result = sync_manager.get_changes_since(0, limit=5)

        assert len(result.changes) == 5
        assert result.has_more is True

        result2 = sync_manager.get_changes_since(result.last_id, limit=5)

        assert len(result2.changes) == 5
        assert result2.has_more is False

    def test_ack_queue_multiple_nodes(self, ack_queue):
        ack_queue.set_nodes_required(3)
        ack_queue.register(100)

        ack_queue.acknowledge(100, "node_001")
        assert not ack_queue.is_confirmed(100)

        ack_queue.acknowledge(100, "node_002")
        assert not ack_queue.is_confirmed(100)

        ack_queue.acknowledge(100, "node_003")
        assert ack_queue.is_confirmed(100)


@pytest.mark.django_db
class TestSyncStateManagement:
    def test_sync_state_creation(self):
        state = DjangoSyncState.objects.create(
            node_id="node_001",
            last_synced_id=100,
        )

        assert state.node_id == "node_001"
        assert state.last_synced_id == 100

    def test_sync_state_update(self):
        state = DjangoSyncState.objects.create(
            node_id="node_002",
            last_synced_id=50,
        )

        state.last_synced_id = 100
        state.save()

        state.refresh_from_db()
        assert state.last_synced_id == 100


@pytest.mark.django_db
class TestSyncLogModel:
    def test_sync_log_creation(self):
        log = DjangoSyncLog.objects.create(
            table_name="tournament",
            record_id="uuid-123",
            operation="INSERT",
            data={"name": "Test"},
            version=1,
        )

        assert log.id is not None
        assert log.table_name == "tournament"
        assert log.record_id == "uuid-123"
        assert log.operation == "INSERT"
        assert log.created_at is not None

    def test_sync_log_ordering(self):
        log1 = DjangoSyncLog.objects.create(
            table_name="tournament",
            record_id="uuid-1",
            operation="INSERT",
            data={},
            version=1,
        )
        log2 = DjangoSyncLog.objects.create(
            table_name="tournament",
            record_id="uuid-2",
            operation="INSERT",
            data={},
            version=1,
        )

        logs = list(DjangoSyncLog.objects.all())

        assert logs[0].id == log2.id
        assert logs[1].id == log1.id
