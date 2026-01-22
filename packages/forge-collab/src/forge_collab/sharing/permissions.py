"""Permission service with BATCHED permission checks.

This module addresses the N+1 query issue identified in the architectural review (P2 fix).
Instead of checking permissions one-at-a-time, the PermissionService provides a check_batch()
method that performs multiple permission checks in a single database round-trip.

Example usage:
    service = PermissionService(auth_provider)

    # GOOD: Batched check - single round trip
    results = await service.check_batch(
        user=user,
        checks=[
            PermissionCheck(resource="datasets/123", action="read"),
            PermissionCheck(resource="datasets/456", action="read"),
            PermissionCheck(resource="pipelines/789", action="execute"),
        ]
    )

    # BAD: Individual checks - N round trips (avoid this pattern)
    # for resource in resources:
    #     await service.check(user, resource, action)  # N+1 queries!
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, Any

from pydantic import BaseModel

from forge_collab.sharing.models import PermissionLevel, ResourceType


class User(Protocol):
    """Protocol for user objects (provided by forge-core auth)."""

    @property
    def id(self) -> str:
        """User identifier."""
        ...

    @property
    def groups(self) -> list[str]:
        """User's group memberships."""
        ...

    @property
    def roles(self) -> list[str]:
        """User's roles."""
        ...


class AuthProvider(Protocol):
    """Protocol for authentication provider (from forge-core)."""

    async def authorize(
        self, user: User, resource: str, action: str
    ) -> bool:
        """Check if user has permission for action on resource."""
        ...

    async def authorize_batch(
        self, user: User, checks: list[tuple[str, str]]
    ) -> dict[str, bool]:
        """Check multiple permissions in a single query.

        Args:
            user: The user to check permissions for
            checks: List of (resource, action) tuples

        Returns:
            Dict mapping "resource:action" to boolean result
        """
        ...


@dataclass
class PermissionCheck:
    """A single permission check request."""

    resource: str  # e.g., "datasets/123" or "pipelines/abc"
    action: str  # e.g., "read", "write", "execute", "delete"
    context: dict[str, Any] = field(default_factory=dict)


class PermissionResult(BaseModel):
    """Result of a permission check."""

    resource: str
    action: str
    allowed: bool
    reason: str | None = None
    checked_at: datetime


class PermissionService:
    """Permission service with batched checks to avoid N+1 queries.

    This service wraps the forge-core auth provider and adds batching
    capabilities for efficient permission checking across multiple resources.

    The key method is check_batch() which performs multiple permission checks
    in a single database round-trip, addressing the N+1 query issue from
    the architectural review.
    """

    def __init__(self, auth_provider: AuthProvider):
        """Initialize permission service.

        Args:
            auth_provider: The authentication provider from forge-core
        """
        self._auth = auth_provider

    async def check(
        self,
        user: User,
        resource: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> PermissionResult:
        """Check a single permission.

        For checking multiple permissions, use check_batch() instead
        to avoid N+1 query issues.

        Args:
            user: User to check permission for
            resource: Resource identifier (e.g., "datasets/123")
            action: Action to check (e.g., "read", "write")
            context: Optional context for ABAC policies

        Returns:
            PermissionResult with the check outcome
        """
        allowed = await self._auth.authorize(user, resource, action)
        return PermissionResult(
            resource=resource,
            action=action,
            allowed=allowed,
            checked_at=datetime.utcnow(),
        )

    async def check_batch(
        self,
        user: User,
        checks: list[PermissionCheck],
    ) -> dict[str, PermissionResult]:
        """Check multiple permissions in a single database round-trip.

        This method addresses the N+1 query issue by batching permission
        checks into a single query. Always prefer this method when checking
        permissions for multiple resources.

        Args:
            user: User to check permissions for
            checks: List of PermissionCheck objects

        Returns:
            Dict mapping "resource:action" to PermissionResult

        Example:
            results = await service.check_batch(
                user=current_user,
                checks=[
                    PermissionCheck(resource="datasets/123", action="read"),
                    PermissionCheck(resource="datasets/456", action="write"),
                ]
            )

            if results["datasets/123:read"].allowed:
                # User can read dataset 123
                pass
        """
        if not checks:
            return {}

        # Build the batch request as (resource, action) tuples
        batch_checks = [(c.resource, c.action) for c in checks]

        # Single database round-trip for all checks
        raw_results = await self._auth.authorize_batch(user, batch_checks)

        # Convert to PermissionResult objects
        now = datetime.utcnow()
        results: dict[str, PermissionResult] = {}

        for check in checks:
            key = f"{check.resource}:{check.action}"
            allowed = raw_results.get(key, False)
            results[key] = PermissionResult(
                resource=check.resource,
                action=check.action,
                allowed=allowed,
                checked_at=now,
            )

        return results

    async def filter_accessible(
        self,
        user: User,
        resources: list[str],
        action: str,
    ) -> list[str]:
        """Filter a list of resources to only those the user can access.

        This is a convenience method built on check_batch() for the common
        pattern of filtering a list of resources.

        Args:
            user: User to check permissions for
            resources: List of resource identifiers
            action: Action to check (e.g., "read")

        Returns:
            List of resource identifiers the user can access
        """
        if not resources:
            return []

        checks = [
            PermissionCheck(resource=r, action=action)
            for r in resources
        ]

        results = await self.check_batch(user, checks)

        return [
            r for r in resources
            if results.get(f"{r}:{action}", PermissionResult(
                resource=r, action=action, allowed=False, checked_at=datetime.utcnow()
            )).allowed
        ]

    async def check_any(
        self,
        user: User,
        checks: list[PermissionCheck],
    ) -> bool:
        """Check if user has ANY of the specified permissions.

        Args:
            user: User to check permissions for
            checks: List of permission checks

        Returns:
            True if user has at least one of the permissions
        """
        results = await self.check_batch(user, checks)
        return any(r.allowed for r in results.values())

    async def check_all(
        self,
        user: User,
        checks: list[PermissionCheck],
    ) -> bool:
        """Check if user has ALL of the specified permissions.

        Args:
            user: User to check permissions for
            checks: List of permission checks

        Returns:
            True if user has all of the permissions
        """
        results = await self.check_batch(user, checks)
        return all(r.allowed for r in results.values())
