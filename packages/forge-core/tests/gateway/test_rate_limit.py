"""Tests for rate limiting."""

from datetime import timedelta

import pytest

from forge_core.gateway.rate_limit import (
    InMemoryRateLimiter,
    RateLimitConfig,
)


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter."""

    @pytest.fixture
    def limiter(self) -> InMemoryRateLimiter:
        """Create a rate limiter for testing."""
        config = RateLimitConfig(
            requests=5,
            window=timedelta(seconds=60),
        )
        return InMemoryRateLimiter(config)

    @pytest.mark.asyncio
    async def test_allows_within_limit(self, limiter: InMemoryRateLimiter) -> None:
        """Test that requests within limit are allowed."""
        for _ in range(5):
            result = await limiter.increment("test-key")
            assert result.allowed

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self, limiter: InMemoryRateLimiter) -> None:
        """Test that requests over limit are blocked."""
        for _ in range(5):
            await limiter.increment("test-key")

        result = await limiter.increment("test-key")
        assert not result.allowed
        assert result.retry_after > 0

    @pytest.mark.asyncio
    async def test_remaining_count(self, limiter: InMemoryRateLimiter) -> None:
        """Test remaining request count."""
        await limiter.increment("test-key", count=3)

        remaining = await limiter.get_remaining("test-key")
        assert remaining == 2

    @pytest.mark.asyncio
    async def test_reset(self, limiter: InMemoryRateLimiter) -> None:
        """Test resetting a rate limit."""
        await limiter.increment("test-key", count=5)
        result = await limiter.check("test-key")
        assert not result.allowed

        await limiter.reset("test-key")

        result = await limiter.check("test-key")
        assert result.allowed
        assert result.remaining == 5

    @pytest.mark.asyncio
    async def test_separate_keys(self, limiter: InMemoryRateLimiter) -> None:
        """Test that different keys have separate limits."""
        await limiter.increment("key-a", count=5)
        await limiter.increment("key-b", count=2)

        result_a = await limiter.check("key-a")
        result_b = await limiter.check("key-b")

        assert not result_a.allowed
        assert result_b.allowed
        assert result_b.remaining == 3

    @pytest.mark.asyncio
    async def test_check_without_increment(self, limiter: InMemoryRateLimiter) -> None:
        """Test checking limit without incrementing."""
        await limiter.increment("test-key", count=3)

        result = await limiter.check("test-key")
        assert result.allowed
        assert result.remaining == 2

        # Check again - should be same
        result = await limiter.check("test-key")
        assert result.allowed
        assert result.remaining == 2

    @pytest.mark.asyncio
    async def test_clear(self, limiter: InMemoryRateLimiter) -> None:
        """Test clearing all rate limits."""
        await limiter.increment("key-a", count=5)
        await limiter.increment("key-b", count=5)

        limiter.clear()

        result_a = await limiter.check("key-a")
        result_b = await limiter.check("key-b")

        assert result_a.allowed
        assert result_a.remaining == 5
        assert result_b.allowed
        assert result_b.remaining == 5
