from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
from core.models.pool_bout import PoolBout


class PoolBoutRepositoryInterface(ABC):
    """小组赛单场比赛仓库接口"""

    @abstractmethod
    def get_bout_by_id(self, bout_id: UUID) -> Optional[PoolBout]:
        pass

    @abstractmethod
    def get_bouts_by_pool(self, pool_id: UUID) -> List[PoolBout]:
        pass

    @abstractmethod
    def get_bouts_by_fencer(self, fencer_id: UUID) -> List[PoolBout]:
        pass

    @abstractmethod
    def get_bouts_by_status(self, status_id: UUID) -> List[PoolBout]:
        pass

    @abstractmethod
    def get_bouts_by_date_range(self, start_date: datetime, end_date: datetime) -> List[PoolBout]:
        pass

    @abstractmethod
    def get_all_bouts(self) -> List[PoolBout]:
        pass

    @abstractmethod
    def save_bout(self, bout: PoolBout) -> PoolBout:
        pass

    @abstractmethod
    def delete_bout(self, bout_id: UUID) -> bool:
        pass

    @abstractmethod
    def get_bout_by_fencers(self, pool_id: UUID, fencer_a_id: UUID, fencer_b_id: UUID) -> Optional[PoolBout]:
        pass
