"""
Permission Definitions

This module defines fine-grained permissions for the Open Forge platform.
Permissions follow the format: resource_type:action or resource_type:resource_id:action
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar


class ResourceType(str, Enum):
    """Types of resources that can have permissions."""

    # Data resources
    DATASET = "dataset"
    PIPELINE = "pipeline"
    CONNECTOR = "connector"
    TRANSFORM = "transform"

    # AI resources
    AGENT = "agent"
    MODEL = "model"
    FUNCTION = "function"

    # Application resources
    APP = "app"
    DASHBOARD = "dashboard"
    REPORT = "report"

    # Platform resources
    PROJECT = "project"
    WORKSPACE = "workspace"
    ORGANIZATION = "organization"

    # System resources
    USER = "user"
    ROLE = "role"
    AUDIT = "audit"
    SETTINGS = "settings"


class Action(str, Enum):
    """Actions that can be performed on resources."""

    # CRUD actions
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"

    # Execution actions
    EXECUTE = "execute"
    SCHEDULE = "schedule"
    CANCEL = "cancel"

    # Admin actions
    SHARE = "share"
    MANAGE = "manage"
    ADMIN = "admin"

    # Special actions
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"


@dataclass(frozen=True)
class Permission:
    """
    Represents a permission to perform an action on a resource type.

    Permissions are immutable and can be used as dictionary keys or in sets.

    Examples:
        >>> Permission(ResourceType.DATASET, Action.READ)
        Permission(dataset:read)
        >>> Permission.from_string("pipeline:execute")
        Permission(pipeline:execute)
    """

    resource_type: ResourceType
    action: Action
    resource_id: str | None = None

    # Common permission patterns
    WILDCARD: ClassVar[str] = "*"

    def __str__(self) -> str:
        """Return permission as a string."""
        if self.resource_id:
            return f"{self.resource_type.value}:{self.resource_id}:{self.action.value}"
        return f"{self.resource_type.value}:{self.action.value}"

    def __repr__(self) -> str:
        """Return permission representation."""
        return f"Permission({self})"

    @classmethod
    def from_string(cls, permission_str: str) -> "Permission":
        """
        Parse a permission from a string.

        Args:
            permission_str: Permission string (e.g., "dataset:read" or "dataset:123:write")

        Returns:
            Permission object

        Raises:
            ValueError: If the permission string is invalid
        """
        parts = permission_str.split(":")

        if len(parts) == 2:
            resource_type = ResourceType(parts[0])
            action = Action(parts[1])
            return cls(resource_type=resource_type, action=action)
        elif len(parts) == 3:
            resource_type = ResourceType(parts[0])
            resource_id = parts[1]
            action = Action(parts[2])
            return cls(
                resource_type=resource_type,
                action=action,
                resource_id=resource_id,
            )
        else:
            raise ValueError(f"Invalid permission string: {permission_str}")

    def matches(self, other: "Permission") -> bool:
        """
        Check if this permission matches another permission.

        Supports wildcard matching for resource_id.
        """
        if self.resource_type != other.resource_type:
            return False
        if self.action != other.action:
            return False

        # Wildcard resource_id matches everything
        if self.resource_id == self.WILDCARD or other.resource_id == self.WILDCARD:
            return True

        return self.resource_id == other.resource_id


@dataclass
class PermissionSet:
    """
    A collection of permissions with efficient lookup.

    Supports wildcard permissions that grant access to all resources of a type.
    """

    permissions: set[str] = field(default_factory=set)

    def add(self, permission: Permission | str) -> None:
        """Add a permission to the set."""
        if isinstance(permission, Permission):
            self.permissions.add(str(permission))
        else:
            self.permissions.add(permission)

    def remove(self, permission: Permission | str) -> None:
        """Remove a permission from the set."""
        if isinstance(permission, Permission):
            self.permissions.discard(str(permission))
        else:
            self.permissions.discard(permission)

    def has(self, permission: Permission | str) -> bool:
        """
        Check if the set contains a permission.

        Checks for exact match and wildcard matches.
        """
        perm_str = str(permission) if isinstance(permission, Permission) else permission

        # Exact match
        if perm_str in self.permissions:
            return True

        # Check for wildcard permissions
        parts = perm_str.split(":")
        if len(parts) >= 2:
            # Check for resource:* (all actions on resource type)
            wildcard_action = f"{parts[0]}:*"
            if wildcard_action in self.permissions:
                return True

            # Check for *:action (action on all resource types)
            wildcard_resource = f"*:{parts[-1]}"
            if wildcard_resource in self.permissions:
                return True

            # Check for * (full admin)
            if "*" in self.permissions:
                return True

        return False

    def __contains__(self, permission: Permission | str) -> bool:
        """Support 'in' operator for permission checking."""
        return self.has(permission)

    def __iter__(self):
        """Iterate over permissions."""
        return iter(self.permissions)

    def __len__(self) -> int:
        """Return number of permissions."""
        return len(self.permissions)
