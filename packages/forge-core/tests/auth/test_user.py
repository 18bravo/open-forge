"""Tests for the User model."""

import pytest

from forge_core.auth.user import User


class TestUser:
    """Tests for the User class."""

    def test_user_creation(self) -> None:
        """Test creating a user with basic attributes."""
        user = User(
            id="user-123",
            email="user@example.com",
            name="Test User",
        )
        assert user.id == "user-123"
        assert user.email == "user@example.com"
        assert user.name == "Test User"
        assert user.roles == frozenset()
        assert user.permissions == frozenset()

    def test_user_with_roles(self) -> None:
        """Test creating a user with roles."""
        user = User(
            id="user-123",
            email="user@example.com",
            name="Test User",
            roles=frozenset({"admin", "developer"}),
        )
        assert user.has_role("admin")
        assert user.has_role("developer")
        assert not user.has_role("viewer")

    def test_user_has_any_role(self) -> None:
        """Test has_any_role method."""
        user = User(
            id="user-123",
            email="user@example.com",
            name="Test User",
            roles=frozenset({"developer"}),
        )
        assert user.has_any_role("admin", "developer")
        assert not user.has_any_role("admin", "viewer")

    def test_user_has_all_roles(self) -> None:
        """Test has_all_roles method."""
        user = User(
            id="user-123",
            email="user@example.com",
            name="Test User",
            roles=frozenset({"admin", "developer", "viewer"}),
        )
        assert user.has_all_roles("admin", "developer")
        assert not user.has_all_roles("admin", "super_admin")

    def test_user_has_permission(self) -> None:
        """Test has_permission method."""
        user = User(
            id="user-123",
            email="user@example.com",
            name="Test User",
            permissions=frozenset({"dataset:read", "dataset:write"}),
        )
        assert user.has_permission("dataset:read")
        assert user.has_permission("dataset:write")
        assert not user.has_permission("dataset:delete")

    def test_user_is_admin(self) -> None:
        """Test is_admin method."""
        admin = User(
            id="admin-123",
            email="admin@example.com",
            name="Admin",
            roles=frozenset({"admin"}),
        )
        super_admin = User(
            id="super-123",
            email="super@example.com",
            name="Super Admin",
            roles=frozenset({"super_admin"}),
        )
        regular = User(
            id="user-123",
            email="user@example.com",
            name="User",
            roles=frozenset({"developer"}),
        )

        assert admin.is_admin()
        assert super_admin.is_admin()
        assert not regular.is_admin()

    def test_user_immutability(self) -> None:
        """Test that User instances are immutable."""
        user = User(
            id="user-123",
            email="user@example.com",
            name="Test User",
        )
        with pytest.raises(AttributeError):
            user.email = "new@example.com"  # type: ignore
