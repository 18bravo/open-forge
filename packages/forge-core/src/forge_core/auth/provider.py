"""
Authentication Provider Abstraction

This module defines the AuthProvider protocol for OAuth2/OIDC authentication.
Implementations can support various identity providers (Auth0, Okta, Keycloak, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from forge_core.auth.row_level import Filter
    from forge_core.auth.user import User


class AuthProviderType(str, Enum):
    """Supported authentication provider types."""

    OIDC = "oidc"
    OAUTH2 = "oauth2"
    SAML = "saml"
    API_KEY = "api_key"
    INTERNAL = "internal"


@dataclass
class AuthProviderConfig:
    """
    Configuration for an authentication provider.

    Attributes:
        provider_type: Type of authentication provider
        issuer: Token issuer URL (for OIDC/OAuth2)
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret (optional, for confidential clients)
        audience: Expected token audience
        jwks_uri: URI for JSON Web Key Set (auto-discovered for OIDC)
        scopes: Required OAuth2 scopes
        redirect_uri: OAuth2 redirect URI for authorization code flow
    """

    provider_type: AuthProviderType
    issuer: str
    client_id: str
    client_secret: str | None = None
    audience: str | None = None
    jwks_uri: str | None = None
    scopes: list[str] | None = None
    redirect_uri: str | None = None


@runtime_checkable
class AuthProvider(Protocol):
    """
    Protocol for authentication providers.

    Implementations must provide methods for:
    - Token validation and user authentication
    - Authorization checks for resources and actions
    - Row-level security filter generation

    Example usage:
        >>> provider = OIDCAuthProvider(config)
        >>> user = await provider.authenticate(token)
        >>> if await provider.authorize(user, "dataset:123", "read"):
        ...     # User can read the dataset
    """

    async def authenticate(self, token: str) -> "User":
        """
        Authenticate a user from a token.

        Args:
            token: Bearer token (JWT) from the request

        Returns:
            Authenticated User object

        Raises:
            AuthenticationError: If the token is invalid or expired
        """
        ...

    async def authorize(self, user: "User", resource: str, action: str) -> bool:
        """
        Check if a user is authorized to perform an action on a resource.

        Args:
            user: The authenticated user
            resource: Resource identifier (e.g., "dataset:123", "pipeline:456")
            action: Action to perform (e.g., "read", "write", "delete", "execute")

        Returns:
            True if authorized, False otherwise
        """
        ...

    async def get_row_filter(
        self, user: "User", object_type: str
    ) -> "Filter | None":
        """
        Get row-level security filter for a user and object type.

        Args:
            user: The authenticated user
            object_type: Type of object to filter (e.g., "employee", "transaction")

        Returns:
            Filter to apply to queries, or None if no filtering needed
        """
        ...

    async def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """
        Refresh an access token.

        Args:
            refresh_token: The refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            AuthenticationError: If the refresh token is invalid
        """
        ...


class BaseAuthProvider(ABC):
    """
    Abstract base class for authentication providers.

    Provides common functionality that concrete implementations can use.
    """

    def __init__(self, config: AuthProviderConfig) -> None:
        """Initialize the provider with configuration."""
        self.config = config

    @abstractmethod
    async def authenticate(self, token: str) -> "User":
        """Authenticate a user from a token."""
        ...

    @abstractmethod
    async def authorize(self, user: "User", resource: str, action: str) -> bool:
        """Check if a user is authorized for an action."""
        ...

    @abstractmethod
    async def get_row_filter(
        self, user: "User", object_type: str
    ) -> "Filter | None":
        """Get row-level security filter."""
        ...

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """Refresh an access token."""
        ...

    async def validate_token_structure(self, token: str) -> dict:
        """
        Validate token structure without verifying signature.

        Useful for extracting claims before full validation.
        """
        # Stub: Implement JWT decoding without verification
        raise NotImplementedError

    async def verify_token_signature(self, token: str) -> dict:
        """
        Verify token signature and return claims.

        Fetches JWKS from the provider and validates the signature.
        """
        # Stub: Implement JWT signature verification
        raise NotImplementedError
