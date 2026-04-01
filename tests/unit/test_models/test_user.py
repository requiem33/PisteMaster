"""
Unit tests for User domain model.
"""

from datetime import datetime
from uuid import UUID


from core.models.user import User


class TestUser:
    """Test suite for User domain model."""

    def test_user_creation_with_required_fields(self):
        """Test creating user with only required fields."""
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        user = User(id=user_id, username="testuser")

        assert user.id == user_id
        assert user.username == "testuser"
        assert user.email is None
        assert user.role == "SCHEDULER"
        assert user.first_name == ""
        assert user.last_name == ""
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_creation_with_all_fields(self):
        """Test creating user with all fields."""
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        user = User(
            id=user_id,
            username="admin_user",
            email="admin@example.com",
            role="ADMIN",
            first_name="Admin",
            last_name="User",
            is_active=True,
        )

        assert user.id == user_id
        assert user.username == "admin_user"
        assert user.email == "admin@example.com"
        assert user.role == "ADMIN"
        assert user.first_name == "Admin"
        assert user.last_name == "User"
        assert user.is_active is True

    def test_user_is_admin_property(self):
        """Test is_admin property."""
        admin_user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            username="admin",
            role="ADMIN",
        )
        scheduler_user = User(
            id=UUID("23456789-2345-6789-2345-678923456789"),
            username="scheduler",
            role="SCHEDULER",
        )

        assert admin_user.is_admin is True
        assert scheduler_user.is_admin is False

    def test_user_is_scheduler_property(self):
        """Test is_scheduler property."""
        scheduler_user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            username="scheduler",
            role="SCHEDULER",
        )
        admin_user = User(
            id=UUID("23456789-2345-6789-2345-678923456789"),
            username="admin",
            role="ADMIN",
        )

        assert scheduler_user.is_scheduler is True
        assert admin_user.is_scheduler is False

    def test_user_create_class_method(self):
        """Test User.create class method."""
        user = User.create(
            username="newuser",
            email="newuser@example.com",
            role="ADMIN",
        )

        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.role == "ADMIN"
        assert isinstance(user.id, UUID)
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_create_default_role(self):
        """Test that create method defaults to SCHEDULER role."""
        user = User.create(username="testuser")

        assert user.role == "SCHEDULER"

    def test_user_default_values(self):
        """Test default values for user fields."""
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        user = User(id=user_id, username="testuser")

        assert user.role == "SCHEDULER"
        assert user.first_name == ""
        assert user.last_name == ""
        assert user.is_active is True

    def test_user_timestamps_auto_generated(self):
        """Test that timestamps are auto-generated."""
        before = datetime.utcnow()
        user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            username="testuser",
        )
        after = datetime.utcnow()

        assert before <= user.created_at <= after
        assert before <= user.updated_at <= after

    def test_user_active_flag(self):
        """Test is_active flag."""
        active_user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            username="active",
            is_active=True,
        )
        inactive_user = User(
            id=UUID("23456789-2345-6789-2345-678923456789"),
            username="inactive",
            is_active=False,
        )

        assert active_user.is_active is True
        assert inactive_user.is_active is False

    def test_user_optional_email(self):
        """Test that email is optional."""
        user_without_email = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            username="noemail",
        )
        user_with_email = User(
            id=UUID("23456789-2345-6789-2345-678923456789"),
            username="withemail",
            email="user@example.com",
        )

        assert user_without_email.email is None
        assert user_with_email.email == "user@example.com"
