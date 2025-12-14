from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
from core.models.pool import Pool


class PoolRepositoryInterface(ABC):
    """小组仓库接口"""

    @abstractmethod
    def get_pool_by_id(self, pool_id: UUID) -> Optional[Pool]:
        pass

    @abstractmethod
    def get_pools_by_event(self, event_id: UUID) -> List[Pool]:
        pass

    @abstractmethod
    def get_pools_by_event_and_status(self, event_id: UUID, status: str) -> List[Pool]:
        pass

    @abstractmethod
    def get_pools_by_piste(self, piste_id: UUID) -> List[Pool]:
        pass

    @abstractmethod
    def get_pools_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Pool]:
        pass

    @abstractmethod
    def get_all_pools(self) -> List[Pool]:
        pass

    @abstractmethod
    def save_pool(self, pool: Pool) -> Pool:
        pass

    @abstractmethod
    def delete_pool(self, pool_id: UUID) -> bool:
        pass

    @abstractmethod
    def get_next_pool_number(self, event_id: UUID) -> int:
        pass
