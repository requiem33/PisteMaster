from core.models.mapper_base import versioned_fields_to_dict, versioned_fields_from_dict
from backend.apps.fencing_organizer.modules.fencer.models import DjangoFencer
from core.models.fencer import Fencer


class FencerMapper:
    """Fencer对象映射器"""

    @staticmethod
    def to_domain(django_fencer: DjangoFencer) -> Fencer:
        """Django ORM → Core Domain"""
        version_fields = versioned_fields_to_dict(django_fencer)
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
            **version_fields
        )

    @staticmethod
    def to_orm_data(fencer: Fencer) -> dict:
        """Core Domain → ORM数据字典"""
        data = {
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
            "updated_at": fencer.updated_at,
        }
        versioned_fields_from_dict(fencer.__dict__, data)
        return data
