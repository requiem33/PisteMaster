from dataclasses import asdict, is_dataclass
from typing import Any

from rest_framework import serializers


class DomainModelSerializer(serializers.Serializer):
    """
    Base serializer that handles both Django ORM models and dataclass domain models.

    For ORM models: Uses standard ModelSerializer behavior via to_representation.
    For Domain models (dataclasses): Converts to dict for serialization.

    This enables Clean Architecture where:
    - Service layer returns domain models (dataclasses)
    - API layer serializes them without knowing about ORM
    """

    def to_representation(self, instance: Any) -> dict:
        if is_dataclass(instance) and not isinstance(instance, type):
            if hasattr(super(), "to_representation"):
                return super().to_representation(instance)
            return asdict(instance)
        elif hasattr(instance, "_meta"):
            if hasattr(super(), "to_representation"):
                return super().to_representation(instance)
            return self._represent_orm(instance)
        else:
            return super().to_representation(instance)

    def _represent_orm(self, instance: Any) -> dict:
        result = {}
        for field_name in self.fields:
            field = self.fields[field_name]
            if field.read_only:
                value = getattr(instance, field_name, None)
            else:
                value = getattr(instance, field_name, None)
            result[field_name] = value
        return result

    def to_internal_value(self, data: dict) -> dict:
        return super().to_internal_value(data)
