from django.contrib import admin

from backend.apps.fencing_organizer.modules.fencer.admin import FencerAdmin
from backend.apps.fencing_organizer.modules.tournament_status.admin import TournamentStatusAdmin
from backend.apps.fencing_organizer.modules.tournament.admin import TournamentAdmin
from backend.apps.fencing_organizer.modules.rule.admin import RuleAdmin
from backend.apps.fencing_organizer.modules.elimination_type.admin import EliminationTypeAdmin
from backend.apps.fencing_organizer.modules.ranking_type.admin import RankingTypeAdmin
from backend.apps.fencing_organizer.modules.event.admin import EventAdmin
from backend.apps.fencing_organizer.modules.event_type.admin import EventTypeAdmin
from backend.apps.fencing_organizer.modules.event_status.admin import EventStatusAdmin
from backend.apps.fencing_organizer.modules.match_status.admin import MatchStatusTypeAdmin
from backend.apps.fencing_organizer.modules.piste.admin import PisteAdmin
from .modules.pool.admin import PoolAdmin
from .modules.pool_bout.admin import PoolBoutAdmin