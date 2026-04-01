"""
Unit tests for SyncLog domain model.
"""

from datetime import datetime
from uuid import uuid4

from core.models.sync_log import SyncLog, SyncOperation


class TestSyncLog:
    """Test suite for SyncLog domain model."""

    def test_sync_log_creation_with_required_fields(self):
        """Test creating sync log with only required fields."""
        record_id = str(uuid4())
        sync_log = SyncLog(
            table_name="Tournament",
            record_id=record_id,
            operation="INSERT",
        )

        assert sync_log.table_name == "Tournament"
        assert sync_log.record_id == record_id
        assert sync_log.operation == "INSERT"
        assert sync_log.data == {}
        assert sync_log.version == 1
        assert sync_log.id is None
        assert isinstance(sync_log.created_at, datetime)

    def test_sync_log_with_all_fields(self):
        """Test creating sync log with all fields."""
        record_id = str(uuid4())
        log_id = 123
        data = {"name": "Test Tournament", "status": "active"}

        sync_log = SyncLog(
            table_name="Event",
            record_id=record_id,
            operation="UPDATE",
            data=data,
            version=5,
            id=log_id,
        )

        assert sync_log.table_name == "Event"
        assert sync_log.record_id == record_id
        assert sync_log.operation == "UPDATE"
        assert sync_log.data == data
        assert sync_log.version == 5
        assert sync_log.id == log_id

    def test_sync_log_operation_from_enum(self):
        """Test creating sync log with SyncOperation enum."""
        for operation in [SyncOperation.INSERT, SyncOperation.UPDATE, SyncOperation.DELETE]:
            sync_log = SyncLog(
                table_name="Test",
                record_id=str(uuid4()),
                operation=operation,
            )

            assert sync_log.operation == operation.value

    def test_sync_log_invalid_operation(self):
        """Test that invalid operation raises ValueError."""
        try:
            SyncLog(
                table_name="Test",
                record_id=str(uuid4()),
                operation="INVALID",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid operation" in str(e)
            assert "INVALID" in str(e)

    def test_sync_log_to_dict(self):
        """Test sync log serialization to dictionary."""
        record_id = str(uuid4())
        data = {"name": "Test", "value": 42}

        sync_log = SyncLog(
            table_name="Fencer",
            record_id=record_id,
            operation="DELETE",
            data=data,
            version=3,
            id=1,
        )

        log_dict = sync_log.to_dict()

        assert log_dict["id"] == 1
        assert log_dict["table_name"] == "Fencer"
        assert log_dict["record_id"] == record_id
        assert log_dict["operation"] == "DELETE"
        assert log_dict["data"] == data
        assert log_dict["version"] == 3
        assert "created_at" in log_dict

    def test_sync_log_to_dict_with_none_id(self):
        """Test sync log serialization with None ID."""
        sync_log = SyncLog(
            table_name="Test",
            record_id=str(uuid4()),
            operation="INSERT",
        )

        log_dict = sync_log.to_dict()

        assert log_dict["id"] is None

    def test_sync_log_operations(self):
        """Test all sync operations."""
        operations = ["INSERT", "UPDATE", "DELETE"]

        for operation in operations:
            sync_log = SyncLog(
                table_name="Test",
                record_id=str(uuid4()),
                operation=operation,
            )
            assert sync_log.operation == operation

    def test_sync_log_data_default(self):
        """Test that data defaults to empty dict."""
        sync_log = SyncLog(
            table_name="Test",
            record_id=str(uuid4()),
            operation="INSERT",
        )

        assert sync_log.data == {}

    def test_sync_log_version_default(self):
        """Test that version defaults to 1."""
        sync_log = SyncLog(
            table_name="Test",
            record_id=str(uuid4()),
            operation="INSERT",
        )

        assert sync_log.version == 1

    def test_sync_log_created_at_generated(self):
        """Test that created_at is auto-generated."""
        before = datetime.now()
        sync_log = SyncLog(
            table_name="Test",
            record_id=str(uuid4()),
            operation="INSERT",
        )
        after = datetime.now()

        assert before <= sync_log.created_at <= after
