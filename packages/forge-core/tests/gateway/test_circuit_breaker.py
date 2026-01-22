"""Tests for circuit breaker."""

from datetime import timedelta

import pytest

from forge_core.gateway.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    DefaultCircuitBreaker,
)


class TestDefaultCircuitBreaker:
    """Tests for DefaultCircuitBreaker."""

    @pytest.fixture
    def circuit(self) -> DefaultCircuitBreaker:
        """Create a circuit breaker for testing."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=timedelta(seconds=1),
        )
        return DefaultCircuitBreaker("test-circuit", config)

    def test_initial_state_closed(self, circuit: DefaultCircuitBreaker) -> None:
        """Test that circuit starts in closed state."""
        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_successful_calls(self, circuit: DefaultCircuitBreaker) -> None:
        """Test successful calls pass through."""

        async def success() -> str:
            return "success"

        result = await circuit.call(success)
        assert result == "success"
        assert circuit.state == CircuitState.CLOSED
        assert circuit.stats.successful_calls == 1

    @pytest.mark.asyncio
    async def test_opens_on_failures(self, circuit: DefaultCircuitBreaker) -> None:
        """Test circuit opens after threshold failures."""

        async def fail() -> None:
            raise ValueError("Failure")

        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit.call(fail)

        assert circuit.state == CircuitState.OPEN
        assert circuit.stats.failed_calls == 3

    @pytest.mark.asyncio
    async def test_rejects_when_open(self, circuit: DefaultCircuitBreaker) -> None:
        """Test requests are rejected when circuit is open."""

        async def fail() -> None:
            raise ValueError("Failure")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit.call(fail)

        # Should reject new calls
        with pytest.raises(CircuitOpenError):
            await circuit.call(fail)

        assert circuit.stats.rejected_calls == 1

    @pytest.mark.asyncio
    async def test_reset(self, circuit: DefaultCircuitBreaker) -> None:
        """Test resetting the circuit."""

        async def fail() -> None:
            raise ValueError("Failure")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit.call(fail)

        assert circuit.state == CircuitState.OPEN

        circuit.reset()

        assert circuit.state == CircuitState.CLOSED

    def test_record_success_resets_failure_count(
        self, circuit: DefaultCircuitBreaker
    ) -> None:
        """Test that success resets failure count."""
        circuit._failure_count = 2
        circuit.record_success()

        assert circuit._failure_count == 0

    def test_stats(self, circuit: DefaultCircuitBreaker) -> None:
        """Test circuit breaker statistics."""
        circuit._total_calls = 10
        circuit._successful_calls = 7
        circuit._failed_calls = 3

        stats = circuit.stats

        assert stats.total_calls == 10
        assert stats.successful_calls == 7
        assert stats.failed_calls == 3
        assert stats.state == CircuitState.CLOSED
