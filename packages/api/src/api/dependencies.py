"""
FastAPI dependencies for dependency injection.
"""
from typing import Annotated, AsyncGenerator, Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.connection import AsyncSessionLocal
from core.messaging.events import EventBus
from api.schemas.common import UserContext


# Global event bus instance
_event_bus: Optional[EventBus] = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.

    Yields a session and handles commit/rollback automatically.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_event_bus() -> EventBus:
    """
    Dependency that provides the event bus instance.

    Raises:
        RuntimeError: If event bus is not initialized.
    """
    if _event_bus is None:
        raise RuntimeError("EventBus not initialized. Call init_event_bus() first.")
    return _event_bus


async def init_event_bus() -> EventBus:
    """Initialize the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        await _event_bus.connect()
    return _event_bus


async def close_event_bus() -> None:
    """Close the global event bus connection."""
    global _event_bus
    if _event_bus is not None:
        await _event_bus.disconnect()
        _event_bus = None


async def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-ID")] = None,
) -> UserContext:
    """
    Dependency that extracts and validates the current user from request headers.

    In production, this would validate JWT tokens. For development, it accepts
    user info from headers.

    Args:
        authorization: Bearer token for authentication
        x_user_id: User ID header (for development/testing)

    Returns:
        UserContext with user information

    Raises:
        HTTPException: If authentication fails
    """
    # Development mode: accept user ID from header
    if x_user_id:
        return UserContext(
            user_id=x_user_id,
            username=f"user_{x_user_id}",
            roles=["user"],
            permissions=["read", "write"]
        )

    # Production mode: validate JWT token
    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization[7:]

        # TODO: Implement proper JWT validation
        # For now, use a placeholder implementation
        if token == "test-token":
            return UserContext(
                user_id="test-user",
                username="test_user",
                email="test@example.com",
                roles=["admin"],
                permissions=["read", "write", "admin"]
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user(
    authorization: Annotated[Optional[str], Header()] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-ID")] = None,
) -> Optional[UserContext]:
    """
    Dependency that optionally extracts the current user.

    Returns None if no authentication is provided instead of raising an exception.
    """
    if not authorization and not x_user_id:
        return None

    try:
        return await get_current_user(authorization, x_user_id)
    except HTTPException:
        return None


def require_permission(permission: str):
    """
    Dependency factory that requires a specific permission.

    Args:
        permission: Required permission string

    Returns:
        Dependency function that validates the permission
    """
    async def permission_checker(
        user: Annotated[UserContext, Depends(get_current_user)]
    ) -> UserContext:
        if permission not in user.permissions and "admin" not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return user

    return permission_checker


def require_role(role: str):
    """
    Dependency factory that requires a specific role.

    Args:
        role: Required role string

    Returns:
        Dependency function that validates the role
    """
    async def role_checker(
        user: Annotated[UserContext, Depends(get_current_user)]
    ) -> UserContext:
        if role not in user.roles and "admin" not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return user

    return role_checker


# Type aliases for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[UserContext, Depends(get_current_user)]
OptionalUser = Annotated[Optional[UserContext], Depends(get_optional_user)]
EventBusDep = Annotated[EventBus, Depends(get_event_bus)]
