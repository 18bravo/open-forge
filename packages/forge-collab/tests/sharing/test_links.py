"""Tests for ShareableLink model and service."""

from datetime import datetime, timedelta

import pytest

from forge_collab.sharing.links import (
    ShareableLink,
    ShareableLinkService,
    CreateLinkRequest,
)
from forge_collab.sharing.models import PermissionLevel, ResourceType


class TestShareableLink:
    """Tests for ShareableLink model."""

    def test_link_not_expired(self):
        """Test link expiration check when not expired."""
        link = ShareableLink(
            id="link-123",
            token="abc123",
            resource_type=ResourceType.DATASET,
            resource_id="ds-456",
            created_by="user-123",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

        assert link.is_expired is False
        assert link.is_valid is True

    def test_link_expired(self):
        """Test link expiration check when expired."""
        link = ShareableLink(
            id="link-123",
            token="abc123",
            resource_type=ResourceType.DATASET,
            resource_id="ds-456",
            created_by="user-123",
            created_at=datetime.utcnow() - timedelta(hours=48),
            expires_at=datetime.utcnow() - timedelta(hours=24),
        )

        assert link.is_expired is True
        assert link.is_valid is False

    def test_link_no_expiration(self):
        """Test link with no expiration is always valid."""
        link = ShareableLink(
            id="link-123",
            token="abc123",
            resource_type=ResourceType.DATASET,
            resource_id="ds-456",
            created_by="user-123",
            created_at=datetime.utcnow(),
            expires_at=None,
        )

        assert link.is_expired is False
        assert link.is_valid is True

    def test_link_exhausted(self):
        """Test link exhausted when max_uses reached."""
        link = ShareableLink(
            id="link-123",
            token="abc123",
            resource_type=ResourceType.DATASET,
            resource_id="ds-456",
            created_by="user-123",
            created_at=datetime.utcnow(),
            max_uses=5,
            use_count=5,
        )

        assert link.is_exhausted is True
        assert link.is_valid is False

    def test_link_not_exhausted(self):
        """Test link not exhausted when under max_uses."""
        link = ShareableLink(
            id="link-123",
            token="abc123",
            resource_type=ResourceType.DATASET,
            resource_id="ds-456",
            created_by="user-123",
            created_at=datetime.utcnow(),
            max_uses=5,
            use_count=3,
        )

        assert link.is_exhausted is False
        assert link.is_valid is True

    def test_link_disabled(self):
        """Test disabled link is not valid."""
        link = ShareableLink(
            id="link-123",
            token="abc123",
            resource_type=ResourceType.DATASET,
            resource_id="ds-456",
            created_by="user-123",
            created_at=datetime.utcnow(),
            enabled=False,
        )

        assert link.is_valid is False


class TestShareableLinkService:
    """Tests for ShareableLinkService."""

    def test_generate_token(self):
        """Test secure token generation."""
        service = ShareableLinkService()

        token1 = service._generate_token()
        token2 = service._generate_token()

        # Tokens should be unique
        assert token1 != token2

        # Tokens should be URL-safe
        assert all(c.isalnum() or c in "-_" for c in token1)

    def test_get_share_url(self):
        """Test share URL generation."""
        service = ShareableLinkService(base_url="https://app.example.com")

        link = ShareableLink(
            id="link-123",
            token="abc123xyz",
            resource_type=ResourceType.DATASET,
            resource_id="ds-456",
            created_by="user-123",
            created_at=datetime.utcnow(),
        )

        url = service.get_share_url(link)

        assert url == "https://app.example.com/share/abc123xyz"
