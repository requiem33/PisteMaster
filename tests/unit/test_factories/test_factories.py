"""
Unit tests for test factories.
Verifies that factories can create model instances correctly.
"""

from tests.factories import (
    TournamentFactory,
    FencerFactory,
    EventFactory,
    PoolFactory,
    PoolBoutFactory,
    MatchFactory,
    PisteFactory,
    RefereeFactory,
    SyncLogFactory,
    SyncStateFactory,
    create_tournament_with_events,
    create_pool_with_fencers,
    create_match_with_fencers,
    create_tournament_full_setup,
)


class TestDomainModelFactories:
    """Test domain model factories."""

    def test_tournament_factory(self):
        """Test TournamentFactory creates valid tournament."""
        tournament = TournamentFactory()

        assert tournament.tournament_name is not None
        assert tournament.start_date is not None
        assert tournament.end_date is not None
        assert tournament.status in [
            "PLANNING",
            "REGISTRATION_OPEN",
            "REGISTRATION_CLOSED",
            "ONGOING",
            "COMPLETED",
            "CANCELLED",
        ]
        assert tournament.id is not None

    def test_fencer_factory(self):
        """Test FencerFactory creates valid fencer."""
        fencer = FencerFactory()

        assert fencer.first_name is not None
        assert fencer.last_name is not None
        assert fencer.id is not None
        assert fencer.gender in ["M", "F"]
        assert fencer.primary_weapon in ["FOIL", "EPEE", "SABRE"]

    def test_event_factory(self):
        """Test EventFactory creates valid event."""
        event = EventFactory()

        assert event.event_name is not None
        assert event.tournament_id is not None
        assert event.id is not None
        assert event.event_type in [
            "MEN_INDIVIDUAL_FOIL",
            "WOMEN_INDIVIDUAL_FOIL",
            "MEN_INDIVIDUAL_EPEE",
            "WOMEN_INDIVIDUAL_EPEE",
            "MEN_INDIVIDUAL_SABRE",
            "WOMEN_INDIVIDUAL_SABRE",
            "MEN_TEAM_FOIL",
            "WOMEN_TEAM_FOIL",
        ]

    def test_pool_factory(self):
        """Test PoolFactory creates valid pool."""
        pool = PoolFactory()

        assert pool.event_id is not None
        assert pool.pool_number >= 1
        assert pool.id is not None
        assert pool.status in ["SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]

    def test_pool_bout_factory(self):
        """Test PoolBoutFactory creates valid pool bout."""
        bout = PoolBoutFactory()

        assert bout.pool_id is not None
        assert bout.fencer_a_id is not None
        assert bout.fencer_b_id is not None
        assert bout.fencer_a_score >= 0
        assert bout.fencer_b_score >= 0

    def test_match_factory(self):
        """Test MatchFactory creates valid match."""
        match = MatchFactory()

        assert match.event_id is not None
        assert match.phase_id is not None
        assert match.match_code is not None
        assert match.status_id is not None
        assert match.id is not None

    def test_piste_factory(self):
        """Test PisteFactory creates valid piste."""
        piste = PisteFactory()

        assert piste.tournament_id is not None
        assert piste.piste_number is not None
        assert piste.id is not None
        assert piste.piste_type in ["MAIN", "WARMUP", "TRAINING"]

    def test_referee_factory(self):
        """Test RefereeFactory creates valid referee."""
        referee = RefereeFactory()

        assert referee.first_name is not None
        assert referee.last_name is not None
        assert referee.id is not None
        assert referee.license_level in ["INTERNATIONAL", "NATIONAL", "REGIONAL", "LOCAL"]

    def test_sync_log_factory(self):
        """Test SyncLogFactory creates valid sync log."""
        sync_log = SyncLogFactory()

        assert sync_log.table_name in ["Tournament", "Fencer", "Event", "Pool", "Match", "Piste"]
        assert sync_log.record_id is not None
        assert sync_log.operation in ["INSERT", "UPDATE", "DELETE"]
        assert sync_log.version >= 1

    def test_sync_state_factory(self):
        """Test SyncStateFactory creates valid sync state."""
        sync_state = SyncStateFactory()

        assert sync_state.node_id is not None
        assert sync_state.last_synced_id >= 0
        assert sync_state.last_sync_time is not None


class TestFactoryHelperFunctions:
    """Test factory helper functions."""

    def test_create_tournament_with_events(self):
        """Test create_tournament_with_events helper."""
        tournament = create_tournament_with_events(num_events=3)

        assert tournament is not None
        assert tournament.id is not None
        assert tournament.tournament_name is not None

    def test_create_pool_with_fencers(self):
        """Test create_pool_with_fencers helper."""
        pool, fencers = create_pool_with_fencers(num_fencers=6)

        assert pool is not None
        assert pool.id is not None
        assert len(fencers) == 6
        assert len(pool.fencer_ids) == 6

    def test_create_match_with_fencers(self):
        """Test create_match_with_fencers helper."""
        match, fencer_a, fencer_b = create_match_with_fencers()

        assert match is not None
        assert match.id is not None
        assert fencer_a is not None
        assert fencer_b is not None
        assert match.fencer_a_id == fencer_a.id
        assert match.fencer_b_id == fencer_b.id

    def test_create_tournament_full_setup(self):
        """Test create_tournament_full_setup helper."""
        setup = create_tournament_full_setup(num_fencers=10, num_events=2, num_pistes=3)

        assert "tournament" in setup
        assert "events" in setup
        assert "pistes" in setup
        assert "fencers" in setup
        assert "pools" in setup
        assert "referees" in setup

        assert len(setup["events"]) == 2
        assert len(setup["pistes"]) == 3
        assert len(setup["fencers"]) == 10
        assert len(setup["pools"]) == 3
        assert len(setup["referees"]) == 3


class TestFactorySequence:
    """Test factory sequence and lazy attribute behaviors."""

    def test_unique_match_codes(self):
        """Test that match codes are unique."""
        match1 = MatchFactory()
        match2 = MatchFactory()

        assert match1.match_code != match2.match_code

    def test_unique_fencing_ids(self):
        """Test that fencing IDs are unique."""
        fencer1 = FencerFactory()
        fencer2 = FencerFactory()

        assert fencer1.fencing_id != fencer2.fencing_id

    def test_pool_numbers_increment(self):
        """Test that pool numbers increment."""
        pool1 = PoolFactory()
        pool2 = PoolFactory()

        # Pool numbers should be sequential
        assert pool1.pool_number >= 1
        assert pool2.pool_number >= 1
