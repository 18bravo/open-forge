"""
JWT Authentication Provider

This module provides a JWT-based authentication provider for Open Forge.
It validates JWT tokens and creates User objects from the token claims.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from jose import jwt, JWTError, ExpiredSignatureError as JoseExpiredSignatureError
from pydantic import BaseModel

from forge_core.auth.provider import AuthProviderConfig, AuthProviderType, BaseAuthProvider
from forge_core.auth.user import User

if TYPE_CHECKING:
    from forge_core.auth.row_level import Filter


class JWTConfig:
    """JWT configuration from environment variables."""

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
    ) -> None:
        """
        Initialize JWT configuration.

        Args:
            secret_key: Secret key for signing tokens. If not provided, uses JWT_SECRET_KEY env var.
            algorithm: JWT algorithm (default: HS256)
            access_token_expire_minutes: Token expiration in minutes (default: 30)
        """
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes

    @property
    def secret_key(self) -> str:
        """Get JWT secret key from config or environment."""
        if self._secret_key:
            return self._secret_key
        key = os.environ.get("JWT_SECRET_KEY")
        if not key:
            raise ValueError(
                "JWT_SECRET_KEY environment variable is required. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return key

    @property
    def algorithm(self) -> str:
        """Get JWT algorithm."""
        return os.environ.get("JWT_ALGORITHM", self._algorithm)

    @property
    def access_token_expire_minutes(self) -> int:
        """Get access token expiration in minutes."""
        return int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(self._access_token_expire_minutes)))


class TokenPayload(BaseModel):
    """JWT token payload model."""
    sub: str  # user_id
    username: str
    email: str | None = None
    name: str | None = None
    roles: list[str] = []
    permissions: list[str] = []
    tenant_id: str | None = None
    exp: datetime
    iat: datetime


class JWTAuthProvider(BaseAuthProvider):
    """
    JWT-based authentication provider.

    This provider validates JWT tokens signed with a secret key and creates
    User objects from the token claims.

    Example:
        >>> config = AuthProviderConfig(
        ...     provider_type=AuthProviderType.INTERNAL,
        ...     issuer="open-forge",
        ...     client_id="api",
        ... )
        >>> jwt_config = JWTConfig(secret_key="your-secret-key")
        >>> provider = JWTAuthProvider(config, jwt_config)
        >>> user = await provider.authenticate(token)
    """

    def __init__(
        self,
        config: AuthProviderConfig,
        jwt_config: JWTConfig | None = None,
    ) -> None:
        """
        Initialize the JWT auth provider.

        Args:
            config: Auth provider configuration
            jwt_config: JWT-specific configuration (uses env vars if not provided)
        """
        super().__init__(config)
        self.jwt_config = jwt_config or JWTConfig()

    async def authenticate(self, token: str) -> User:
        """
        Authenticate a user from a JWT token.

        Args:
            token: JWT token string

        Returns:
            Authenticated User object

        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_config.secret_key,
                algorithms=[self.jwt_config.algorithm],
            )

            return User(
                id=payload["sub"],
                email=payload.get("email", ""),
                name=payload.get("name", payload.get("username", "")),
                roles=frozenset(payload.get("roles", [])),
                permissions=frozenset(payload.get("permissions", [])),
                tenant_id=payload.get("tenant_id"),
                last_login=datetime.now(timezone.utc),
            )
        except JoseExpiredSignatureError as e:
            raise JWTError("Token has expired") from e
        except JWTError as e:
            raise JWTError(f"Invalid token: {e}") from e

    async def authorize(self, user: User, resource: str, action: str) -> bool:
        """
        Check if a user is authorized for an action on a resource.

        Authorization logic:
        1. Admin users have full access
        2. Check for exact permission match (resource:action)
        3. Check for wildcard permissions (resource:* or *:action)

        Args:
            user: The authenticated user
            resource: Resource identifier (e.g., "dataset", "pipeline:123")
            action: Action to perform (e.g., "read", "write")

        Returns:
            True if authorized
        """
        # Admins have full access
        if user.is_admin():
            return True

        # Check for full wildcard
        if "*" in user.permissions:
            return True

        # Build permission string
        permission = f"{resource}:{action}"

        # Exact match
        if permission in user.permissions:
            return True

        # Check for resource wildcard (e.g., "dataset:*")
        resource_parts = resource.split(":")
        resource_type = resource_parts[0]
        if f"{resource_type}:*" in user.permissions:
            return True

        # Check for action wildcard (e.g., "*:read")
        if f"*:{action}" in user.permissions:
            return True

        return False

    async def get_row_filter(
        self, user: User, object_type: str
    ) -> "Filter | None":
        """
        Get row-level security filter for a user.

        Default implementation returns None (no filtering).
        Override in subclass to implement row-level security.

        Args:
            user: The authenticated user
            object_type: Type of object to filter

        Returns:
            Filter to apply, or None for no filtering
        """
        # Default: no row-level filtering
        # Subclasses can override to implement RLS
        return None

    async def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """
        Refresh an access token.

        Args:
            refresh_token: The refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            JWTError: If refresh token is invalid
        """
        # Validate refresh token
        try:
            payload = jwt.decode(
                refresh_token,
                self.jwt_config.secret_key,
                algorithms=[self.jwt_config.algorithm],
            )
        except JoseExpiredSignatureError:
            raise JWTError("Refresh token has expired")
        except JWTError as e:
            raise JWTError(f"Invalid refresh token: {e}")

        # Create new tokens
        now = datetime.now(timezone.utc)
        access_expire = now + timedelta(minutes=self.jwt_config.access_token_expire_minutes)
        refresh_expire = now + timedelta(days=7)

        # Create new access token
        access_payload = {
            "sub": payload["sub"],
            "username": payload.get("username", ""),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
            "tenant_id": payload.get("tenant_id"),
            "exp": access_expire,
            "iat": now,
        }
        new_access_token = jwt.encode(
            access_payload,
            self.jwt_config.secret_key,
            algorithm=self.jwt_config.algorithm,
        )

        # Create new refresh token
        refresh_payload = {
            "sub": payload["sub"],
            "username": payload.get("username", ""),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
            "tenant_id": payload.get("tenant_id"),
            "exp": refresh_expire,
            "iat": now,
            "type": "refresh",
        }
        new_refresh_token = jwt.encode(
            refresh_payload,
            self.jwt_config.secret_key,
            algorithm=self.jwt_config.algorithm,
        )

        return new_access_token, new_refresh_token

    def create_access_token(
        self,
        user_id: str,
        username: str,
        email: str | None = None,
        name: str | None = None,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        tenant_id: str | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: The user's unique identifier
            username: The user's username
            email: Optional email address
            name: Optional display name
            roles: List of user roles
            permissions: List of user permissions
            tenant_id: Optional tenant ID
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token string
        """
        now = datetime.now(timezone.utc)

        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=self.jwt_config.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "username": username,
            "email": email,
            "name": name or username,
            "roles": roles or ["user"],
            "permissions": permissions or ["read"],
            "tenant_id": tenant_id,
            "exp": expire,
            "iat": now,
        }

        return jwt.encode(
            payload,
            self.jwt_config.secret_key,
            algorithm=self.jwt_config.algorithm,
        )

    def create_refresh_token(
        self,
        user_id: str,
        username: str,
        email: str | None = None,
        name: str | None = None,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        tenant_id: str | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a JWT refresh token.

        Args:
            user_id: The user's unique identifier
            username: The user's username
            email: Optional email address
            name: Optional display name
            roles: List of user roles
            permissions: List of user permissions
            tenant_id: Optional tenant ID
            expires_delta: Optional custom expiration time (default: 7 days)

        Returns:
            Encoded JWT refresh token string
        """
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(days=7))

        payload = {
            "sub": user_id,
            "username": username,
            "email": email,
            "name": name or username,
            "roles": roles or ["user"],
            "permissions": permissions or ["read"],
            "tenant_id": tenant_id,
            "exp": expire,
            "iat": now,
            "type": "refresh",
        }

        return jwt.encode(
            payload,
            self.jwt_config.secret_key,
            algorithm=self.jwt_config.algorithm,
        )
