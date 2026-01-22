"""
Request Routing

This module provides request routing functionality for directing requests
to appropriate backend services.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol, runtime_checkable


class RouteMatchType(str, Enum):
    """Types of route matching."""

    EXACT = "exact"  # Exact path match
    PREFIX = "prefix"  # Path prefix match
    REGEX = "regex"  # Regular expression match


class LoadBalanceStrategy(str, Enum):
    """Load balancing strategies."""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"


@dataclass
class RouteConfig:
    """
    Configuration for a route.

    Attributes:
        path: Path pattern to match
        match_type: Type of path matching
        service: Target service name
        methods: Allowed HTTP methods (empty = all)
        strip_prefix: Whether to strip the matched prefix from the path
        timeout: Request timeout in seconds
        retries: Number of retry attempts
        headers: Headers to add/override
        rate_limit_key: Key for rate limiting (e.g., "user", "ip")
    """

    path: str
    service: str
    match_type: RouteMatchType = RouteMatchType.PREFIX
    methods: set[str] = field(default_factory=set)
    strip_prefix: bool = False
    timeout: float = 30.0
    retries: int = 0
    headers: dict[str, str] = field(default_factory=dict)
    rate_limit_key: str | None = None


@dataclass
class Route:
    """
    A configured route with compiled patterns.

    Attributes:
        config: Route configuration
        priority: Route priority (higher = matched first)
        regex: Compiled regex pattern (for regex match type)
    """

    config: RouteConfig
    priority: int = 0
    _regex: re.Pattern | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Compile regex pattern if needed."""
        if self.config.match_type == RouteMatchType.REGEX:
            self._regex = re.compile(self.config.path)

    def matches(self, path: str, method: str = "GET") -> bool:
        """
        Check if this route matches the given path and method.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            True if the route matches
        """
        # Check method
        if self.config.methods and method.upper() not in self.config.methods:
            return False

        # Check path
        if self.config.match_type == RouteMatchType.EXACT:
            return path == self.config.path

        elif self.config.match_type == RouteMatchType.PREFIX:
            return path.startswith(self.config.path)

        elif self.config.match_type == RouteMatchType.REGEX and self._regex:
            return bool(self._regex.match(path))

        return False

    def transform_path(self, path: str) -> str:
        """
        Transform the path according to route configuration.

        Args:
            path: Original request path

        Returns:
            Transformed path
        """
        if self.config.strip_prefix and self.config.match_type == RouteMatchType.PREFIX:
            return path[len(self.config.path) :] or "/"
        return path


@dataclass
class ServiceEndpoint:
    """
    A service endpoint for routing.

    Attributes:
        url: Base URL of the service
        weight: Weight for weighted load balancing
        healthy: Whether the endpoint is healthy
        connections: Current connection count
    """

    url: str
    weight: int = 1
    healthy: bool = True
    connections: int = 0


@runtime_checkable
class RequestRouter(Protocol):
    """
    Protocol for request routing.

    Routes incoming requests to appropriate backend services based on
    path patterns, methods, and other criteria.
    """

    def add_route(self, route: Route) -> None:
        """
        Add a route to the router.

        Args:
            route: Route to add
        """
        ...

    def remove_route(self, path: str) -> None:
        """
        Remove a route by path.

        Args:
            path: Path of the route to remove
        """
        ...

    def match(self, path: str, method: str = "GET") -> Route | None:
        """
        Find a matching route for a request.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            Matching route or None
        """
        ...

    def get_endpoint(self, service: str) -> ServiceEndpoint | None:
        """
        Get an endpoint for a service using load balancing.

        Args:
            service: Service name

        Returns:
            Selected endpoint or None
        """
        ...


class DefaultRequestRouter:
    """
    Default implementation of request routing.

    Supports:
    - Multiple match types (exact, prefix, regex)
    - Priority-based route matching
    - Load balancing across service endpoints
    """

    def __init__(
        self,
        load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN,
    ) -> None:
        """
        Initialize the request router.

        Args:
            load_balance_strategy: Strategy for load balancing
        """
        self.load_balance_strategy = load_balance_strategy
        self._routes: list[Route] = []
        self._services: dict[str, list[ServiceEndpoint]] = {}
        self._round_robin_counters: dict[str, int] = {}

    def add_route(self, route: Route) -> None:
        """Add a route to the router."""
        self._routes.append(route)
        # Sort by priority (descending) then by path length (descending)
        self._routes.sort(
            key=lambda r: (-r.priority, -len(r.config.path)),
        )

    def remove_route(self, path: str) -> None:
        """Remove a route by path."""
        self._routes = [r for r in self._routes if r.config.path != path]

    def add_service_endpoint(self, service: str, endpoint: ServiceEndpoint) -> None:
        """
        Add an endpoint for a service.

        Args:
            service: Service name
            endpoint: Service endpoint
        """
        if service not in self._services:
            self._services[service] = []
        self._services[service].append(endpoint)

    def remove_service_endpoint(self, service: str, url: str) -> None:
        """
        Remove an endpoint from a service.

        Args:
            service: Service name
            url: Endpoint URL to remove
        """
        if service in self._services:
            self._services[service] = [
                e for e in self._services[service] if e.url != url
            ]

    def match(self, path: str, method: str = "GET") -> Route | None:
        """Find a matching route for a request."""
        for route in self._routes:
            if route.matches(path, method):
                return route
        return None

    def get_endpoint(self, service: str) -> ServiceEndpoint | None:
        """Get an endpoint for a service using load balancing."""
        endpoints = self._services.get(service, [])
        healthy = [e for e in endpoints if e.healthy]

        if not healthy:
            return None

        if self.load_balance_strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_select(service, healthy)
        elif self.load_balance_strategy == LoadBalanceStrategy.RANDOM:
            import random

            return random.choice(healthy)
        elif self.load_balance_strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return min(healthy, key=lambda e: e.connections)
        elif self.load_balance_strategy == LoadBalanceStrategy.WEIGHTED:
            return self._weighted_select(healthy)

        return healthy[0] if healthy else None

    def _round_robin_select(
        self,
        service: str,
        endpoints: list[ServiceEndpoint],
    ) -> ServiceEndpoint:
        """Select an endpoint using round-robin."""
        counter = self._round_robin_counters.get(service, 0)
        endpoint = endpoints[counter % len(endpoints)]
        self._round_robin_counters[service] = counter + 1
        return endpoint

    def _weighted_select(
        self,
        endpoints: list[ServiceEndpoint],
    ) -> ServiceEndpoint:
        """Select an endpoint using weighted selection."""
        import random

        total_weight = sum(e.weight for e in endpoints)
        r = random.uniform(0, total_weight)
        cumulative = 0

        for endpoint in endpoints:
            cumulative += endpoint.weight
            if r <= cumulative:
                return endpoint

        return endpoints[-1]

    @property
    def routes(self) -> list[Route]:
        """Get all configured routes."""
        return list(self._routes)

    @property
    def services(self) -> dict[str, list[ServiceEndpoint]]:
        """Get all configured services and endpoints."""
        return dict(self._services)
