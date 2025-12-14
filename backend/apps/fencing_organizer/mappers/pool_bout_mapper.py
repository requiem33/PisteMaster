from backend.apps.fencing_organizer.modules.pool_bout.models import DjangoPoolBout
from core.models.pool_bout import PoolBout


class PoolBoutMapper:
    """小组赛单场映射器"""

    @staticmethod
    def to_domain(django_bout: DjangoPoolBout) -> PoolBout:
        """Django ORM → Core Domain"""
        return PoolBout(
            id=django_bout.id,
            pool_id=django_bout.pool.id,
            fencer_a_id=django_bout.fencer_a.id,
            fencer_b_id=django_bout.fencer_b.id,
            status_id=django_bout.status.id,
            winner_id=django_bout.winner.id if django_bout.winner else None,
            fencer_a_score=django_bout.fencer_a_score,
            fencer_b_score=django_bout.fencer_b_score,
            scheduled_time=django_bout.scheduled_time,
            actual_start_time=django_bout.actual_start_time,
            actual_end_time=django_bout.actual_end_time,
            duration_seconds=django_bout.duration_seconds,
            notes=django_bout.notes
        )

    @staticmethod
    def to_orm_data(bout: PoolBout) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": bout.id,
            "pool_id": bout.pool_id,
            "fencer_a_id": bout.fencer_a_id,
            "fencer_b_id": bout.fencer_b_id,
            "status_id": bout.status_id,
            "winner_id": bout.winner_id,
            "fencer_a_score": bout.fencer_a_score,
            "fencer_b_score": bout.fencer_b_score,
            "scheduled_time": bout.scheduled_time,
            "actual_start_time": bout.actual_start_time,
            "actual_end_time": bout.actual_end_time,
            "duration_seconds": bout.duration_seconds,
            "notes": bout.notes
        }
