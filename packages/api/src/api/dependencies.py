"""
FastAPI dependencies for dependency injection.

This module integrates forge-core authentication, events, and other services
into the FastAPI application via dependency injection.
"""

from typing import Annotated, AsyncGenerator, Optional

from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from core.database.connection import AsyncSessionLocal

# Import forge-core auth components
from forge_core.auth import (
    AuthProvider,
    AuthProviderConfig,
    AuthProviderType,
    JWTAuthProvider,
    JWTConfig,
    User,
    configure_auth,
    get_current_user as forge_get_current_user,
    get_current_user_optional as forge_get_current_user_optional,
    require_permission as forge_require_permission,
    require_role as forge_require_role,
)

# Import forge-core events
from forge_core.events.backends.memory import InMemoryEventBus
from forge_core.events.bus import Event

# Import forge-core storage
from forge_core.storage import StorageBackend, StorageConfig, StorageError
from forge_core.storage.abstraction import StorageProvider
from forge_core.storage.backends.local import LocalStorageBackend

# Import forge-core gateway (rate limiting, circuit breaker, health)
from forge_core.gateway import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    HealthCheck,
    HealthCheckRegistry,
    HealthStatus,
    RateLimitConfig,
    RateLimiter,
    RateLimitExceeded,
)
from forge_core.gateway.rate_limit import InMemoryRateLimiter
from forge_core.gateway.circuit_breaker import DefaultCircuitBreaker


# -----------------------------------------------------------------------------
# Auth Provider Configuration
# -----------------------------------------------------------------------------

# Global auth provider instance
_auth_provider: Optional[AuthProvider] = None


async def init_auth_provider() -> AuthProvider:
    """
    Initialize the authentication provider.

    Call this during application startup.

    Returns:
        Configured auth provider instance
    """
    global _auth_provider

    if _auth_provider is None:
        # Configure JWT-based auth provider
        auth_config = AuthProviderConfig(
            provider_type=AuthProviderType.INTERNAL,
            issuer="open-forge",
            client_id="api",
        )
        jwt_config = JWTConfig()  # Uses environment variables
        _auth_provider = JWTAuthProvider(auth_config, jwt_config)

        # Register with forge-core middleware
        configure_auth(_auth_provider)

    return _auth_provider


async def close_auth_provider() -> None:
    """Clean up auth provider on shutdown."""
    global _auth_provider
    _auth_provider = None


def get_auth_provider_instance() -> AuthProvider:
    """Get the configured auth provider."""
    if _auth_provider is None:
        raise RuntimeError("Auth provider not initialized. Call init_auth_provider() first.")
    return _auth_provider


# -----------------------------------------------------------------------------
# Database Session
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Event Bus
# -----------------------------------------------------------------------------

# Global event bus instance
_event_bus: Optional[InMemoryEventBus] = None


async def init_event_bus() -> InMemoryEventBus:
    """
    Initialize the global event bus instance.

    Uses forge-core's InMemoryEventBus for local development.
    In production, this should be replaced with Redis or PostgreSQL backend.
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = InMemoryEventBus(source="open-forge-api")
        await _event_bus.connect()
    return _event_bus


async def close_event_bus() -> None:
    """Close the global event bus connection."""
    global _event_bus
    if _event_bus is not None:
        await _event_bus.disconnect()
        _event_bus = None


def get_event_bus() -> InMemoryEventBus:
    """
    Dependency that provides the event bus instance.

    Raises:
        RuntimeError: If event bus is not initialized.
    """
    if _event_bus is None:
        raise RuntimeError("EventBus not initialized. Call init_event_bus() first.")
    return _event_bus


# -----------------------------------------------------------------------------
# Storage
# -----------------------------------------------------------------------------

# Global storage backend instance
_storage_backend: Optional[StorageBackend] = None


async def init_storage(storage_path: Optional[str] = None) -> StorageBackend:
    """
    Initialize the global storage backend.

    Uses forge-core's LocalStorageBackend for development.
    In production, this should be replaced with S3 or Azure backend.

    Args:
        storage_path: Optional path for local storage. Defaults to ./data/storage

    Returns:
        Configured storage backend
    """
    import os
    global _storage_backend

    if _storage_backend is None:
        # Use local storage for development, S3/Azure in production
        path = storage_path or os.environ.get("STORAGE_PATH", "./data/storage")

        config = StorageConfig(
            provider=StorageProvider.LOCAL,
            bucket=path,
        )
        _storage_backend = LocalStorageBackend(config)
        await _storage_backend.connect()

    return _storage_backend


async def close_storage() -> None:
    """Close the storage backend connection."""
    global _storage_backend
    if _storage_backend is not None:
        await _storage_backend.disconnect()
        _storage_backend = None


def get_storage() -> StorageBackend:
    """
    Dependency that provides the storage backend instance.

    Raises:
        RuntimeError: If storage is not initialized.
    """
    if _storage_backend is None:
        raise RuntimeError("Storage not initialized. Call init_storage() first.")
    return _storage_backend


# -----------------------------------------------------------------------------
# Rate Limiting
# -----------------------------------------------------------------------------

# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


async def init_rate_limiter(
    requests_per_minute: int = 100,
) -> RateLimiter:
    """
    Initialize the global rate limiter.

    Uses forge-core's InMemoryRateLimiter for development.
    In production, use Redis-backed rate limiter.

    Args:
        requests_per_minute: Maximum requests per minute per key

    Returns:
        Configured rate limiter
    """
    from datetime import timedelta
    global _rate_limiter

    if _rate_limiter is None:
        config = RateLimitConfig(
            requests=requests_per_minute,
            window=timedelta(minutes=1),
            key_prefix="api",
        )
        _rate_limiter = InMemoryRateLimiter(config)

    return _rate_limiter


def get_rate_limiter() -> RateLimiter:
    """
    Dependency that provides the rate limiter instance.

    Raises:
        RuntimeError: If rate limiter is not initialized.
    """
    if _rate_limiter is None:
        raise RuntimeError("Rate limiter not initialized. Call init_rate_limiter() first.")
    return _rate_limiter


# -----------------------------------------------------------------------------
# Circuit Breaker
# -----------------------------------------------------------------------------

# Global circuit breaker registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout_seconds: int = 60,
) -> CircuitBreaker:
    """
    Get or create a circuit breaker for a service.

    Circuit breakers prevent cascading failures when external services are down.

    Args:
        name: Unique name for the circuit breaker (e.g., "external-api")
        failure_threshold: Number of failures before opening circuit
        recovery_timeout_seconds: Seconds to wait before trying recovery

    Returns:
        Circuit breaker instance
    """
    from datetime import timedelta

    if name not in _circuit_breakers:
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=timedelta(seconds=recovery_timeout_seconds),
        )
        _circuit_breakers[name] = DefaultCircuitBreaker(name, config)

    return _circuit_breakers[name]


# -----------------------------------------------------------------------------
# Health Check Registry
# -----------------------------------------------------------------------------

# Global health check registry
_health_registry: Optional[HealthCheckRegistry] = None


def init_health_registry() -> HealthCheckRegistry:
    """Initialize the health check registry."""
    global _health_registry
    if _health_registry is None:
        _health_registry = HealthCheckRegistry()
    return _health_registry


def get_health_registry() -> HealthCheckRegistry:
    """Get the health check registry."""
    if _health_registry is None:
        raise RuntimeError("Health registry not initialized. Call init_health_registry() first.")
    return _health_registry


# -----------------------------------------------------------------------------
# User Dependencies (wrapping forge-core)
# -----------------------------------------------------------------------------

# Use forge-core's get_current_user directly
get_current_user = forge_get_current_user
get_current_user_optional = forge_get_current_user_optional

# Use forge-core's permission/role checkers
require_permission = forge_require_permission
require_role = forge_require_role


# -----------------------------------------------------------------------------
# Type Aliases for Dependency Injection
# -----------------------------------------------------------------------------

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_current_user_optional)]
EventBusDep = Annotated[InMemoryEventBus, Depends(get_event_bus)]
StorageDep = Annotated[StorageBackend, Depends(get_storage)]
RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]
HealthRegistryDep = Annotated[HealthCheckRegistry, Depends(get_health_registry)]


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

async def publish_event(topic: str, event_type: str, payload: dict) -> None:
    """
    Helper to publish an event to the event bus.

    Args:
        topic: Event topic (e.g., "engagement.created")
        event_type: Type of event (e.g., "created", "updated", "deleted")
        payload: Event payload data
    """
    bus = get_event_bus()
    event = Event(topic=topic, type=event_type, payload=payload)
    await bus.publish(event)
