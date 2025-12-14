from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from core.models.fencer import Fencer


class FencerRepositoryInterface(ABC):
    """Fencer仓库接口"""

    @abstractmethod
    def get_fencer_by_id(self, fencer_id: UUID) -> Optional[Fencer]:
        """根据ID获取运动员"""
        pass

    @abstractmethod
    def get_fencer_by_fencing_id(self, fencing_id: str) -> Optional[Fencer]:
        """根据击剑ID获取运动员"""
        pass

    @abstractmethod
    def get_fencers_by_country(self, country_code: str) -> List[Fencer]:
        """根据国家获取运动员列表"""
        pass

    @abstractmethod
    def get_fencers_by_name(self, first_name: Optional[str] = None,
                            last_name: Optional[str] = None) -> List[Fencer]:
        """根据姓名获取运动员列表"""
        pass

    @abstractmethod
    def get_all_fencers(self, skip: int = 0, limit: int = 100) -> List[Fencer]:
        """获取所有运动员"""
        pass

    @abstractmethod
    def save_fencer(self, fencer: Fencer) -> Fencer:
        """保存或更新运动员"""
        pass

    @abstractmethod
    def delete_fencer(self, fencer_id: UUID) -> bool:
        """删除运动员"""
        pass

    @abstractmethod
    def search_fencers(self, query: str, limit: int = 50) -> List[Fencer]:
        """搜索运动员"""
        pass

    @abstractmethod
    def get_fencers_by_weapon(self, weapon: str) -> List[Fencer]:
        """根据主剑种获取运动员"""
        pass
