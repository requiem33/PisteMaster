from backend.apps.fencing_organizer.modules.pool_assignment.models import DjangoPoolAssignment
from core.models.pool_assignment import PoolAssignment


class PoolAssignmentMapper:
    """PoolAssignment映射器"""

    @staticmethod
    def to_domain(django_assignment: DjangoPoolAssignment) -> PoolAssignment:
        """Django ORM → Core Domain"""
        return PoolAssignment(
            id=django_assignment.id,
            pool_id=django_assignment.pool.id,
            fencer_id=django_assignment.fencer.id,
            final_pool_rank=django_assignment.final_pool_rank,
            victories=django_assignment.victories,
            indicator=django_assignment.indicator,
            touches_scored=django_assignment.touches_scored,
            touches_received=django_assignment.touches_received,
            matches_played=django_assignment.matches_played,
            is_qualified=django_assignment.is_qualified,
            qualification_rank=django_assignment.qualification_rank
        )

    @staticmethod
    def to_orm_data(assignment: PoolAssignment) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": assignment.id,
            "pool_id": assignment.pool_id,
            "fencer_id": assignment.fencer_id,
            "final_pool_rank": assignment.final_pool_rank,
            "victories": assignment.victories,
            "indicator": assignment.indicator,
            "touches_scored": assignment.touches_scored,
            "touches_received": assignment.touches_received,
            "matches_played": assignment.matches_played,
            "is_qualified": assignment.is_qualified,
            "qualification_rank": assignment.qualification_rank
        }
