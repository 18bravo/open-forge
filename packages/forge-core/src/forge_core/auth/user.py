"""
User model for authenticated users.

This module defines the User class that represents an authenticated user
throughout the Open Forge platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class User:
    """
    Represents an authenticated user in the system.

    Attributes:
        id: Unique identifier for the user (from identity provider)
        email: User's email address
        name: User's display name
        roles: Set of role names assigned to the user
        permissions: Set of permission strings the user has been granted
        attributes: Additional user attributes from the identity provider
        tenant_id: Optional tenant identifier for multi-tenant deployments
        created_at: When the user record was created
        last_login: Timestamp of the user's last login
    """

    id: str
    email: str
    name: str
    roles: frozenset[str] = field(default_factory=frozenset)
    permissions: frozenset[str] = field(default_factory=frozenset)
    attributes: dict[str, Any] = field(default_factory=dict)
    tenant_id: str | None = None
    created_at: datetime | None = None
    last_login: datetime | None = None

    def has_role(self, role: str) -> bool:
        """Check if the user has a specific role."""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """Check if the user has a specific permission."""
        return permission in self.permissions

    def has_any_role(self, *roles: str) -> bool:
        """Check if the user has any of the specified roles."""
        return bool(self.roles & set(roles))

    def has_all_roles(self, *roles: str) -> bool:
        """Check if the user has all of the specified roles."""
        return set(roles) <= self.roles

    def is_admin(self) -> bool:
        """Check if the user has admin privileges."""
        return "admin" in self.roles or "super_admin" in self.roles
