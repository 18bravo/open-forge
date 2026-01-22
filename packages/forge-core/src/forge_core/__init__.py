"""
Open Forge Core - Centralized Infrastructure Package

This package provides foundational infrastructure for the Open Forge platform:

- **auth**: OAuth2/OIDC authentication, RBAC, row-level security, session management
- **events**: Event bus abstraction with Redis and PostgreSQL backends
- **storage**: Storage abstraction for S3/MinIO/Azure/local filesystems
- **gateway**: Rate limiting, circuit breaker, request routing, health checks
- **config**: Centralized configuration management

All other forge packages depend on forge-core for common infrastructure needs.
"""

from forge_core.auth import (
    AuthProvider,
    Permission,
    Role,
    RowLevelPolicy,
    User,
)
from forge_core.config import Settings, get_settings
from forge_core.events import Event, EventBus, EventHandler, Subscription
from forge_core.gateway import CircuitBreaker, HealthCheck, RateLimiter
from forge_core.storage import StorageBackend

__version__ = "0.1.0"

__all__ = [
    # Auth
    "AuthProvider",
    "User",
    "Role",
    "Permission",
    "RowLevelPolicy",
    # Events
    "EventBus",
    "Event",
    "EventHandler",
    "Subscription",
    # Storage
    "StorageBackend",
    # Gateway
    "RateLimiter",
    "CircuitBreaker",
    "HealthCheck",
    # Config
    "Settings",
    "get_settings",
]
