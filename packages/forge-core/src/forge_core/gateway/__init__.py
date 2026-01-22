"""
API Gateway Module

This module provides API gateway functionality for the Open Forge platform:

- **rate_limit**: Rate limiting for API endpoints
- **circuit_breaker**: Circuit breaker pattern for fault tolerance
- **routing**: Request routing and load balancing
- **health**: Health check aggregation across services

These components help ensure reliability and fair resource usage across the platform.
"""

from forge_core.gateway.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)
from forge_core.gateway.health import (
    HealthCheck,
    HealthCheckRegistry,
    HealthStatus,
    ServiceHealth,
)
from forge_core.gateway.rate_limit import (
    RateLimitConfig,
    RateLimiter,
    RateLimitExceeded,
)
from forge_core.gateway.routing import RequestRouter, Route, RouteConfig

__all__ = [
    # Rate limiting
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitExceeded",
    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    # Health checks
    "HealthCheck",
    "HealthCheckRegistry",
    "HealthStatus",
    "ServiceHealth",
    # Routing
    "RequestRouter",
    "Route",
    "RouteConfig",
]
