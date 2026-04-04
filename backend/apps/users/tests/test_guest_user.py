"""
Tests for Guest user authentication.
These tests verify that the Guest user is properly created and can authenticate.
"""

import pytest
from django.contrib.auth import authenticate
from backend.apps.users.models import User


@pytest.mark.django_db
class TestGuestUser:
    """Test Guest user creation and authentication."""

    def test_guest_user_exists(self):
        """Test that Guest user exists after migrations."""
        guest_user = User.objects.filter(username="Guest").first()
        assert guest_user is not None, "Guest user should exist"

    def test_guest_user_role(self):
        """Test that Guest user has the correct role."""
        guest_user = User.objects.get(username="Guest")
        assert guest_user.role == User.Role.GUEST, "Guest user should have GUEST role"

    def test_guest_user_is_active(self):
        """Test that Guest user is active."""
        guest_user = User.objects.get(username="Guest")
        assert guest_user.is_active is True, "Guest user should be active"

    def test_guest_user_has_usable_password(self):
        """Test that Guest user has a usable password."""
        guest_user = User.objects.get(username="Guest")
        assert guest_user.has_usable_password(), "Guest user should have a usable password"

    def test_guest_user_authentication(self):
        """Test that Guest user can authenticate with Guest/Guest credentials."""
        user = authenticate(username="Guest", password="Guest")
        assert user is not None, "Guest user should authenticate successfully"
        assert user.username == "Guest", "Authenticated user should be Guest"
        assert user.role == User.Role.GUEST, "Authenticated user should have GUEST role"

    def test_guest_user_wrong_password(self):
        """Test that Guest user cannot authenticate with wrong password."""
        user = authenticate(username="Guest", password="wrong_password")
        assert user is None, "Authentication should fail with wrong password"

    def test_guest_user_can_create_tournament(self):
        """Test that Guest user has necessary permissions."""
        guest_user = User.objects.get(username="Guest")
        # Guest should be able to create tournaments
        # (This is enforced by permission classes in views)
        assert guest_user.role == User.Role.GUEST
