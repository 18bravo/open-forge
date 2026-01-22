"""
Health Check Aggregation

This module provides health check functionality for monitoring service health
across the Open Forge platform.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """
    Health information for a service.

    Attributes:
        name: Service name
        status: Current health status
        message: Human-readable status message
        last_check: Timestamp of the last health check
        details: Additional health details
        response_time_ms: Response time of the last check in milliseconds
    """

    name: str
    status: HealthStatus
    message: str = ""
    last_check: datetime | None = None
    details: dict[str, Any] = field(default_factory=dict)
    response_time_ms: float | None = None


@dataclass
class HealthCheckResult:
    """
    Result of a health check operation.

    Attributes:
        overall_status: Aggregated health status
        services: Health status of individual services
        timestamp: When the check was performed
    """

    overall_status: HealthStatus
    services: dict[str, ServiceHealth]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "status": self.overall_status.value,
            "timestamp": self.timestamp.isoformat(),
            "services": {
                name: {
                    "status": health.status.value,
                    "message": health.message,
                    "last_check": health.last_check.isoformat()
                    if health.last_check
                    else None,
                    "response_time_ms": health.response_time_ms,
                    "details": health.details,
                }
                for name, health in self.services.items()
            },
        }


# Type alias for health check functions
HealthCheckFunc = Callable[[], Awaitable[ServiceHealth]]


@runtime_checkable
class HealthCheck(Protocol):
    """
    Protocol for health check implementations.

    Health checks verify that services are functioning correctly.
    """

    async def check(self) -> ServiceHealth:
        """
        Perform a health check.

        Returns:
            ServiceHealth with the current status
        """
        ...


class HealthCheckRegistry:
    """
    Registry for health checks.

    Manages health checks for multiple services and provides aggregated
    health status.

    Example usage:
        >>> registry = HealthCheckRegistry()
        >>>
        >>> @registry.register("database")
        >>> async def check_database() -> ServiceHealth:
        ...     # Check database connectivity
        ...     return ServiceHealth(name="database", status=HealthStatus.HEALTHY)
        >>>
        >>> result = await registry.check_all()
    """

    def __init__(
        self,
        check_timeout: timedelta = timedelta(seconds=5),
        cache_ttl: timedelta = timedelta(seconds=10),
    ) -> None:
        """
        Initialize the health check registry.

        Args:
            check_timeout: Timeout for individual health checks
            cache_ttl: How long to cache health check results
        """
        self.check_timeout = check_timeout
        self.cache_ttl = cache_ttl
        self._checks: dict[str, HealthCheckFunc] = {}
        self._cache: dict[str, tuple[ServiceHealth, datetime]] = {}

    def register(
        self,
        name: str,
        critical: bool = True,
    ) -> Callable[[HealthCheckFunc], HealthCheckFunc]:
        """
        Decorator to register a health check.

        Args:
            name: Service name
            critical: Whether this service is critical (affects overall status)

        Returns:
            Decorator function
        """

        def decorator(func: HealthCheckFunc) -> HealthCheckFunc:
            self._checks[name] = func
            return func

        return decorator

    def add_check(
        self,
        name: str,
        check: HealthCheckFunc,
    ) -> None:
        """
        Add a health check programmatically.

        Args:
            name: Service name
            check: Health check function
        """
        self._checks[name] = check

    def remove_check(self, name: str) -> None:
        """
        Remove a health check.

        Args:
            name: Service name to remove
        """
        self._checks.pop(name, None)
        self._cache.pop(name, None)

    async def check(self, name: str, use_cache: bool = True) -> ServiceHealth:
        """
        Check health of a specific service.

        Args:
            name: Service name
            use_cache: Whether to use cached results

        Returns:
            ServiceHealth for the service
        """
        if name not in self._checks:
            return ServiceHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"No health check registered for '{name}'",
            )

        # Check cache
        if use_cache and name in self._cache:
            cached, cached_at = self._cache[name]
            if datetime.utcnow() - cached_at < self.cache_ttl:
                return cached

        # Perform check
        check_func = self._checks[name]
        start_time = datetime.utcnow()

        try:
            result = await asyncio.wait_for(
                check_func(),
                timeout=self.check_timeout.total_seconds(),
            )
            result.last_check = datetime.utcnow()
            result.response_time_ms = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000

        except asyncio.TimeoutError:
            result = ServiceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.check_timeout.total_seconds()}s",
                last_check=datetime.utcnow(),
            )
        except Exception as e:
            result = ServiceHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {e}",
                last_check=datetime.utcnow(),
            )
            logger.exception(f"Health check failed for '{name}'")

        # Update cache
        self._cache[name] = (result, datetime.utcnow())

        return result

    async def check_all(self, use_cache: bool = True) -> HealthCheckResult:
        """
        Check health of all registered services.

        Args:
            use_cache: Whether to use cached results

        Returns:
            HealthCheckResult with aggregated status
        """
        # Run all checks concurrently
        results = await asyncio.gather(
            *(self.check(name, use_cache) for name in self._checks),
            return_exceptions=True,
        )

        services: dict[str, ServiceHealth] = {}
        for name, result in zip(self._checks.keys(), results):
            if isinstance(result, Exception):
                services[name] = ServiceHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(result),
                )
            else:
                services[name] = result

        # Determine overall status
        overall_status = self._aggregate_status(list(services.values()))

        return HealthCheckResult(
            overall_status=overall_status,
            services=services,
        )

    def _aggregate_status(self, services: list[ServiceHealth]) -> HealthStatus:
        """Aggregate service health into overall status."""
        if not services:
            return HealthStatus.UNKNOWN

        statuses = [s.status for s in services]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY

        if any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED

        return HealthStatus.UNKNOWN

    def clear_cache(self) -> None:
        """Clear the health check cache."""
        self._cache.clear()

    @property
    def registered_checks(self) -> list[str]:
        """Get list of registered health check names."""
        return list(self._checks.keys())
