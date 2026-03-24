from django.contrib import admin  # noqa: F401

from backend.apps.fencing_organizer.modules.fencer.admin import FencerAdmin  # noqa: F401
from backend.apps.fencing_organizer.modules.tournament_status.admin import TournamentStatusAdmin  # noqa: F401
from backend.apps.fencing_organizer.modules.tournament.admin import TournamentAdmin  # noqa: F401
from backend.apps.fencing_organizer.modules.rule.admin import RuleAdmin  # noqa: F401
from backend.apps.fencing_organizer.modules.elimination_type.admin import EliminationTypeAdmin  # noqa: F401
from backend.apps.fencing_organizer.modules.ranking_type.admin import RankingTypeAdmin  # noqa: F401
from backend.apps.fencing_organizer.modules.event.admin import EventAdmin  # noqa: F401
from backend.apps.fencing_organizer.modules.event_type.admin import EventTypeAdmin  # noqa: F401
from backend.apps.fencing_organizer.modules.event_status.admin import EventStatusAdmin  # noqa: F401
from backend.apps.fencing_organizer.modules.match_status.admin import MatchStatusTypeAdmin  # noqa: F401
from backend.apps.fencing_organizer.modules.piste.admin import PisteAdmin  # noqa: F401
from .modules.pool.admin import PoolAdmin  # noqa: F401
from .modules.pool_bout.admin import PoolBoutAdmin  # noqa: F401
from .modules.event_participant.admin import EventParticipantAdmin  # noqa: F401
from .modules.pool_assignment.admin import PoolAssignmentAdmin  # noqa: F401