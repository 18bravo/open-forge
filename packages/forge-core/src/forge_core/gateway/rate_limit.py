"""
Rate Limiting

This module provides rate limiting functionality to protect APIs from abuse
and ensure fair resource usage.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol, runtime_checkable


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""

    FIXED_WINDOW = "fixed_window"  # Fixed time windows
    SLIDING_WINDOW = "sliding_window"  # Sliding window with interpolation
    TOKEN_BUCKET = "token_bucket"  # Token bucket algorithm
    LEAKY_BUCKET = "leaky_bucket"  # Leaky bucket algorithm


@dataclass
class RateLimitConfig:
    """
    Configuration for rate limiting.

    Attributes:
        requests: Maximum number of requests allowed
        window: Time window for the limit
        strategy: Rate limiting strategy to use
        key_prefix: Prefix for rate limit keys (useful for multi-tenant)
        burst_multiplier: Multiplier for burst allowance (token bucket only)
    """

    requests: int
    window: timedelta
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    key_prefix: str = "ratelimit"
    burst_multiplier: float = 1.5


@dataclass
class RateLimitResult:
    """
    Result of a rate limit check.

    Attributes:
        allowed: Whether the request is allowed
        remaining: Remaining requests in the current window
        reset_at: When the rate limit resets
        retry_after: Seconds until the request can be retried (if not allowed)
    """

    allowed: bool
    remaining: int
    reset_at: datetime
    retry_after: int = 0


class RateLimitExceeded(Exception):
    """Raised when a rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 0,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


@runtime_checkable
class RateLimiter(Protocol):
    """
    Protocol for rate limiter implementations.

    Rate limiters track request counts and determine whether additional
    requests should be allowed based on configured limits.

    Example usage:
        >>> limiter = RedisRateLimiter(config)
        >>> result = await limiter.check("user:123")
        >>> if not result.allowed:
        ...     raise RateLimitExceeded(retry_after=result.retry_after)
    """

    async def check(self, key: str) -> RateLimitResult:
        """
        Check if a request is allowed under the rate limit.

        Args:
            key: Identifier for the rate limit (e.g., user ID, IP address)

        Returns:
            RateLimitResult indicating whether the request is allowed
        """
        ...

    async def increment(self, key: str, count: int = 1) -> RateLimitResult:
        """
        Increment the request count and check the limit.

        This combines the check and increment operations atomically.

        Args:
            key: Identifier for the rate limit
            count: Number of requests to add

        Returns:
            RateLimitResult after incrementing
        """
        ...

    async def reset(self, key: str) -> None:
        """
        Reset the rate limit for a key.

        Args:
            key: Identifier for the rate limit to reset
        """
        ...

    async def get_remaining(self, key: str) -> int:
        """
        Get the remaining request count for a key.

        Args:
            key: Identifier for the rate limit

        Returns:
            Number of remaining requests
        """
        ...


class BaseRateLimiter(ABC):
    """
    Abstract base class for rate limiters.

    Provides common functionality for rate limiting implementations.
    """

    def __init__(self, config: RateLimitConfig) -> None:
        """Initialize the rate limiter with configuration."""
        self.config = config

    @abstractmethod
    async def check(self, key: str) -> RateLimitResult:
        """Check if a request is allowed."""
        ...

    @abstractmethod
    async def increment(self, key: str, count: int = 1) -> RateLimitResult:
        """Increment and check the rate limit."""
        ...

    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset a rate limit."""
        ...

    @abstractmethod
    async def get_remaining(self, key: str) -> int:
        """Get remaining requests."""
        ...

    def _get_full_key(self, key: str) -> str:
        """Get the full key with prefix."""
        return f"{self.config.key_prefix}:{key}"


class InMemoryRateLimiter(BaseRateLimiter):
    """
    In-memory rate limiter for development and testing.

    Uses a simple fixed window algorithm with in-memory storage.
    Not suitable for distributed deployments.
    """

    def __init__(self, config: RateLimitConfig) -> None:
        """Initialize the in-memory rate limiter."""
        super().__init__(config)
        self._counters: dict[str, tuple[int, datetime]] = {}

    async def check(self, key: str) -> RateLimitResult:
        """Check the rate limit without incrementing."""
        full_key = self._get_full_key(key)
        now = datetime.utcnow()

        if full_key in self._counters:
            count, window_start = self._counters[full_key]
            window_end = window_start + self.config.window

            if now < window_end:
                remaining = max(0, self.config.requests - count)
                allowed = count < self.config.requests
                retry_after = int((window_end - now).total_seconds()) if not allowed else 0

                return RateLimitResult(
                    allowed=allowed,
                    remaining=remaining,
                    reset_at=window_end,
                    retry_after=retry_after,
                )

        # New window
        reset_at = now + self.config.window
        return RateLimitResult(
            allowed=True,
            remaining=self.config.requests,
            reset_at=reset_at,
        )

    async def increment(self, key: str, count: int = 1) -> RateLimitResult:
        """Increment and check the rate limit."""
        full_key = self._get_full_key(key)
        now = datetime.utcnow()

        if full_key in self._counters:
            current_count, window_start = self._counters[full_key]
            window_end = window_start + self.config.window

            if now < window_end:
                # Within current window
                new_count = current_count + count
                self._counters[full_key] = (new_count, window_start)

                remaining = max(0, self.config.requests - new_count)
                allowed = new_count <= self.config.requests
                retry_after = int((window_end - now).total_seconds()) if not allowed else 0

                return RateLimitResult(
                    allowed=allowed,
                    remaining=remaining,
                    reset_at=window_end,
                    retry_after=retry_after,
                )

        # Start new window
        self._counters[full_key] = (count, now)
        reset_at = now + self.config.window

        return RateLimitResult(
            allowed=True,
            remaining=self.config.requests - count,
            reset_at=reset_at,
        )

    async def reset(self, key: str) -> None:
        """Reset the rate limit for a key."""
        full_key = self._get_full_key(key)
        self._counters.pop(full_key, None)

    async def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        result = await self.check(key)
        return result.remaining

    def clear(self) -> None:
        """Clear all rate limits (useful for testing)."""
        self._counters.clear()
