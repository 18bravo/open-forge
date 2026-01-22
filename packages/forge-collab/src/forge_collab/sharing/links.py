"""Shareable links - Time-limited, permission-scoped sharing URLs."""

import secrets
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field

from forge_collab.sharing.models import PermissionLevel, ResourceType


class ShareableLink(BaseModel):
    """A shareable link for granting access to a resource.

    Shareable links provide a way to share resources with external users
    or users who don't have direct access. Links can be:
    - Time-limited (expires_at)
    - Scoped to specific permission levels
    - Password protected (optional)
    - Limited in usage count
    """

    id: str
    token: str = Field(description="Unique token used in the URL")
    resource_type: ResourceType
    resource_id: str
    permission_level: PermissionLevel = PermissionLevel.VIEW
    created_by: str
    created_at: datetime
    expires_at: datetime | None = None
    password_hash: str | None = None
    max_uses: int | None = None
    use_count: int = 0
    enabled: bool = True
    name: str | None = None
    description: str | None = None

    @property
    def is_expired(self) -> bool:
        """Check if the link has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_exhausted(self) -> bool:
        """Check if the link has reached its max uses."""
        if self.max_uses is None:
            return False
        return self.use_count >= self.max_uses

    @property
    def is_valid(self) -> bool:
        """Check if the link can be used."""
        return self.enabled and not self.is_expired and not self.is_exhausted


class CreateLinkRequest(BaseModel):
    """Request to create a shareable link."""

    resource_type: ResourceType
    resource_id: str
    permission_level: PermissionLevel = PermissionLevel.VIEW
    expires_in: timedelta | None = None
    password: str | None = None
    max_uses: int | None = None
    name: str | None = None
    description: str | None = None


class ShareableLinkService:
    """Service for managing shareable links.

    This is a scaffold interface. Full implementation requires:
    - Database storage (from forge-core)
    - Password hashing (bcrypt)
    - URL generation based on deployment config
    """

    def __init__(self, base_url: str = ""):
        """Initialize the shareable link service.

        Args:
            base_url: Base URL for generating shareable links
        """
        self._base_url = base_url

    def _generate_token(self, length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)

    async def create_link(
        self,
        creator_id: str,
        request: CreateLinkRequest,
    ) -> ShareableLink:
        """Create a new shareable link.

        Args:
            creator_id: ID of the user creating the link
            request: Link creation request

        Returns:
            The created ShareableLink

        Raises:
            NotImplementedError: Full implementation requires database
        """
        # Generate secure token
        token = self._generate_token()

        # Calculate expiration
        expires_at = None
        if request.expires_in:
            expires_at = datetime.utcnow() + request.expires_in

        # Hash password if provided
        password_hash = None
        if request.password:
            # TODO: Use bcrypt for password hashing
            password_hash = f"hashed:{request.password}"

        link = ShareableLink(
            id=secrets.token_hex(16),
            token=token,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            permission_level=request.permission_level,
            created_by=creator_id,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            password_hash=password_hash,
            max_uses=request.max_uses,
            name=request.name,
            description=request.description,
        )

        # TODO: Store link in database
        raise NotImplementedError("Database storage not implemented")

    async def get_link_by_token(self, token: str) -> ShareableLink | None:
        """Retrieve a shareable link by its token.

        Args:
            token: The link token

        Returns:
            The ShareableLink if found and valid, None otherwise
        """
        # TODO: Retrieve from database
        raise NotImplementedError("Database storage not implemented")

    async def validate_and_use(
        self,
        token: str,
        password: str | None = None,
    ) -> tuple[ShareableLink | None, str | None]:
        """Validate a shareable link and increment its use count.

        Args:
            token: The link token
            password: Password if link is password-protected

        Returns:
            Tuple of (link, error_message). Link is None if invalid.
        """
        link = await self.get_link_by_token(token)

        if link is None:
            return None, "Link not found"

        if not link.enabled:
            return None, "Link has been disabled"

        if link.is_expired:
            return None, "Link has expired"

        if link.is_exhausted:
            return None, "Link has reached maximum uses"

        if link.password_hash and not password:
            return None, "Password required"

        if link.password_hash:
            # TODO: Verify password with bcrypt
            if f"hashed:{password}" != link.password_hash:
                return None, "Invalid password"

        # Increment use count
        # TODO: Atomic increment in database
        link.use_count += 1

        return link, None

    async def revoke_link(self, link_id: str, revoked_by: str) -> bool:
        """Revoke (disable) a shareable link.

        Args:
            link_id: ID of the link to revoke
            revoked_by: ID of the user revoking the link

        Returns:
            True if link was revoked, False if not found
        """
        # TODO: Update link in database
        raise NotImplementedError("Database storage not implemented")

    async def list_links_for_resource(
        self,
        resource_type: ResourceType,
        resource_id: str,
        include_expired: bool = False,
    ) -> list[ShareableLink]:
        """List all shareable links for a resource.

        Args:
            resource_type: Type of the resource
            resource_id: ID of the resource
            include_expired: Whether to include expired links

        Returns:
            List of ShareableLinks
        """
        # TODO: Query database
        raise NotImplementedError("Database storage not implemented")

    def get_share_url(self, link: ShareableLink) -> str:
        """Generate the full shareable URL for a link.

        Args:
            link: The ShareableLink

        Returns:
            Full URL for sharing
        """
        return f"{self._base_url}/share/{link.token}"
