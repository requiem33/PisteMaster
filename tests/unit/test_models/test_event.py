"""
Unit tests for Event domain model.
"""

from datetime import datetime
from uuid import UUID


from core.models.event import Event


class TestEvent:
    """Test suite for Event domain model."""

    def test_event_creation_with_required_fields(self):
        """Test creating event with only required fields."""
        tournament_id = UUID("12345678-1234-5678-1234-567812345678")
        event = Event(
            tournament_id=tournament_id,
            event_name="Men's Individual Foil",
        )

        assert event.tournament_id == tournament_id
        assert event.event_name == "Men's Individual Foil"
        assert isinstance(event.id, UUID)
        assert event.rule_id is None
        assert event.event_type == ""
        assert event.status == "REGISTRATION"
        assert event.is_team_event is False
        assert event.current_step == 0
        assert event.live_ranking == []
        assert event.de_trees == {}
        assert event.custom_rule_config == {}

    def test_event_creation_with_all_fields(self):
        """Test creating event with all fields."""
        tournament_id = UUID("12345678-1234-5678-1234-567812345678")
        rule_id = UUID("23456789-2345-6789-2345-678923456789")

        event = Event(
            tournament_id=tournament_id,
            event_name="Women's Epee",
            rule_id=rule_id,
            event_type="WOMEN_INDIVIDUAL_EPEE",
            status="POOL_STAGE",
            is_team_event=False,
            current_step=2,
            live_ranking=[{"fencer_id": "1", "rank": 1}],
            de_trees={"round_of_64": {"matches": []}},
            custom_rule_config={"pool_size": 6},
            start_time=datetime(2024, 6, 15, 10, 0),
        )

        assert event.tournament_id == tournament_id
        assert event.event_name == "Women's Epee"
        assert event.rule_id == rule_id
        assert event.event_type == "WOMEN_INDIVIDUAL_EPEE"
        assert event.status == "POOL_STAGE"
        assert event.is_team_event is False
        assert event.current_step == 2
        assert len(event.live_ranking) == 1
        assert "round_of_64" in event.de_trees
        assert event.custom_rule_config["pool_size"] == 6
        assert event.start_time == datetime(2024, 6, 15, 10, 0)

    def test_event_id_generation(self):
        """Test that each event gets a unique ID."""
        tournament_id = UUID("12345678-1234-5678-1234-567812345678")

        event1 = Event(tournament_id=tournament_id, event_name="Event 1")
        event2 = Event(tournament_id=tournament_id, event_name="Event 2")

        assert event1.id != event2.id
        assert isinstance(event1.id, UUID)
        assert isinstance(event2.id, UUID)

    def test_event_default_status(self):
        """Test that default status is REGISTRATION."""
        event = Event(
            tournament_id=UUID("12345678-1234-5678-1234-567812345678"),
            event_name="Test Event",
        )

        assert event.status == "REGISTRATION"

    def test_event_team_event_flag(self):
        """Test is_team_event flag."""
        individual_event = Event(
            tournament_id=UUID("12345678-1234-5678-1234-567812345678"),
            event_name="Individual Event",
            is_team_event=False,
        )
        team_event = Event(
            tournament_id=UUID("12345678-1234-5678-1234-567812345678"),
            event_name="Team Event",
            is_team_event=True,
        )

        assert individual_event.is_team_event is False
        assert team_event.is_team_event is True

    def test_event_json_fields(self):
        """Test that JSON fields are mutable."""
        event = Event(
            tournament_id=UUID("12345678-1234-5678-1234-567812345678"),
            event_name="Test Event",
        )

        event.live_ranking.append({"fencer_id": "1", "rank": 1})
        event.de_trees["round_1"] = {"matches": []}
        event.custom_rule_config["key"] = "value"

        assert len(event.live_ranking) == 1
        assert "round_1" in event.de_trees
        assert event.custom_rule_config["key"] == "value"

    def test_event_timestamps(self):
        """Test that timestamps are generated correctly."""
        before_creation = datetime.now()
        event = Event(
            tournament_id=UUID("12345678-1234-5678-1234-567812345678"),
            event_name="Test Event",
        )
        after_creation = datetime.now()

        assert before_creation <= event.created_at <= after_creation
        assert before_creation <= event.updated_at <= after_creation

    def test_event_field_metadata(self):
        """Test that field metadata is correctly defined."""
        event = Event(
            tournament_id=UUID("12345678-1234-5678-1234-567812345678"),
            event_name="Test Event",
        )

        fields = event.__dataclass_fields__
        assert fields["event_name"].metadata["max_length"] == 200
        assert fields["tournament_id"].metadata["foreign_key"] == "Tournament"
