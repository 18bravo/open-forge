"""Tests for PermissionService with batched permission checks."""

import pytest

from forge_collab.sharing.permissions import (
    PermissionService,
    PermissionCheck,
    PermissionResult,
)


class TestPermissionService:
    """Tests for PermissionService."""

    @pytest.mark.asyncio
    async def test_check_single_permission_allowed(
        self, mock_user, mock_auth_provider
    ):
        """Test checking a single allowed permission."""
        service = PermissionService(mock_auth_provider)

        result = await service.check(
            user=mock_user,
            resource="datasets/123",
            action="read",
        )

        assert result.allowed is True
        assert result.resource == "datasets/123"
        assert result.action == "read"

    @pytest.mark.asyncio
    async def test_check_single_permission_denied(
        self, mock_user, mock_auth_provider
    ):
        """Test checking a single denied permission."""
        service = PermissionService(mock_auth_provider)

        result = await service.check(
            user=mock_user,
            resource="datasets/456",
            action="write",
        )

        assert result.allowed is False

    @pytest.mark.asyncio
    async def test_check_batch_multiple_permissions(
        self, mock_user, mock_auth_provider
    ):
        """Test batched permission checking - addresses N+1 query issue."""
        service = PermissionService(mock_auth_provider)

        checks = [
            PermissionCheck(resource="datasets/123", action="read"),
            PermissionCheck(resource="datasets/123", action="write"),
            PermissionCheck(resource="datasets/456", action="read"),
            PermissionCheck(resource="datasets/456", action="write"),
            PermissionCheck(resource="pipelines/789", action="execute"),
        ]

        results = await service.check_batch(user=mock_user, checks=checks)

        # All checks should be performed
        assert len(results) == 5

        # Verify specific results
        assert results["datasets/123:read"].allowed is True
        assert results["datasets/123:write"].allowed is True
        assert results["datasets/456:read"].allowed is True
        assert results["datasets/456:write"].allowed is False
        assert results["pipelines/789:execute"].allowed is False

    @pytest.mark.asyncio
    async def test_check_batch_empty_list(self, mock_user, mock_auth_provider):
        """Test batched check with empty list."""
        service = PermissionService(mock_auth_provider)

        results = await service.check_batch(user=mock_user, checks=[])

        assert results == {}

    @pytest.mark.asyncio
    async def test_filter_accessible_resources(
        self, mock_user, mock_auth_provider
    ):
        """Test filtering resources to accessible ones."""
        service = PermissionService(mock_auth_provider)

        resources = [
            "datasets/123",
            "datasets/456",
            "datasets/789",  # Not in permissions = False
        ]

        accessible = await service.filter_accessible(
            user=mock_user,
            resources=resources,
            action="read",
        )

        assert "datasets/123" in accessible
        assert "datasets/456" in accessible
        assert "datasets/789" not in accessible

    @pytest.mark.asyncio
    async def test_check_any_permission(self, mock_user, mock_auth_provider):
        """Test checking if user has ANY of the permissions."""
        service = PermissionService(mock_auth_provider)

        # At least one is allowed
        checks = [
            PermissionCheck(resource="datasets/456", action="write"),  # False
            PermissionCheck(resource="datasets/123", action="read"),  # True
        ]

        has_any = await service.check_any(user=mock_user, checks=checks)
        assert has_any is True

        # None are allowed
        checks = [
            PermissionCheck(resource="datasets/456", action="write"),  # False
            PermissionCheck(resource="pipelines/789", action="execute"),  # False
        ]

        has_any = await service.check_any(user=mock_user, checks=checks)
        assert has_any is False

    @pytest.mark.asyncio
    async def test_check_all_permissions(self, mock_user, mock_auth_provider):
        """Test checking if user has ALL of the permissions."""
        service = PermissionService(mock_auth_provider)

        # All are allowed
        checks = [
            PermissionCheck(resource="datasets/123", action="read"),
            PermissionCheck(resource="datasets/123", action="write"),
        ]

        has_all = await service.check_all(user=mock_user, checks=checks)
        assert has_all is True

        # Not all are allowed
        checks = [
            PermissionCheck(resource="datasets/123", action="read"),  # True
            PermissionCheck(resource="datasets/456", action="write"),  # False
        ]

        has_all = await service.check_all(user=mock_user, checks=checks)
        assert has_all is False
