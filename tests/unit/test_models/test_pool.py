"""
Unit tests for Pool domain model.
"""

from datetime import datetime
from uuid import UUID


from core.models.pool import Pool


class TestPool:
    """Test suite for Pool domain model."""

    def test_pool_creation_with_required_fields(self):
        """Test creating pool with only required fields."""
        event_id = UUID("12345678-1234-5678-1234-567812345678")
        pool = Pool(event_id=event_id, pool_number=1)

        assert pool.event_id == event_id
        assert pool.pool_number == 1
        assert isinstance(pool.id, UUID)
        assert pool.piste_id is None
        assert pool.start_time is None
        assert pool.fencer_ids == []
        assert pool.results == []
        assert pool.stats == []
        assert pool.status == "SCHEDULED"
        assert pool.is_completed is False

    def test_pool_creation_with_all_fields(self):
        """Test creating pool with all fields."""
        event_id = UUID("12345678-1234-5678-1234-567812345678")
        piste_id = UUID("23456789-2345-6789-2345-678923456789")

        pool = Pool(
            event_id=event_id,
            pool_number=5,
            piste_id=piste_id,
            start_time=datetime(2024, 6, 15, 10, 0),
            fencer_ids=["fencer1", "fencer2", "fencer3"],
            results=[{"fencer": "fencer1", "wins": 2}],
            stats=[{"fencer": "fencer1", "hits_scored": 15}],
            status="IN_PROGRESS",
            is_completed=False,
        )

        assert pool.pool_number == 5
        assert pool.piste_id == piste_id
        assert pool.start_time == datetime(2024, 6, 15, 10, 0)
        assert len(pool.fencer_ids) == 3
        assert len(pool.results) == 1
        assert len(pool.stats) == 1
        assert pool.status == "IN_PROGRESS"

    def test_pool_id_generation(self):
        """Test that each pool gets a unique ID."""
        event_id = UUID("12345678-1234-5678-1234-567812345678")

        pool1 = Pool(event_id=event_id, pool_number=1)
        pool2 = Pool(event_id=event_id, pool_number=2)

        assert pool1.id != pool2.id
        assert isinstance(pool1.id, UUID)
        assert isinstance(pool2.id, UUID)

    def test_pool_status_choices(self):
        """Test different pool statuses."""
        statuses = ["SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]

        for status in statuses:
            pool = Pool(
                event_id=UUID("12345678-1234-5678-1234-567812345678"),
                pool_number=1,
                status=status,
            )
            assert pool.status == status

    def test_pool_default_status(self):
        """Test that default status is SCHEDULED."""
        pool = Pool(
            event_id=UUID("12345678-1234-5678-1234-567812345678"),
            pool_number=1,
        )

        assert pool.status == "SCHEDULED"

    def test_pool_fencer_ids_default(self):
        """Test that fencer_ids defaults to empty list."""
        pool = Pool(
            event_id=UUID("12345678-1234-5678-1234-567812345678"),
            pool_number=1,
        )

        assert pool.fencer_ids == []

    def test_pool_json_fields_mutable(self):
        """Test that JSON fields are mutable."""
        pool = Pool(
            event_id=UUID("12345678-1234-5678-1234-567812345678"),
            pool_number=1,
        )

        pool.fencer_ids.append("fencer1")
        pool.results.append({"match": 1, "score": 5})
        pool.stats.append({"stat": "value"})

        assert len(pool.fencer_ids) == 1
        assert len(pool.results) == 1
        assert len(pool.stats) == 1

    def test_pool_is_completed_flag(self):
        """Test is_completed flag."""
        completed_pool = Pool(
            event_id=UUID("12345678-1234-5678-1234-567812345678"),
            pool_number=1,
            is_completed=True,
        )
        incomplete_pool = Pool(
            event_id=UUID("23456789-2345-6789-2345-678923456789"),
            pool_number=2,
            is_completed=False,
        )

        assert completed_pool.is_completed is True
        assert incomplete_pool.is_completed is False

    def test_pool_field_metadata(self):
        """Test that field metadata is correctly defined."""
        pool = Pool(
            event_id=UUID("12345678-1234-5678-1234-567812345678"),
            pool_number=1,
        )

        fields = pool.__dataclass_fields__
        assert fields["event_id"].metadata["foreign_key"] == "Event"
        assert fields["status"].metadata["max_length"] == 20
