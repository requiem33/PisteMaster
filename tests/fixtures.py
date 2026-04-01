"""
Common pytest fixtures for PisteMaster tests.
Provides reusable fixtures for domain models, test data, and Django models.
"""

import pytest
from uuid import uuid4

from core.models.sync_log import SyncOperation
from tests.factories import (
    TournamentFactory,
    FencerFactory,
    EventFactory,
    PoolFactory,
    MatchFactory,
    PisteFactory,
    RefereeFactory,
    SyncLogFactory,
    SyncStateFactory,
)

# ============================================
# Core Domain Model Fixtures
# ============================================


@pytest.fixture
def tournament():
    """Fixture for a single tournament."""
    return TournamentFactory()


@pytest.fixture
def fencer():
    """Fixture for a single fencer."""
    return FencerFactory()


@pytest.fixture
def event(tournament):
    """Fixture for a single event with associated tournament."""
    return EventFactory(tournament_id=tournament.id)


@pytest.fixture
def pool(event):
    """Fixture for a single pool with associated event."""
    return PoolFactory(event_id=event.id)


@pytest.fixture
def match(event):
    """Fixture for a single match with associated event."""
    return MatchFactory(event_id=event.id, phase_id=uuid4(), status_id=uuid4())


@pytest.fixture
def piste(tournament):
    """Fixture for a single piste with associated tournament."""
    return PisteFactory(tournament_id=tournament.id)


@pytest.fixture
def referee():
    """Fixture for a single referee."""
    return RefereeFactory()


@pytest.fixture
def sync_log():
    """Fixture for a single sync log."""
    return SyncLogFactory()


@pytest.fixture
def sync_state():
    """Fixture for a single sync state."""
    return SyncStateFactory()


# ============================================
# Multiple Entity Fixtures
# ============================================


@pytest.fixture
def multiple_fencers():
    """Fixture for multiple fencers (default 5)."""
    return [FencerFactory() for _ in range(5)]


@pytest.fixture
def multiple_tournaments():
    """Fixture for multiple tournaments (default 3)."""
    return [TournamentFactory() for _ in range(3)]


@pytest.fixture
def multiple_events(tournament):
    """Fixture for multiple events with the same tournament."""
    return [EventFactory(tournament_id=tournament.id) for _ in range(3)]


# ============================================
# Complex Setup Fixtures
# ============================================


@pytest.fixture
def tournament_setup():
    """Fixture for a complete tournament setup with events and pistes."""
    from tests.factories import create_tournament_full_setup

    return create_tournament_full_setup(num_fencers=10, num_events=2, num_pistes=3)


@pytest.fixture
def pool_with_fencers():
    """Fixture for a pool with fencers."""
    from tests.factories import create_pool_with_fencers

    return create_pool_with_fencers(num_fencers=6)


@pytest.fixture
def match_with_fencers():
    """Fixture for a match with two fencers."""
    from tests.factories import create_match_with_fencers

    return create_match_with_fencers()


# ============================================
# Sync Test Fixtures
# ============================================


@pytest.fixture
def sync_logs():
    """Fixture for multiple sync logs for testing sync behavior."""
    return [
        SyncLogFactory(operation=SyncOperation.INSERT),
        SyncLogFactory(operation=SyncOperation.UPDATE),
        SyncLogFactory(operation=SyncOperation.DELETE),
    ]


@pytest.fixture
def sync_states():
    """Fixture for multiple sync states (different nodes)."""
    return [SyncStateFactory() for _ in range(3)]
