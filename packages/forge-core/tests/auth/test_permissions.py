"""Tests for the permissions module."""

import pytest

from forge_core.auth.permissions import (
    Action,
    Permission,
    PermissionSet,
    ResourceType,
)


class TestPermission:
    """Tests for the Permission class."""

    def test_permission_creation(self) -> None:
        """Test creating a permission."""
        perm = Permission(ResourceType.DATASET, Action.READ)
        assert perm.resource_type == ResourceType.DATASET
        assert perm.action == Action.READ
        assert perm.resource_id is None

    def test_permission_with_resource_id(self) -> None:
        """Test creating a permission with a resource ID."""
        perm = Permission(ResourceType.DATASET, Action.READ, resource_id="123")
        assert perm.resource_id == "123"
        assert str(perm) == "dataset:123:read"

    def test_permission_str(self) -> None:
        """Test permission string representation."""
        perm = Permission(ResourceType.PIPELINE, Action.EXECUTE)
        assert str(perm) == "pipeline:execute"

    def test_permission_from_string(self) -> None:
        """Test parsing a permission from string."""
        perm = Permission.from_string("dataset:read")
        assert perm.resource_type == ResourceType.DATASET
        assert perm.action == Action.READ
        assert perm.resource_id is None

    def test_permission_from_string_with_id(self) -> None:
        """Test parsing a permission with resource ID from string."""
        perm = Permission.from_string("dataset:123:write")
        assert perm.resource_type == ResourceType.DATASET
        assert perm.action == Action.WRITE
        assert perm.resource_id == "123"

    def test_permission_from_invalid_string(self) -> None:
        """Test parsing an invalid permission string."""
        with pytest.raises(ValueError):
            Permission.from_string("invalid")
        with pytest.raises(ValueError):
            Permission.from_string("a:b:c:d")

    def test_permission_matches_exact(self) -> None:
        """Test exact permission matching."""
        perm1 = Permission(ResourceType.DATASET, Action.READ)
        perm2 = Permission(ResourceType.DATASET, Action.READ)
        perm3 = Permission(ResourceType.DATASET, Action.WRITE)

        assert perm1.matches(perm2)
        assert not perm1.matches(perm3)

    def test_permission_matches_wildcard(self) -> None:
        """Test wildcard permission matching."""
        perm = Permission(ResourceType.DATASET, Action.READ, resource_id="*")
        specific = Permission(ResourceType.DATASET, Action.READ, resource_id="123")

        assert perm.matches(specific)
        assert specific.matches(perm)


class TestPermissionSet:
    """Tests for the PermissionSet class."""

    def test_permission_set_add(self) -> None:
        """Test adding permissions to a set."""
        perm_set = PermissionSet()
        perm = Permission(ResourceType.DATASET, Action.READ)

        perm_set.add(perm)
        assert perm in perm_set

        perm_set.add("pipeline:execute")
        assert "pipeline:execute" in perm_set

    def test_permission_set_remove(self) -> None:
        """Test removing permissions from a set."""
        perm_set = PermissionSet(permissions={"dataset:read", "dataset:write"})

        perm_set.remove("dataset:read")
        assert "dataset:read" not in perm_set
        assert "dataset:write" in perm_set

    def test_permission_set_wildcard(self) -> None:
        """Test wildcard permission checking."""
        perm_set = PermissionSet(permissions={"dataset:*"})

        assert perm_set.has("dataset:read")
        assert perm_set.has("dataset:write")
        assert not perm_set.has("pipeline:execute")

    def test_permission_set_full_admin(self) -> None:
        """Test full admin wildcard permission."""
        perm_set = PermissionSet(permissions={"*"})

        assert perm_set.has("dataset:read")
        assert perm_set.has("pipeline:execute")
        assert perm_set.has("anything:action")

    def test_permission_set_len(self) -> None:
        """Test permission set length."""
        perm_set = PermissionSet(permissions={"a:b", "c:d", "e:f"})
        assert len(perm_set) == 3

    def test_permission_set_iteration(self) -> None:
        """Test iterating over permission set."""
        perms = {"dataset:read", "pipeline:execute"}
        perm_set = PermissionSet(permissions=perms)

        assert set(perm_set) == perms
