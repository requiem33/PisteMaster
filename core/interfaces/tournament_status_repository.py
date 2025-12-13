from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from core.models.tournament_status import TournamentStatus


class TournamentStatusRepositoryInterface(ABC):
    """赛事状态仓库接口"""

    @abstractmethod
    def get_status_by_id(self, status_id: UUID) -> Optional[TournamentStatus]:
        pass

    @abstractmethod
    def get_status_by_code(self, status_code: str) -> Optional[TournamentStatus]:
        pass

    @abstractmethod
    def get_all_statuses(self) -> List[TournamentStatus]:
        pass

    @abstractmethod
    def save_status(self, status: TournamentStatus) -> TournamentStatus:
        pass
