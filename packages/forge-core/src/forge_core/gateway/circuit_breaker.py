"""
Circuit Breaker

This module implements the circuit breaker pattern for fault tolerance.
It prevents cascading failures by temporarily stopping requests to failing services.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Generic, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """States of the circuit breaker."""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Failure threshold reached, requests are blocked
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """
    Configuration for the circuit breaker.

    Attributes:
        failure_threshold: Number of failures before opening the circuit
        success_threshold: Number of successes in half-open state before closing
        timeout: Time to wait before transitioning from open to half-open
        half_open_max_calls: Maximum concurrent calls in half-open state
        exclude_exceptions: Exception types that don't count as failures
    """

    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: timedelta = timedelta(seconds=30)
    half_open_max_calls: int = 3
    exclude_exceptions: tuple[type[Exception], ...] = ()


@dataclass
class CircuitBreakerStats:
    """
    Statistics for circuit breaker monitoring.

    Attributes:
        total_calls: Total number of calls made
        successful_calls: Number of successful calls
        failed_calls: Number of failed calls
        rejected_calls: Number of calls rejected due to open circuit
        state: Current circuit state
        last_failure_time: Time of the last failure
        last_state_change: Time of the last state change
    """

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: datetime | None = None
    last_state_change: datetime | None = None


class CircuitOpenError(Exception):
    """Raised when the circuit is open and requests are being rejected."""

    def __init__(self, message: str = "Circuit breaker is open") -> None:
        super().__init__(message)


@runtime_checkable
class CircuitBreaker(Protocol):
    """
    Protocol for circuit breaker implementations.

    Circuit breakers prevent cascading failures by monitoring for failures
    and temporarily blocking requests when a threshold is exceeded.

    Example usage:
        >>> circuit = DefaultCircuitBreaker("external-api", config)
        >>>
        >>> try:
        ...     result = await circuit.call(external_api_request)
        ... except CircuitOpenError:
        ...     # Handle circuit open (return cached data, show error, etc.)
        ...     pass
    """

    @property
    def state(self) -> CircuitState:
        """Get the current circuit state."""
        ...

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        ...

    async def call(
        self,
        func: Callable[[], Awaitable[T]],
    ) -> T:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Async function to execute

        Returns:
            Result of the function

        Raises:
            CircuitOpenError: If the circuit is open
            Exception: If the function raises an exception
        """
        ...

    def record_success(self) -> None:
        """Record a successful call."""
        ...

    def record_failure(self, error: Exception) -> None:
        """Record a failed call."""
        ...

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        ...


class DefaultCircuitBreaker:
    """
    Default implementation of the circuit breaker pattern.

    State transitions:
    - CLOSED -> OPEN: When failure_threshold is reached
    - OPEN -> HALF_OPEN: After timeout expires
    - HALF_OPEN -> CLOSED: When success_threshold is reached
    - HALF_OPEN -> OPEN: On any failure
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> None:
        """
        Initialize the circuit breaker.

        Args:
            name: Name for identification and logging
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None
        self._last_state_change = datetime.utcnow()
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

        # Statistics
        self._total_calls = 0
        self._successful_calls = 0
        self._failed_calls = 0
        self._rejected_calls = 0

    @property
    def state(self) -> CircuitState:
        """Get the current circuit state."""
        self._check_state_transition()
        return self._state

    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return CircuitBreakerStats(
            total_calls=self._total_calls,
            successful_calls=self._successful_calls,
            failed_calls=self._failed_calls,
            rejected_calls=self._rejected_calls,
            state=self._state,
            last_failure_time=self._last_failure_time,
            last_state_change=self._last_state_change,
        )

    async def call(
        self,
        func: Callable[[], Awaitable[T]],
    ) -> T:
        """Execute a function through the circuit breaker."""
        async with self._lock:
            self._check_state_transition()

            if self._state == CircuitState.OPEN:
                self._rejected_calls += 1
                raise CircuitOpenError(f"Circuit '{self.name}' is open")

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self._rejected_calls += 1
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is half-open and at max calls"
                    )
                self._half_open_calls += 1

            self._total_calls += 1

        try:
            result = await func()
            self.record_success()
            return result
        except Exception as e:
            if not isinstance(e, self.config.exclude_exceptions):
                self.record_failure(e)
            raise

    def record_success(self) -> None:
        """Record a successful call."""
        self._successful_calls += 1

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            self._half_open_calls = max(0, self._half_open_calls - 1)

            if self._success_count >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        else:
            # Reset failure count on success in closed state
            self._failure_count = 0

    def record_failure(self, error: Exception) -> None:
        """Record a failed call."""
        self._failed_calls += 1
        self._last_failure_time = datetime.utcnow()

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open goes back to open
            self._transition_to(CircuitState.OPEN)
        else:
            self._failure_count += 1

            if self._failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

        logger.warning(
            f"Circuit '{self.name}' recorded failure: {error}. "
            f"State: {self._state}, failures: {self._failure_count}"
        )

    def reset(self) -> None:
        """Reset the circuit breaker."""
        self._transition_to(CircuitState.CLOSED)
        self._failure_count = 0
        self._success_count = 0
        logger.info(f"Circuit '{self.name}' reset to closed state")

    def _check_state_transition(self) -> None:
        """Check if the circuit should transition states."""
        if self._state == CircuitState.OPEN:
            time_since_open = datetime.utcnow() - self._last_state_change
            if time_since_open >= self.config.timeout:
                self._transition_to(CircuitState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._last_state_change = datetime.utcnow()

            if new_state == CircuitState.CLOSED:
                self._failure_count = 0
                self._success_count = 0
            elif new_state == CircuitState.HALF_OPEN:
                self._success_count = 0
                self._half_open_calls = 0

            logger.info(
                f"Circuit '{self.name}' transitioned from {old_state} to {new_state}"
            )
