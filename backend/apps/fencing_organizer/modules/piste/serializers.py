from backend.apps.fencing_organizer.serializers.base import VersionedModelSerializer
from backend.apps.fencing_organizer.modules.piste.models import DjangoPiste


class PisteSerializer(VersionedModelSerializer):
    class Meta:
        model = DjangoPiste
        fields = "__all__"
