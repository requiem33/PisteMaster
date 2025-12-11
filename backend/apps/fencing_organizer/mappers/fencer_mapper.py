from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from core.models.fencer import Fencer


class FencerMapper:
    """Fencer Dataclass 和 DjangoFencer ORM 的双向转换"""

    @staticmethod
    def to_domain(django_fencer: DjangoFencer) -> Fencer:
        """从 Django ORM 转换为核心 Dataclass"""
        # 注意：created_at 和 updated_at 字段应直接使用 ORM 的值
        return Fencer(
            id=django_fencer.id,
            first_name=django_fencer.first_name,
            last_name=django_fencer.last_name,
            display_name=django_fencer.display_name,
            gender=django_fencer.gender,
            country_code=django_fencer.country_code,
            birth_date=django_fencer.birth_date,
            fencing_id=django_fencer.fencing_id,
            current_ranking=django_fencer.current_ranking,
            primary_weapon=django_fencer.primary_weapon,
            created_at=django_fencer.created_at,
            updated_at=django_fencer.updated_at,
        )

    @staticmethod
    def to_orm_data(fencer_domain: Fencer) -> dict:
        """从核心 Dataclass 转换为用于 ORM 操作的字典"""
        # 注意：这里排除 created_at 和 updated_at，让 Django ORM 自动管理
        return {
            "id": fencer_domain.id,
            "first_name": fencer_domain.first_name,
            "last_name": fencer_domain.last_name,
            "display_name": fencer_domain.display_name,
            "gender": fencer_domain.gender,
            "country_code": fencer_domain.country_code,
            "birth_date": fencer_domain.birth_date,
            "fencing_id": fencer_domain.fencing_id,
            "current_ranking": fencer_domain.current_ranking,
            "primary_weapon": fencer_domain.primary_weapon,
        }
