from datetime import date

from rest_framework import serializers

from backend.apps.fencing_organizer.serializers.base import DomainModelSerializer
from .models import DjangoFencer


class FencerSerializer(DomainModelSerializer):
    """
    Fencer serializer - handles both Django ORM models and domain models (dataclasses).

    Extends DomainModelSerializer for Clean Architecture compatibility.
    """

    id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(max_length=100, required=True)
    last_name = serializers.CharField(max_length=100, required=True)
    display_name = serializers.CharField(max_length=200, required=False, allow_null=True)
    gender = serializers.CharField(max_length=10, required=False, allow_null=True)
    country_code = serializers.CharField(max_length=3, required=False, allow_null=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    fencing_id = serializers.CharField(max_length=50, required=False, allow_null=True)
    current_ranking = serializers.IntegerField(required=False, allow_null=True)
    primary_weapon = serializers.CharField(max_length=10, required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    age = serializers.SerializerMethodField(read_only=True)
    is_international = serializers.SerializerMethodField(read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DjangoFencer
        fields = [
            "id",
            "first_name",
            "last_name",
            "display_name",
            "full_name",
            "gender",
            "country_code",
            "birth_date",
            "fencing_id",
            "current_ranking",
            "primary_weapon",
            "age",
            "is_international",
            "created_at",
            "updated_at",
        ]

    def get_full_name(self, obj):
        if hasattr(obj, "full_name"):
            return obj.full_name
        last_name = getattr(obj, "last_name", "") or ""
        first_name = getattr(obj, "first_name", "") or ""
        return f"{last_name} {first_name}".strip()

    def get_age(self, obj):
        birth_date = getattr(obj, "birth_date", None)
        if not birth_date:
            return None
        today = date.today()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age

    def get_is_international(self, obj):
        fencing_id = getattr(obj, "fencing_id", None)
        return bool(fencing_id)

    def validate_first_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("First name cannot be empty")
        if len(value) > 100:
            raise serializers.ValidationError("First name cannot exceed 100 characters")
        return value.strip()

    def validate_last_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Last name cannot be empty")
        if len(value) > 100:
            raise serializers.ValidationError("Last name cannot exceed 100 characters")
        return value.strip()

    def validate_country_code(self, value):
        if value:
            value = value.upper().strip()
            if len(value) != 3:
                raise serializers.ValidationError("Country code must be 3 letters")
            if not value.isalpha():
                raise serializers.ValidationError("Country code can only contain letters")
        return value

    def validate_fencing_id(self, value):
        if value:
            value = value.strip()
            if len(value) > 50:
                raise serializers.ValidationError("Fencing ID cannot exceed 50 characters")
        return value

    def validate_birth_date(self, value):
        if value:
            if value > date.today():
                raise serializers.ValidationError("Birth date cannot be in the future")
            if value.year < 1900:
                raise serializers.ValidationError("Birth date cannot be before 1900")
        return value

    def validate_current_ranking(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Ranking cannot be negative")
        return value

    def validate(self, attrs):
        valid_genders = ["MEN", "WOMEN", "MIXED", "OPEN", None]
        if "gender" in attrs and attrs["gender"] not in valid_genders:
            raise serializers.ValidationError({"gender": f"Gender must be one of: {', '.join([g for g in valid_genders if g])}"})

        valid_weapons = ["FOIL", "EPEE", "SABRE", None]
        if "primary_weapon" in attrs and attrs["primary_weapon"] not in valid_weapons:
            raise serializers.ValidationError({"primary_weapon": f"Weapon must be one of: {', '.join([w for w in valid_weapons if w])}"})

        return attrs


class FencerCreateSerializer(DomainModelSerializer):
    """
    Fencer create serializer - for creating new fencers.
    """

    first_name = serializers.CharField(max_length=100, required=True)
    last_name = serializers.CharField(max_length=100, required=True)
    display_name = serializers.CharField(max_length=200, required=False, allow_null=True)
    gender = serializers.CharField(max_length=10, required=False, allow_null=True)
    country_code = serializers.CharField(max_length=3, required=False, allow_null=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    fencing_id = serializers.CharField(max_length=50, required=False, allow_null=True)
    current_ranking = serializers.IntegerField(required=False, allow_null=True)
    primary_weapon = serializers.CharField(max_length=10, required=False, allow_null=True)

    class Meta:
        model = DjangoFencer
        fields = [
            "first_name",
            "last_name",
            "display_name",
            "gender",
            "country_code",
            "birth_date",
            "fencing_id",
            "current_ranking",
            "primary_weapon",
        ]

    def validate_first_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("First name cannot be empty")
        return value.strip()

    def validate_last_name(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Last name cannot be empty")
        return value.strip()


class FencerUpdateSerializer(DomainModelSerializer):
    """
    Fencer update serializer - for updating existing fencers.
    """

    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    display_name = serializers.CharField(max_length=200, required=False, allow_null=True)
    gender = serializers.CharField(max_length=10, required=False, allow_null=True)
    country_code = serializers.CharField(max_length=3, required=False, allow_null=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    fencing_id = serializers.CharField(max_length=50, required=False, allow_null=True)
    current_ranking = serializers.IntegerField(required=False, allow_null=True)
    primary_weapon = serializers.CharField(max_length=10, required=False, allow_null=True)

    class Meta:
        model = DjangoFencer
        fields = [
            "first_name",
            "last_name",
            "display_name",
            "gender",
            "country_code",
            "birth_date",
            "fencing_id",
            "current_ranking",
            "primary_weapon",
        ]


class FencerSearchSerializer(serializers.Serializer):
    """
    Fencer search serializer - for searching fencers.
    """

    query = serializers.CharField(required=True, min_length=1, max_length=100, help_text="Search query (name, fencing ID, country code)")
    limit = serializers.IntegerField(required=False, default=50, min_value=1, max_value=1000, help_text="Maximum number of results")
