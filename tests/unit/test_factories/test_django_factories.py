"""
Tests for Django model factories.
Requires database access (pytest-django).
"""

import pytest

from tests.django_factories import UserFactory, DjangoTournamentFactory, DjangoFencerFactory


@pytest.mark.django_db
class TestDjangoModelFactories:
    """Test Django model factories."""

    def test_user_factory(self):
        """Test UserFactory creates valid user."""
        user = UserFactory()

        assert user.username is not None
        assert user.email is not None
        assert user.role in ["ADMIN", "SCHEDULER"]
        assert user.is_active is True
        assert user.check_password("testpassword123") is True

    def test_user_factory_with_custom_password(self):
        """Test UserFactory with custom password."""
        user = UserFactory(password="custompassword")

        assert user.check_password("custompassword") is True

    def test_django_tournament_factory(self):
        """Test DjangoTournamentFactory creates valid tournament."""
        tournament = DjangoTournamentFactory()

        assert tournament.tournament_name is not None
        assert tournament.start_date is not None
        assert tournament.end_date >= tournament.start_date
        assert tournament.status in [
            "PLANNING",
            "REGISTRATION_OPEN",
            "REGISTRATION_CLOSED",
            "ONGOING",
            "COMPLETED",
            "CANCELLED",
        ]
        assert tournament.id is not None

    def test_django_tournament_with_schedulers(self):
        """Test DjangoTournamentFactory with schedulers."""
        scheduler1 = UserFactory(role="SCHEDULER")
        scheduler2 = UserFactory(role="SCHEDULER")

        tournament = DjangoTournamentFactory(schedulers=[scheduler1, scheduler2])

        assert tournament.schedulers.count() == 2
        assert scheduler1 in tournament.schedulers.all()
        assert scheduler2 in tournament.schedulers.all()

    def test_django_fencer_factory(self):
        """Test DjangoFencerFactory creates valid fencer."""
        fencer = DjangoFencerFactory()

        assert fencer.first_name is not None
        assert fencer.last_name is not None
        assert fencer.id is not None
        assert fencer.gender in ["MEN", "WOMEN", "MIXED", "OPEN"]
        assert fencer.primary_weapon in ["FOIL", "EPEE", "SABRE"]
        assert fencer.display_name == f"{fencer.last_name} {fencer.first_name}"

    def test_multiple_fencers_unique_fencing_ids(self):
        """Test that fencing IDs are unique across fencers."""
        fencer1 = DjangoFencerFactory()
        fencer2 = DjangoFencerFactory()

        assert fencer1.fencing_id != fencer2.fencing_id or (fencer1.fencing_id is None and fencer2.fencing_id is None)
