from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from core.models.pool_assignment import PoolAssignment


class PoolAssignmentRepositoryInterface(ABC):
    """PoolAssignment仓库接口"""

    @abstractmethod
    def get_assignment_by_id(self, assignment_id: UUID) -> Optional[PoolAssignment]:
        """根据ID获取分配记录"""
        pass

    @abstractmethod
    def get_assignments_by_pool(self, pool_id: UUID) -> List[PoolAssignment]:
        """获取指定小组的所有分配记录"""
        pass

    @abstractmethod
    def get_assignments_by_fencer(self, fencer_id: UUID) -> List[PoolAssignment]:
        """获取指定运动员的所有小组分配记录"""
        pass

    @abstractmethod
    def get_assignment(self, pool_id: UUID, fencer_id: UUID) -> Optional[PoolAssignment]:
        """获取指定小组和运动员的分配记录"""
        pass

    @abstractmethod
    def save_assignment(self, assignment: PoolAssignment) -> PoolAssignment:
        """保存或更新分配记录"""
        pass

    @abstractmethod
    def delete_assignment(self, pool_id: UUID, fencer_id: UUID) -> bool:
        """删除分配记录"""
        pass

    @abstractmethod
    def create_assignment(self, pool_id: UUID, fencer_id: UUID) -> PoolAssignment:
        """创建分配记录"""
        pass

    @abstractmethod
    def update_ranking(self, pool_id: UUID, ranking_updates: List[Dict[str, Any]]) -> List[PoolAssignment]:
        """更新排名"""
        pass

    @abstractmethod
    def calculate_pool_ranking(self, pool_id: UUID) -> List[PoolAssignment]:
        """计算小组排名"""
        pass

    @abstractmethod
    def get_pool_stats(self, pool_id: UUID) -> Dict[str, Any]:
        """获取小组统计"""
        pass

    @abstractmethod
    def update_match_result(self, pool_id: UUID, fencer_id: UUID,
                            touches_scored: int, touches_received: int, is_winner: bool) -> Optional[PoolAssignment]:
        """更新比赛结果"""
        pass

    @abstractmethod
    def get_qualified_fencers(self, event_id: UUID) -> List[PoolAssignment]:
        """获取晋级的运动员"""
        pass

    @abstractmethod
    def calculate_qualification_ranking(self, event_id: UUID, qualification_count: int) -> List[PoolAssignment]:
        """计算晋级排名"""
        pass

    @abstractmethod
    def reset_pool_assignments(self, pool_id: UUID) -> bool:
        """重置小组分配（清除所有排名和统计）"""
        pass

    @abstractmethod
    def get_pool_assignments_with_fencers(self, pool_id: UUID) -> List[Dict[str, Any]]:
        """获取小组分配记录（包含运动员信息）"""
        pass
