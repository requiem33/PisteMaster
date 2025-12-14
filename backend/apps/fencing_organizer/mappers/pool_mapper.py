from backend.apps.fencing_organizer.modules.pool.models import DjangoPool
from core.models.pool import Pool


class PoolMapper:
    """小组映射器"""

    @staticmethod
    def to_domain(django_pool: DjangoPool) -> Pool:
        """Django ORM → Core Domain"""
        return Pool(
            id=django_pool.id,
            event_id=django_pool.event.id,
            pool_number=django_pool.pool_number,
            pool_letter=django_pool.pool_letter,
            piste_id=django_pool.piste.id if django_pool.piste else None,
            start_time=django_pool.start_time,
            status=django_pool.status,
            is_completed=django_pool.is_completed
        )

    @staticmethod
    def to_orm_data(pool: Pool) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": pool.id,
            "event_id": pool.event_id,
            "pool_number": pool.pool_number,
            "pool_letter": pool.pool_letter,
            "piste_id": pool.piste_id,
            "start_time": pool.start_time,
            "status": pool.status,
            "is_completed": pool.is_completed
        }
