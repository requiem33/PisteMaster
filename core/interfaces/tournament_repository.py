from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import date
from core.models.tournament import Tournament


class TournamentRepositoryInterface(ABC):
    """赛事仓库接口"""

    @abstractmethod
    def get_tournament_by_id(self, tournament_id: UUID) -> Optional[Tournament]:
        pass

    @abstractmethod
    def get_tournaments_by_date_range(self, start_date: date, end_date: date) -> List[Tournament]:
        pass

    @abstractmethod
    def get_tournaments_by_status(self, status_id: UUID) -> List[Tournament]:
        pass

    @abstractmethod
    def get_all_tournaments(self) -> List[Tournament]:
        pass

    @abstractmethod
    def save_tournament(self, tournament: Tournament) -> Tournament:
        pass

    @abstractmethod
    def delete_tournament(self, tournament_id: UUID) -> bool:
        pass
