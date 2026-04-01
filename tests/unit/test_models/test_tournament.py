"""
Unit tests for Tournament domain model.
"""

from datetime import date, datetime
from uuid import UUID


from core.models.tournament import Tournament


class TestTournament:
    """Test suite for Tournament domain model."""

    def test_tournament_creation_with_required_fields(self):
        """Test creating tournament with only required fields."""
        tournament = Tournament(
            tournament_name="Test Tournament",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        assert tournament.tournament_name == "Test Tournament"
        assert tournament.start_date == date(2024, 1, 1)
        assert tournament.end_date == date(2024, 1, 7)
        assert tournament.status == "PLANNING"
        assert isinstance(tournament.id, UUID)
        assert tournament.organizer is None
        assert tournament.location is None
        assert tournament.created_by_id is None
        assert tournament.scheduler_ids == []
        assert isinstance(tournament.created_at, datetime)
        assert isinstance(tournament.updated_at, datetime)

    def test_tournament_creation_with_all_fields(self):
        """Test creating tournament with all fields."""
        tournament = Tournament(
            tournament_name="Full Tournament",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 7),
            status="REGISTRATION_OPEN",
            organizer="Fencing Club",
            location="Paris, France",
        )

        assert tournament.tournament_name == "Full Tournament"
        assert tournament.status == "REGISTRATION_OPEN"
        assert tournament.organizer == "Fencing Club"
        assert tournament.location == "Paris, France"

    def test_tournament_status_choices(self):
        """Test all status choices."""
        valid_statuses = [
            "PLANNING",
            "REGISTRATION_OPEN",
            "REGISTRATION_CLOSED",
            "ONGOING",
            "COMPLETED",
            "CANCELLED",
        ]

        for status in valid_statuses:
            tournament = Tournament(
                tournament_name="Test",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 7),
                status=status,
            )
            assert tournament.status == status

    def test_tournament_default_values(self):
        """Test default values for tournament fields."""
        tournament = Tournament(
            tournament_name="Default Test",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        assert tournament.status == "PLANNING"
        assert tournament.id is not None
        assert tournament.scheduler_ids == []

    def test_tournament_id_generation(self):
        """Test that each tournament gets a unique ID."""
        tournament1 = Tournament(
            tournament_name="Tournament 1",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )
        tournament2 = Tournament(
            tournament_name="Tournament 2",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        assert tournament1.id != tournament2.id
        assert isinstance(tournament1.id, UUID)
        assert isinstance(tournament2.id, UUID)

    def test_tournament_with_scheduler_ids(self):
        """Test tournament with scheduler IDs."""
        scheduler_ids = [
            UUID("12345678-1234-5678-1234-567812345678"),
            UUID("23456789-2345-6789-2345-678923456789"),
        ]

        tournament = Tournament(
            tournament_name="Test",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
            scheduler_ids=scheduler_ids,
        )

        assert tournament.scheduler_ids == scheduler_ids
        assert len(tournament.scheduler_ids) == 2

    def test_tournament_timestamps(self):
        """Test that timestamps are generated correctly."""
        before_creation = datetime.now()
        tournament = Tournament(
            tournament_name="Test",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )
        after_creation = datetime.now()

        assert before_creation <= tournament.created_at <= after_creation
        assert before_creation <= tournament.updated_at <= after_creation

    def test_tournament_field_metadata(self):
        """Test that field metadata is correctly defined."""
        tournament = Tournament(
            tournament_name="Test",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )

        fields = tournament.__dataclass_fields__
        assert fields["tournament_name"].metadata["max_length"] == 200
        assert fields["status"].metadata["choices"] == [
            "PLANNING",
            "REGISTRATION_OPEN",
            "REGISTRATION_CLOSED",
            "ONGOING",
            "COMPLETED",
            "CANCELLED",
        ]
