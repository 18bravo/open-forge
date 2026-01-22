"""Pytest configuration and fixtures for forge-collab tests."""

from datetime import datetime
from typing import Any

import pytest

from forge_collab.sharing.permissions import PermissionCheck, User


class MockUser:
    """Mock user for testing."""

    def __init__(
        self,
        id: str = "user-123",
        groups: list[str] | None = None,
        roles: list[str] | None = None,
    ):
        self._id = id
        self._groups = groups or []
        self._roles = roles or []

    @property
    def id(self) -> str:
        return self._id

    @property
    def groups(self) -> list[str]:
        return self._groups

    @property
    def roles(self) -> list[str]:
        return self._roles


class MockAuthProvider:
    """Mock auth provider for testing batched permission checks."""

    def __init__(self, permissions: dict[str, bool] | None = None):
        """Initialize with permission map.

        Args:
            permissions: Dict mapping "resource:action" to boolean
        """
        self._permissions = permissions or {}

    async def authorize(
        self, user: User, resource: str, action: str
    ) -> bool:
        """Check single permission."""
        key = f"{resource}:{action}"
        return self._permissions.get(key, False)

    async def authorize_batch(
        self, user: User, checks: list[tuple[str, str]]
    ) -> dict[str, bool]:
        """Check multiple permissions in batch."""
        results = {}
        for resource, action in checks:
            key = f"{resource}:{action}"
            results[key] = self._permissions.get(key, False)
        return results


@pytest.fixture
def mock_user() -> MockUser:
    """Create a mock user."""
    return MockUser(
        id="user-123",
        groups=["team-a", "engineers"],
        roles=["editor"],
    )


@pytest.fixture
def mock_auth_provider() -> MockAuthProvider:
    """Create a mock auth provider with sample permissions."""
    return MockAuthProvider({
        "datasets/123:read": True,
        "datasets/123:write": True,
        "datasets/456:read": True,
        "datasets/456:write": False,
        "pipelines/789:read": True,
        "pipelines/789:execute": False,
    })


@pytest.fixture
def sample_audit_event() -> dict[str, Any]:
    """Create sample audit event data."""
    return {
        "event_type": "dataset.created",
        "action": "create",
        "actor_id": "user-123",
        "resource_type": "dataset",
        "resource_id": "ds-456",
        "resource_name": "Customer Data",
        "success": True,
    }
