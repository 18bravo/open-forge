"""
Role-Based Access Control (RBAC)

This module defines roles and role assignments for the Open Forge platform.
Roles can be hierarchical and contain sets of permissions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from forge_core.auth.permissions import Permission


class BuiltinRole(str, Enum):
    """
    Built-in roles provided by the platform.

    These roles cannot be deleted but can have their permissions modified.
    """

    SUPER_ADMIN = "super_admin"  # Full system access
    ADMIN = "admin"  # Organization admin
    DEVELOPER = "developer"  # Can create/modify pipelines, datasets
    ANALYST = "analyst"  # Can view and analyze data
    VIEWER = "viewer"  # Read-only access
    SERVICE = "service"  # Service account for automation


@dataclass
class Role:
    """
    Represents a role in the RBAC system.

    Attributes:
        name: Unique role identifier
        display_name: Human-readable role name
        description: Description of what this role allows
        permissions: Set of permissions granted by this role
        parent_roles: Roles that this role inherits permissions from
        is_builtin: Whether this is a system-defined role
        tenant_id: Optional tenant scope for multi-tenant deployments
        created_at: When the role was created
        updated_at: When the role was last modified
    """

    name: str
    display_name: str
    description: str = ""
    permissions: set[str] = field(default_factory=set)
    parent_roles: set[str] = field(default_factory=set)
    is_builtin: bool = False
    tenant_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def get_all_permissions(
        self, role_registry: dict[str, "Role"]
    ) -> set[str]:
        """
        Get all permissions for this role, including inherited ones.

        Args:
            role_registry: Dictionary mapping role names to Role objects

        Returns:
            Set of all permission strings
        """
        all_permissions = set(self.permissions)

        for parent_name in self.parent_roles:
            if parent := role_registry.get(parent_name):
                all_permissions |= parent.get_all_permissions(role_registry)

        return all_permissions

    def has_permission(
        self, permission: str, role_registry: dict[str, "Role"]
    ) -> bool:
        """
        Check if this role grants a specific permission.

        Args:
            permission: Permission string to check
            role_registry: Dictionary mapping role names to Role objects

        Returns:
            True if the role grants the permission
        """
        return permission in self.get_all_permissions(role_registry)


@dataclass
class RoleAssignment:
    """
    Represents assignment of a role to a user or group.

    Attributes:
        role_name: Name of the assigned role
        principal_id: ID of the user or group
        principal_type: Type of principal ("user" or "group")
        resource_scope: Optional resource scope (e.g., "project:123")
        granted_by: ID of the user who granted this assignment
        granted_at: When the assignment was made
        expires_at: Optional expiration time for temporary assignments
    """

    role_name: str
    principal_id: str
    principal_type: str = "user"
    resource_scope: str | None = None
    granted_by: str | None = None
    granted_at: datetime | None = None
    expires_at: datetime | None = None

    def is_expired(self) -> bool:
        """Check if this role assignment has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def is_active(self) -> bool:
        """Check if this role assignment is currently active."""
        return not self.is_expired()
