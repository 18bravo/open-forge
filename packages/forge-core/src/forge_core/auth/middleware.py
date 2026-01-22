"""
FastAPI Authentication Middleware

This module provides FastAPI middleware and dependency injection for authentication.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

if TYPE_CHECKING:
    from forge_core.auth.provider import AuthProvider
    from forge_core.auth.user import User

# Security scheme for OpenAPI documentation
bearer_scheme = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """
    FastAPI middleware for authentication.

    This middleware:
    1. Extracts the bearer token from the Authorization header
    2. Validates the token with the configured auth provider
    3. Attaches the authenticated user to the request state

    Example usage:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> auth_middleware = AuthMiddleware(auth_provider)
        >>> app.add_middleware(auth_middleware)

    Or as a dependency:
        >>> @app.get("/protected")
        >>> async def protected_route(user: User = Depends(get_current_user)):
        ...     return {"user": user.email}
    """

    def __init__(
        self,
        auth_provider: "AuthProvider",
        exclude_paths: list[str] | None = None,
    ) -> None:
        """
        Initialize the authentication middleware.

        Args:
            auth_provider: Provider for token validation
            exclude_paths: Paths to exclude from authentication (e.g., health checks)
        """
        self.auth_provider = auth_provider
        self.exclude_paths = set(exclude_paths or [])

    async def __call__(
        self,
        request: Request,
        call_next: Callable,
    ):
        """Process the request through the middleware."""
        # Skip authentication for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Extract token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return await call_next(request)

        if not auth_header.startswith("Bearer "):
            return await call_next(request)

        token = auth_header.removeprefix("Bearer ")

        try:
            # Authenticate and attach user to request
            user = await self.auth_provider.authenticate(token)
            request.state.user = user
        except Exception:
            # Let the request continue without user for optional auth
            # Required auth is enforced by the get_current_user dependency
            pass

        return await call_next(request)


class AuthenticationError(HTTPException):
    """Exception raised when authentication fails."""

    def __init__(self, detail: str = "Could not validate credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Exception raised when authorization fails."""

    def __init__(self, detail: str = "Not authorized to access this resource") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


# Global auth provider reference for dependency injection
_auth_provider: "AuthProvider | None" = None


def configure_auth(provider: "AuthProvider") -> None:
    """
    Configure the global auth provider.

    This should be called during application startup.

    Args:
        provider: Auth provider instance to use
    """
    global _auth_provider
    _auth_provider = provider


def get_auth_provider() -> "AuthProvider":
    """Get the configured auth provider."""
    if _auth_provider is None:
        raise RuntimeError("Auth provider not configured. Call configure_auth() first.")
    return _auth_provider


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    request: Request,
) -> "User":
    """
    FastAPI dependency that returns the current authenticated user.

    This dependency can be used in route handlers to require authentication.

    Example:
        >>> @app.get("/me")
        >>> async def get_me(user: User = Depends(get_current_user)):
        ...     return {"email": user.email}

    Raises:
        AuthenticationError: If no valid token is provided
    """
    # Check if user was already authenticated by middleware
    if hasattr(request.state, "user") and request.state.user is not None:
        return request.state.user

    # Try to authenticate from credentials
    if credentials is None:
        raise AuthenticationError()

    provider = get_auth_provider()

    try:
        user = await provider.authenticate(credentials.credentials)
        return user
    except Exception as e:
        raise AuthenticationError(str(e))


async def get_current_user_optional(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    request: Request,
) -> "User | None":
    """
    FastAPI dependency that returns the current user if authenticated, None otherwise.

    Use this for routes that support both authenticated and anonymous access.

    Example:
        >>> @app.get("/data")
        >>> async def get_data(user: User | None = Depends(get_current_user_optional)):
        ...     if user:
        ...         return get_user_data(user)
        ...     return get_public_data()
    """
    # Check if user was already authenticated by middleware
    if hasattr(request.state, "user") and request.state.user is not None:
        return request.state.user

    if credentials is None:
        return None

    provider = get_auth_provider()

    try:
        return await provider.authenticate(credentials.credentials)
    except Exception:
        return None


def require_permission(permission: str) -> Callable:
    """
    Create a dependency that requires a specific permission.

    Example:
        >>> @app.delete("/datasets/{id}")
        >>> async def delete_dataset(
        ...     id: str,
        ...     user: User = Depends(require_permission("dataset:delete")),
        ... ):
        ...     ...
    """

    async def check_permission(
        user: Annotated["User", Depends(get_current_user)],
    ) -> "User":
        if not user.has_permission(permission):
            raise AuthorizationError(f"Missing permission: {permission}")
        return user

    return check_permission


def require_role(*roles: str) -> Callable:
    """
    Create a dependency that requires one of the specified roles.

    Example:
        >>> @app.post("/admin/users")
        >>> async def create_user(
        ...     user: User = Depends(require_role("admin", "super_admin")),
        ... ):
        ...     ...
    """

    async def check_role(
        user: Annotated["User", Depends(get_current_user)],
    ) -> "User":
        if not user.has_any_role(*roles):
            raise AuthorizationError(f"Requires one of roles: {', '.join(roles)}")
        return user

    return check_role
