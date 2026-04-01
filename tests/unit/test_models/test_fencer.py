"""
Unit tests for Fencer domain model.
"""

from datetime import date, datetime
from uuid import UUID


from core.models.fencer import Fencer


class TestFencer:
    """Test suite for Fencer domain model."""

    def test_fencer_creation_with_required_fields(self):
        """Test creating fencer with only required fields."""
        fencer = Fencer(
            first_name="John",
            last_name="Doe",
        )

        assert fencer.first_name == "John"
        assert fencer.last_name == "Doe"
        assert isinstance(fencer.id, UUID)
        assert fencer.display_name is None
        assert fencer.gender is None
        assert fencer.country_code is None
        assert fencer.birth_date is None
        assert fencer.fencing_id is None
        assert fencer.current_ranking is None
        assert fencer.primary_weapon is None

    def test_fencer_creation_with_all_fields(self):
        """Test creating fencer with all fields."""
        fencer = Fencer(
            first_name="Jane",
            last_name="Smith",
            display_name="Smith Jane",
            gender="F",
            country_code="USA",
            birth_date=date(1990, 5, 15),
            fencing_id="FEN123456",
            current_ranking=42,
            primary_weapon="FOIL",
        )

        assert fencer.first_name == "Jane"
        assert fencer.last_name == "Smith"
        assert fencer.display_name == "Smith Jane"
        assert fencer.gender == "F"
        assert fencer.country_code == "USA"
        assert fencer.birth_date == date(1990, 5, 15)
        assert fencer.fencing_id == "FEN123456"
        assert fencer.current_ranking == 42
        assert fencer.primary_weapon == "FOIL"

    def test_fencer_id_generation(self):
        """Test that each fencer gets a unique ID."""
        fencer1 = Fencer(first_name="John", last_name="Doe")
        fencer2 = Fencer(first_name="Jane", last_name="Smith")

        assert fencer1.id != fencer2.id
        assert isinstance(fencer1.id, UUID)
        assert isinstance(fencer2.id, UUID)

    def test_fencer_field_metadata(self):
        """Test that field metadata is correctly defined."""
        fencer = Fencer(first_name="John", last_name="Doe")

        fields = fencer.__dataclass_fields__
        assert fields["first_name"].metadata["max_length"] == 100
        assert fields["last_name"].metadata["max_length"] == 100
        assert fields["country_code"].metadata["max_length"] == 3

    def test_fencer_timestamps(self):
        """Test that timestamps are generated correctly."""
        before_creation = datetime.now()
        fencer = Fencer(first_name="John", last_name="Doe")
        after_creation = datetime.now()

        assert before_creation <= fencer.created_at <= after_creation
        assert before_creation <= fencer.updated_at <= after_creation

    def test_fencer_with_fencing_id(self):
        """Test fencer with international fencing ID."""
        fencer = Fencer(
            first_name="International",
            last_name="Fencer",
            fencing_id="FEN999999",
        )

        assert fencer.fencing_id == "FEN999999"

    def test_fencer_primary_weapon_choices(self):
        """Test different weapon choices for fencer."""
        weapons = ["FOIL", "EPEE", "SABRE"]

        for weapon in weapons:
            fencer = Fencer(
                first_name="Test",
                last_name="Fencer",
                primary_weapon=weapon,
            )
            assert fencer.primary_weapon == weapon

    def test_fencer_display_name_optional(self):
        """Test that display name is optional."""
        fencer_no_display = Fencer(first_name="John", last_name="Doe")
        fencer_with_display = Fencer(
            first_name="Jane",
            last_name="Smith",
            display_name="Smith Jane",
        )

        assert fencer_no_display.display_name is None
        assert fencer_with_display.display_name == "Smith Jane"
