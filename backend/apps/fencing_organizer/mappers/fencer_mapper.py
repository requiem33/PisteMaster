from datetime import datetime
from typing import Optional

from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from core.models.fencer import Fencer


class FencerMapper:
    """Fencer对象映射器"""

    @staticmethod
    def to_domain(django_fencer: DjangoFencer) -> Fencer:
        """Django ORM → Core Domain"""
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
            updated_at=django_fencer.updated_at
        )

    @staticmethod
    def to_orm_data(fencer: Fencer) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": fencer.id,
            "first_name": fencer.first_name,
            "last_name": fencer.last_name,
            "display_name": fencer.display_name,
            "gender": fencer.gender,
            "country_code": fencer.country_code,
            "birth_date": fencer.birth_date,
            "fencing_id": fencer.fencing_id,
            "current_ranking": fencer.current_ranking,
            "primary_weapon": fencer.primary_weapon,
            "created_at": fencer.created_at,
            "updated_at": fencer.updated_at
        }
