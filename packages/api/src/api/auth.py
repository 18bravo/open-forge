"""
JWT authentication utilities for Open Forge API.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # user_id
    username: str
    email: Optional[str] = None
    roles: list[str] = []
    permissions: list[str] = []
    exp: datetime
    iat: datetime


class JWTConfig:
    """JWT configuration from environment variables."""

    @property
    def secret_key(self) -> str:
        """Get JWT secret key from environment."""
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
        return os.environ.get("JWT_ALGORITHM", "HS256")

    @property
    def access_token_expire_minutes(self) -> int:
        """Get access token expiration in minutes."""
        return int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


jwt_config = JWTConfig()


def create_access_token(
    user_id: str,
    username: str,
    email: Optional[str] = None,
    roles: Optional[list[str]] = None,
    permissions: Optional[list[str]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: The user's unique identifier
        username: The user's username
        email: Optional email address
        roles: List of user roles
        permissions: List of user permissions
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=jwt_config.access_token_expire_minutes)

    payload = {
        "sub": user_id,
        "username": username,
        "email": email,
        "roles": roles or ["user"],
        "permissions": permissions or ["read"],
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(
        payload,
        jwt_config.secret_key,
        algorithm=jwt_config.algorithm,
    )


def decode_access_token(token: str) -> Optional[TokenPayload]:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT token string

    Returns:
        TokenPayload if valid, None if invalid or expired

    Raises:
        jwt.InvalidTokenError: If token is malformed
        jwt.ExpiredSignatureError: If token has expired
    """
    try:
        payload = jwt.decode(
            token,
            jwt_config.secret_key,
            algorithms=[jwt_config.algorithm],
        )
        return TokenPayload(
            sub=payload["sub"],
            username=payload["username"],
            email=payload.get("email"),
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
