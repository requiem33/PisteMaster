"""
Test Factories for PisteMaster
Uses factory-boy to generate test data for domain models and Django models.
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import factory
from factory import Faker, LazyFunction
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyDate

from core.models.tournament import Tournament
from core.models.fencer import Fencer
from core.models.event import Event
from core.models.pool import Pool
from core.models.pool_bout import PoolBout
from core.models.match import Match
from core.models.piste import Piste
from core.models.referee import Referee
from core.models.sync_log import SyncLog, SyncOperation
from core.models.sync_state import SyncState


class TournamentFactory(factory.Factory):
    """Factory for creating Tournament domain model instances."""

    class Meta:
        model = Tournament

    tournament_name = Faker("company")
    start_date = FuzzyDate(start_date=date.today(), end_date=date.today() + timedelta(days=30))
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timedelta(days=7))
    status = FuzzyChoice(choices=["PLANNING", "REGISTRATION_OPEN", "REGISTRATION_CLOSED", "ONGOING", "COMPLETED", "CANCELLED"])
    id = LazyFunction(uuid4)
    organizer = Faker("company")
    location = Faker("city")
    created_by_id = LazyFunction(uuid4)
    scheduler_ids = factory.LazyFunction(lambda: [uuid4()])
    created_at = LazyFunction(datetime.now)
    updated_at = LazyFunction(datetime.now)


class FencerFactory(factory.Factory):
    """Factory for creating Fencer domain model instances."""

    class Meta:
        model = Fencer

    first_name = Faker("first_name")
    last_name = Faker("last_name")
    id = LazyFunction(uuid4)
    display_name = factory.LazyAttribute(lambda obj: f"{obj.last_name} {obj.first_name}")
    gender = FuzzyChoice(choices=["M", "F"])
    country_code = Faker("country_code")
    birth_date = FuzzyDate(start_date=date(1970, 1, 1), end_date=date(2005, 12, 31))
    fencing_id = factory.LazyFunction(lambda: f"FEN{FuzzyInteger(100000, 999999).fuzz()}")
    current_ranking = FuzzyInteger(1, 1000)
    primary_weapon = FuzzyChoice(choices=["FOIL", "EPEE", "SABRE"])
    created_at = LazyFunction(datetime.now)
    updated_at = LazyFunction(datetime.now)


class EventFactory(factory.Factory):
    """Factory for creating Event domain model instances."""

    class Meta:
        model = Event

    tournament_id = LazyFunction(uuid4)
    event_name = Faker("sentence", nb_words=4)
    id = LazyFunction(uuid4)
    rule_id = LazyFunction(uuid4)
    event_type = FuzzyChoice(
        choices=[
            "MEN_INDIVIDUAL_FOIL",
            "WOMEN_INDIVIDUAL_FOIL",
            "MEN_INDIVIDUAL_EPEE",
            "WOMEN_INDIVIDUAL_EPEE",
            "MEN_INDIVIDUAL_SABRE",
            "WOMEN_INDIVIDUAL_SABRE",
            "MEN_TEAM_FOIL",
            "WOMEN_TEAM_FOIL",
        ]
    )
    status = FuzzyChoice(choices=["REGISTRATION", "POOL_STAGE", "ELIMINATION", "FINAL", "COMPLETED"])
    is_team_event = FuzzyChoice(choices=[True, False])
    current_step = FuzzyInteger(0, 10)
    live_ranking = factory.LazyFunction(list)
    de_trees = factory.LazyFunction(dict)
    custom_rule_config = factory.LazyFunction(dict)
    start_time = LazyFunction(datetime.now)
    created_at = LazyFunction(datetime.now)
    updated_at = LazyFunction(datetime.now)


class PisteFactory(factory.Factory):
    """Factory for creating Piste domain model instances."""

    class Meta:
        model = Piste

    tournament_id = LazyFunction(uuid4)
    piste_number = factory.Sequence(lambda n: f"{n+1}")
    id = LazyFunction(uuid4)
    location = Faker("city")
    piste_type = FuzzyChoice(choices=["MAIN", "WARMUP", "TRAINING"])
    is_available = FuzzyChoice(choices=[True, False])
    notes = Faker("text", max_nb_chars=100)


class PoolFactory(factory.Factory):
    """Factory for creating Pool domain model instances."""

    class Meta:
        model = Pool

    event_id = LazyFunction(uuid4)
    pool_number = factory.Sequence(lambda n: n + 1)
    id = LazyFunction(uuid4)
    piste_id = LazyFunction(uuid4)
    start_time = LazyFunction(datetime.now)
    fencer_ids = factory.LazyFunction(list)
    results = factory.LazyFunction(list)
    stats = factory.LazyFunction(list)
    status = FuzzyChoice(choices=["SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"])
    is_completed = FuzzyChoice(choices=[True, False])


class PoolBoutFactory(factory.Factory):
    """Factory for creating PoolBout domain model instances."""

    class Meta:
        model = PoolBout

    pool_id = LazyFunction(uuid4)
    fencer_a_id = LazyFunction(uuid4)
    fencer_b_id = LazyFunction(uuid4)
    status_id = LazyFunction(uuid4)
    id = LazyFunction(uuid4)
    winner_id = None
    fencer_a_score = FuzzyInteger(0, 5)
    fencer_b_score = FuzzyInteger(0, 5)
    scheduled_time = LazyFunction(datetime.now)
    actual_start_time = None
    actual_end_time = None
    duration_seconds = FuzzyInteger(60, 600)
    notes = None


class MatchFactory(factory.Factory):
    """Factory for creating Match domain model instances."""

    class Meta:
        model = Match

    event_id = LazyFunction(uuid4)
    phase_id = LazyFunction(uuid4)
    match_code = factory.Sequence(lambda n: f"M{n+1:03d}")
    status_id = LazyFunction(uuid4)
    id = LazyFunction(uuid4)
    fencer_a_id = LazyFunction(uuid4)
    fencer_b_id = LazyFunction(uuid4)
    winner_id = None
    fencer_a_score = FuzzyInteger(0, 15)
    fencer_b_score = FuzzyInteger(0, 15)
    match_number = factory.Sequence(lambda n: n + 1)
    piste_id = LazyFunction(uuid4)
    scheduled_time = LazyFunction(datetime.now)
    actual_start_time = None
    actual_end_time = None
    duration_minutes = FuzzyInteger(5, 30)
    forfeit_type_id = None
    forfeit_notes = None
    created_at = LazyFunction(datetime.now)
    updated_at = LazyFunction(datetime.now)


class RefereeFactory(factory.Factory):
    """Factory for creating Referee domain model instances."""

    class Meta:
        model = Referee

    first_name = Faker("first_name")
    last_name = Faker("last_name")
    id = LazyFunction(uuid4)
    display_name = factory.LazyAttribute(lambda obj: f"{obj.first_name} {obj.last_name}")
    country_code = Faker("country_code")
    license_number = factory.LazyFunction(lambda: f"REF{FuzzyInteger(100000, 999999).fuzz()}")
    license_level = FuzzyChoice(choices=["INTERNATIONAL", "NATIONAL", "REGIONAL", "LOCAL"])
    is_active = FuzzyChoice(choices=[True, False])
    created_at = LazyFunction(datetime.now)
    updated_at = LazyFunction(datetime.now)


class SyncLogFactory(factory.Factory):
    """Factory for creating SyncLog domain model instances."""

    class Meta:
        model = SyncLog

    table_name = FuzzyChoice(choices=["Tournament", "Fencer", "Event", "Pool", "Match", "Piste"])
    record_id = factory.LazyFunction(lambda: str(uuid4()))
    operation = FuzzyChoice(choices=[SyncOperation.INSERT, SyncOperation.UPDATE, SyncOperation.DELETE])
    data = factory.LazyFunction(dict)
    version = FuzzyInteger(1, 100)
    id = None
    created_at = LazyFunction(datetime.now)


class SyncStateFactory(factory.Factory):
    """Factory for creating SyncState domain model instances."""

    class Meta:
        model = SyncState

    node_id = factory.Sequence(lambda n: f"node-{n+1}")
    last_synced_id = FuzzyInteger(0, 10000)
    last_sync_time = LazyFunction(datetime.now)
    id = None


def create_tournament_with_events(num_events: int = 3) -> Tournament:
    """Create a tournament with associated events."""
    tournament = TournamentFactory()
    for _ in range(num_events):
        EventFactory(tournament_id=tournament.id)
    return tournament


def create_pool_with_fencers(num_fencers: int = 6) -> tuple[Pool, list[Fencer]]:
    """Create a pool with fencers for testing pool functionality."""
    fencers = [FencerFactory() for _ in range(num_fencers)]
    pool = PoolFactory(event_id=uuid4(), fencer_ids=[str(f.id) for f in fencers])
    return pool, fencers


def create_match_with_fencers() -> tuple[Match, Fencer, Fencer]:
    """Create a match with two fencers for testing match functionality."""
    fencer_a = FencerFactory()
    fencer_b = FencerFactory()
    match = MatchFactory(
        event_id=uuid4(),
        phase_id=uuid4(),
        status_id=uuid4(),
        fencer_a_id=fencer_a.id,
        fencer_b_id=fencer_b.id,
    )
    return match, fencer_a, fencer_b


def create_tournament_full_setup(num_fencers: int = 10, num_events: int = 2, num_pistes: int = 3) -> dict:
    """
    Create a complete tournament setup for integration testing.
    Returns a dict with all created entities.
    """
    tournament = TournamentFactory()

    events = [EventFactory(tournament_id=tournament.id) for _ in range(num_events)]

    pistes = [PisteFactory(tournament_id=tournament.id) for _ in range(num_pistes)]

    fencers = [FencerFactory() for _ in range(num_fencers)]

    pools = [PoolFactory(event_id=events[0].id, piste_id=pistes[0].id) for _ in range(3)]

    referees = [RefereeFactory() for _ in range(3)]

    return {
        "tournament": tournament,
        "events": events,
        "pistes": pistes,
        "fencers": fencers,
        "pools": pools,
        "referees": referees,
    }
