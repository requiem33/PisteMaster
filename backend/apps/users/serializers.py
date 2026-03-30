from rest_framework import serializers
from backend.apps.fencing_organizer.serializers.base import DomainModelSerializer
from .models import User


class UserSerializer(DomainModelSerializer):
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_null=True)
    role = serializers.CharField(read_only=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "first_name", "last_name"]


class UserCreateSerializer(DomainModelSerializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_null=True)
    role = serializers.ChoiceField(choices=["ADMIN", "SCHEDULER"], default="SCHEDULER")
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["username", "password", "email", "role", "first_name", "last_name"]

    def validate_username(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Username cannot be empty")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value.strip()

    def validate_password(self, value):
        if not value or len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters")
        return value


class UserUpdateSerializer(DomainModelSerializer):
    email = serializers.EmailField(required=False, allow_null=True)
    role = serializers.ChoiceField(choices=["ADMIN", "SCHEDULER"], required=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "role", "first_name", "last_name"]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
