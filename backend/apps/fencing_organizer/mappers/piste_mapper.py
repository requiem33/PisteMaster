from backend.apps.fencing_organizer.modules.piste.models import DjangoPiste
from core.models.piste import Piste


class PisteMapper:
    """剑道映射器"""

    @staticmethod
    def to_domain(django_piste: DjangoPiste) -> Piste:
        """Django ORM → Core Domain"""
        return Piste(
            id=django_piste.id,
            tournament_id=django_piste.tournament.id,
            piste_number=django_piste.piste_number,
            location=django_piste.location,
            piste_type=django_piste.piste_type,
            is_available=django_piste.is_available,
            notes=django_piste.notes
        )

    @staticmethod
    def to_orm_data(piste: Piste) -> dict:
        """Core Domain → ORM数据字典"""
        return {
            "id": piste.id,
            "tournament_id": piste.tournament_id,
            "piste_number": piste.piste_number,
            "location": piste.location,
            "piste_type": piste.piste_type,
            "is_available": piste.is_available,
            "notes": piste.notes
        }
