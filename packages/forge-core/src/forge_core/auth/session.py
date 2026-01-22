"""
Session Management

This module provides session management for authenticated users,
including token storage, refresh, and invalidation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Protocol, runtime_checkable
from uuid import uuid4

if TYPE_CHECKING:
    from forge_core.auth.user import User


@dataclass
class Session:
    """
    Represents an authenticated user session.

    Attributes:
        id: Unique session identifier
        user_id: ID of the authenticated user
        access_token: Current access token
        refresh_token: Token for refreshing the session
        created_at: When the session was created
        expires_at: When the session expires
        last_activity: Timestamp of last activity
        ip_address: IP address of the client
        user_agent: User agent string of the client
        metadata: Additional session metadata
    """

    id: str
    user_id: str
    access_token: str
    refresh_token: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    last_activity: datetime | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        user_id: str,
        access_token: str,
        refresh_token: str | None = None,
        ttl: timedelta = timedelta(hours=1),
        **kwargs,
    ) -> "Session":
        """
        Create a new session.

        Args:
            user_id: ID of the authenticated user
            access_token: Current access token
            refresh_token: Token for refreshing the session
            ttl: Time-to-live for the session
            **kwargs: Additional session attributes

        Returns:
            New Session instance
        """
        now = datetime.utcnow()
        return cls(
            id=str(uuid4()),
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            created_at=now,
            expires_at=now + ttl,
            last_activity=now,
            **kwargs,
        )

    def is_expired(self) -> bool:
        """Check if the session has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def is_active(self) -> bool:
        """Check if the session is active (not expired)."""
        return not self.is_expired()

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def extend(self, ttl: timedelta) -> None:
        """Extend the session expiration time."""
        self.expires_at = datetime.utcnow() + ttl


@runtime_checkable
class SessionManager(Protocol):
    """
    Protocol for session management.

    Implementations should handle session storage, retrieval, and lifecycle.
    """

    async def create_session(
        self,
        user: "User",
        access_token: str,
        refresh_token: str | None = None,
        ttl: timedelta = timedelta(hours=1),
        **metadata,
    ) -> Session:
        """
        Create a new session for a user.

        Args:
            user: Authenticated user
            access_token: Access token for the session
            refresh_token: Optional refresh token
            ttl: Session time-to-live
            **metadata: Additional session metadata

        Returns:
            Created Session object
        """
        ...

    async def get_session(self, session_id: str) -> Session | None:
        """
        Retrieve a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found and active, None otherwise
        """
        ...

    async def get_session_by_token(self, access_token: str) -> Session | None:
        """
        Retrieve a session by access token.

        Args:
            access_token: Access token

        Returns:
            Session if found and active, None otherwise
        """
        ...

    async def update_session(self, session: Session) -> None:
        """
        Update a session (e.g., after token refresh).

        Args:
            session: Session to update
        """
        ...

    async def invalidate_session(self, session_id: str) -> None:
        """
        Invalidate a session (logout).

        Args:
            session_id: Session to invalidate
        """
        ...

    async def invalidate_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user.

        Args:
            user_id: User whose sessions to invalidate

        Returns:
            Number of sessions invalidated
        """
        ...

    async def cleanup_expired(self) -> int:
        """
        Remove expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        ...


class BaseSessionManager(ABC):
    """
    Abstract base class for session managers.

    Provides common session management logic that concrete implementations extend.
    """

    def __init__(
        self,
        default_ttl: timedelta = timedelta(hours=1),
        max_sessions_per_user: int = 10,
    ) -> None:
        """
        Initialize the session manager.

        Args:
            default_ttl: Default session time-to-live
            max_sessions_per_user: Maximum concurrent sessions per user
        """
        self.default_ttl = default_ttl
        self.max_sessions_per_user = max_sessions_per_user

    @abstractmethod
    async def create_session(
        self,
        user: "User",
        access_token: str,
        refresh_token: str | None = None,
        ttl: timedelta | None = None,
        **metadata,
    ) -> Session:
        """Create a new session."""
        ...

    @abstractmethod
    async def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        ...

    @abstractmethod
    async def get_session_by_token(self, access_token: str) -> Session | None:
        """Get a session by access token."""
        ...

    @abstractmethod
    async def update_session(self, session: Session) -> None:
        """Update a session."""
        ...

    @abstractmethod
    async def invalidate_session(self, session_id: str) -> None:
        """Invalidate a session."""
        ...

    @abstractmethod
    async def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for a user."""
        ...

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Clean up expired sessions."""
        ...
