from abc import ABC, abstractmethod
from uuid import UUID

from core.models.fencer import Fencer
from core.models.bout import Bout
from core.models.elinimation_type import EliminationType
from core.models.event import Event
from core.models.event_phase import EventPhase
from core.models.event_seed import EventSeed
from core.models.event_type import EventType
from core.models.forfeit_type import ForfeitType
from core.models.match import Match
from core.models.match_referee_assignment import MatchRefereeAssignment
from core.models.match_status_type import MatchStatusType
from core.models.match_tree import MatchTree
from core.models.piste import Piste
from core.models.pool import Pool
from core.models.pool_assignment import PoolAssignment
from core.models.pool_bout import PoolBout
from core.models.ranking_type import RankingType
from core.models.referee import Referee
from core.models.referee_role import RefereeRole
from core.models.rule import Rule
from core.models.seed_type import SeedType
from core.models.source_type import SourceType
from core.models.team import Team
from core.models.team_match import TeamMatch
from core.models.team_match_tree import TeamMatchTree
from core.models.team_membership import TeamMembership
from core.models.team_role import TeamRole
from core.models.tournament import Tournament
from core.models.tournament_status import TournamentStatus


class FencerRepositoryInterface(ABC):
    """Fencer 仓库的抽象定义。核心服务只依赖此接口。"""

    @abstractmethod
    def get_fencer_by_id(self, fencer_id: UUID) -> Fencer | None:
        pass

    @abstractmethod
    def save_fencer(self, fencer: Fencer) -> Fencer:
        pass


class BoutRepositoryInterface(ABC):
    """Bout 仓库的抽象定义。"""

    @abstractmethod
    def get_bout_by_id(self, bout_id: UUID) -> Bout | None:
        pass

    @abstractmethod
    def save_bout(self, bout: Bout) -> Bout:
        pass


class ElinimationTypeRepositoryInterface(ABC):
    """ElinimationType 仓库的抽象定义。"""

    @abstractmethod
    def get_elinimation_type_by_id(self, elinimation_type_id: UUID) -> EliminationType | None:
        pass

    @abstractmethod
    def save_elinimation_type(self, elinimation_type: EliminationType) -> EliminationType:
        pass


class EventRepositoryInterface(ABC):
    """Event 仓库的抽象定义。"""

    @abstractmethod
    def get_event_by_id(self, event_id: UUID) -> Event | None:
        pass

    @abstractmethod
    def save_event(self, event: Event) -> Event:
        pass


class EventPhaseRepositoryInterface(ABC):
    """EventPhase 仓库的抽象定义。"""

    @abstractmethod
    def get_event_phase_by_id(self, event_phase_id: UUID) -> EventPhase | None:
        pass

    @abstractmethod
    def save_event_phase(self, event_phase: EventPhase) -> EventPhase:
        pass


class EventSeedRepositoryInterface(ABC):
    """EventSeed 仓库的抽象定义。"""

    @abstractmethod
    def get_event_seed_by_id(self, event_seed_id: UUID) -> EventSeed | None:
        pass

    @abstractmethod
    def save_event_seed(self, event_seed: EventSeed) -> EventSeed:
        pass


class EventTypeRepositoryInterface(ABC):
    """EventType 仓库的抽象定义。"""

    @abstractmethod
    def get_event_type_by_id(self, event_type_id: UUID) -> EventType | None:
        pass

    @abstractmethod
    def save_event_type(self, event_type: EventType) -> EventType:
        pass


class ForfeitTypeRepositoryInterface(ABC):
    """ForfeitType 仓库的抽象定义。"""

    @abstractmethod
    def get_forfeit_type_by_id(self, forfeit_type_id: UUID) -> ForfeitType | None:
        pass

    @abstractmethod
    def save_forfeit_type(self, forfeit_type: ForfeitType) -> ForfeitType:
        pass


class MatchRepositoryInterface(ABC):
    """Match 仓库的抽象定义。"""

    @abstractmethod
    def get_match_by_id(self, match_id: UUID) -> Match | None:
        pass

    @abstractmethod
    def save_match(self, match: Match) -> Match:
        pass


class MatchRefereeAssignmentRepositoryInterface(ABC):
    """MatchRefereeAssignment 仓库的抽象定义。"""

    @abstractmethod
    def get_match_referee_assignment_by_id(self, assignment_id: UUID) -> MatchRefereeAssignment | None:
        pass

    @abstractmethod
    def save_match_referee_assignment(self, assignment: MatchRefereeAssignment) -> MatchRefereeAssignment:
        pass


class MatchStatusTypeRepositoryInterface(ABC):
    """MatchStatusType 仓库的抽象定义。"""

    @abstractmethod
    def get_match_status_type_by_id(self, status_type_id: UUID) -> MatchStatusType | None:
        pass

    @abstractmethod
    def save_match_status_type(self, status_type: MatchStatusType) -> MatchStatusType:
        pass


class MatchTreeRepositoryInterface(ABC):
    """MatchTree 仓库的抽象定义。"""

    @abstractmethod
    def get_match_tree_by_id(self, match_tree_id: UUID) -> MatchTree | None:
        pass

    @abstractmethod
    def save_match_tree(self, match_tree: MatchTree) -> MatchTree:
        pass


class PisteRepositoryInterface(ABC):
    """Piste 仓库的抽象定义。"""

    @abstractmethod
    def get_piste_by_id(self, piste_id: UUID) -> Piste | None:
        pass

    @abstractmethod
    def save_piste(self, piste: Piste) -> Piste:
        pass


class PoolRepositoryInterface(ABC):
    """Pool 仓库的抽象定义。"""

    @abstractmethod
    def get_pool_by_id(self, pool_id: UUID) -> Pool | None:
        pass

    @abstractmethod
    def save_pool(self, pool: Pool) -> Pool:
        pass


class PoolAssignmentRepositoryInterface(ABC):
    """PoolAssignment 仓库的抽象定义。"""

    @abstractmethod
    def get_pool_assignment_by_id(self, assignment_id: UUID) -> PoolAssignment | None:
        pass

    @abstractmethod
    def save_pool_assignment(self, assignment: PoolAssignment) -> PoolAssignment:
        pass


class PoolBoutRepositoryInterface(ABC):
    """PoolBout 仓库的抽象定义。"""

    @abstractmethod
    def get_pool_bout_by_id(self, pool_bout_id: UUID) -> PoolBout | None:
        pass

    @abstractmethod
    def save_pool_bout(self, pool_bout: PoolBout) -> PoolBout:
        pass


class RankingTypeRepositoryInterface(ABC):
    """RankingType 仓库的抽象定义。"""

    @abstractmethod
    def get_ranking_type_by_id(self, ranking_type_id: UUID) -> RankingType | None:
        pass

    @abstractmethod
    def save_ranking_type(self, ranking_type: RankingType) -> RankingType:
        pass


class RefereeRepositoryInterface(ABC):
    """Referee 仓库的抽象定义。"""

    @abstractmethod
    def get_referee_by_id(self, referee_id: UUID) -> Referee | None:
        pass

    @abstractmethod
    def save_referee(self, referee: Referee) -> Referee:
        pass


class RefereeRoleRepositoryInterface(ABC):
    """RefereeRole 仓库的抽象定义。"""

    @abstractmethod
    def get_referee_role_by_id(self, referee_role_id: UUID) -> RefereeRole | None:
        pass

    @abstractmethod
    def save_referee_role(self, referee_role: RefereeRole) -> RefereeRole:
        pass


class RuleRepositoryInterface(ABC):
    """Rule 仓库的抽象定义。"""

    @abstractmethod
    def get_rule_by_id(self, rule_id: UUID) -> Rule | None:
        pass

    @abstractmethod
    def save_rule(self, rule: Rule) -> Rule:
        pass


class SeedTypeRepositoryInterface(ABC):
    """SeedType 仓库的抽象定义。"""

    @abstractmethod
    def get_seed_type_by_id(self, seed_type_id: UUID) -> SeedType | None:
        pass

    @abstractmethod
    def save_seed_type(self, seed_type: SeedType) -> SeedType:
        pass


class SourceTypeRepositoryInterface(ABC):
    """SourceType 仓库的抽象定义。"""

    @abstractmethod
    def get_source_type_by_id(self, source_type_id: UUID) -> SourceType | None:
        pass

    @abstractmethod
    def save_source_type(self, source_type: SourceType) -> SourceType:
        pass


class TeamRepositoryInterface(ABC):
    """Team 仓库的抽象定义。"""

    @abstractmethod
    def get_team_by_id(self, team_id: UUID) -> Team | None:
        pass

    @abstractmethod
    def save_team(self, team: Team) -> Team:
        pass


class TeamMatchRepositoryInterface(ABC):
    """TeamMatch 仓库的抽象定义。"""

    @abstractmethod
    def get_team_match_by_id(self, team_match_id: UUID) -> TeamMatch | None:
        pass

    @abstractmethod
    def save_team_match(self, team_match: TeamMatch) -> TeamMatch:
        pass


class TeamMatchTreeRepositoryInterface(ABC):
    """TeamMatchTree 仓库的抽象定义。"""

    @abstractmethod
    def get_team_match_tree_by_id(self, team_match_tree_id: UUID) -> TeamMatchTree | None:
        pass

    @abstractmethod
    def save_team_match_tree(self, team_match_tree: TeamMatchTree) -> TeamMatchTree:
        pass


class TeamMembershipRepositoryInterface(ABC):
    """TeamMembership 仓库的抽象定义。"""

    @abstractmethod
    def get_team_membership_by_id(self, membership_id: UUID) -> TeamMembership | None:
        pass

    @abstractmethod
    def save_team_membership(self, membership: TeamMembership) -> TeamMembership:
        pass


class TeamRoleRepositoryInterface(ABC):
    """TeamRole 仓库的抽象定义。"""

    @abstractmethod
    def get_team_role_by_id(self, team_role_id: UUID) -> TeamRole | None:
        pass

    @abstractmethod
    def save_team_role(self, team_role: TeamRole) -> TeamRole:
        pass


class TournamentRepositoryInterface(ABC):
    """Tournament 仓库的抽象定义。"""

    @abstractmethod
    def get_tournament_by_id(self, tournament_id: UUID) -> Tournament | None:
        pass

    @abstractmethod
    def save_tournament(self, tournament: Tournament) -> Tournament:
        pass


class TournamentStatusRepositoryInterface(ABC):
    """TournamentStatus 仓库的抽象定义。"""

    @abstractmethod
    def get_tournament_status_by_id(self, tournament_status_id: UUID) -> TournamentStatus | None:
        pass

    @abstractmethod
    def save_tournament_status(self, tournament_status: TournamentStatus) -> TournamentStatus:
        pass
