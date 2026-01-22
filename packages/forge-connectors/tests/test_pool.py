"""Tests for connection pooling."""

import asyncio
from datetime import timedelta

import pytest

from forge_connectors.core.pool import ConnectionPool, PoolConfig, PoolStats


class MockConnection:
    """Mock connection for testing."""

    def __init__(self, id: int):
        self.id = id
        self.closed = False

    async def close(self):
        self.closed = True


class MockPool(ConnectionPool[MockConnection]):
    """Mock pool implementation for testing."""

    def __init__(self, config: PoolConfig):
        super().__init__(config)
        self._connection_counter = 0

    async def _create_connection(self) -> MockConnection:
        self._connection_counter += 1
        return MockConnection(self._connection_counter)

    async def _close_connection(self, connection: MockConnection) -> None:
        connection.closed = True

    async def _validate_connection(self, connection: MockConnection) -> bool:
        return not connection.closed


@pytest.fixture
def pool_config():
    """Default pool configuration for tests."""
    return PoolConfig(
        min_connections=2,
        max_connections=5,
        max_idle_time=timedelta(minutes=5),
        health_check_interval=timedelta(seconds=60),
        acquire_timeout=timedelta(seconds=5),
    )


@pytest.mark.asyncio
async def test_pool_initialization(pool_config):
    """Test pool initializes with minimum connections."""
    pool = MockPool(pool_config)
    await pool.initialize()

    try:
        stats = pool.get_stats()
        assert stats.total_connections >= pool_config.min_connections
        assert stats.idle_connections >= pool_config.min_connections
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_pool_acquire_release(pool_config):
    """Test acquiring and releasing connections."""
    pool = MockPool(pool_config)
    await pool.initialize()

    try:
        async with pool.acquire() as conn:
            assert isinstance(conn, MockConnection)
            assert not conn.closed

        stats = pool.get_stats()
        assert stats.total_acquired == 1
        assert stats.total_released == 1
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_pool_reuses_connections(pool_config):
    """Test that pool reuses connections."""
    pool = MockPool(pool_config)
    await pool.initialize()

    try:
        # Get a connection
        async with pool.acquire() as conn1:
            conn1_id = conn1.id

        # Get another connection - should reuse
        async with pool.acquire() as conn2:
            conn2_id = conn2.id

        # Should be the same connection
        assert conn1_id == conn2_id
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_pool_concurrent_access(pool_config):
    """Test concurrent access to pool."""
    pool = MockPool(pool_config)
    await pool.initialize()

    acquired_ids = []

    async def use_connection(delay: float):
        async with pool.acquire() as conn:
            acquired_ids.append(conn.id)
            await asyncio.sleep(delay)

    try:
        # Acquire multiple connections concurrently
        await asyncio.gather(
            use_connection(0.1),
            use_connection(0.1),
            use_connection(0.1),
        )

        stats = pool.get_stats()
        assert stats.total_acquired == 3
        assert stats.total_released == 3
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_pool_max_connections(pool_config):
    """Test that pool respects max connections."""
    pool_config.max_connections = 2
    pool = MockPool(pool_config)
    await pool.initialize()

    connections_held = []

    async def hold_connection():
        async with pool.acquire() as conn:
            connections_held.append(conn)
            await asyncio.sleep(1)

    try:
        # Start two connections that hold
        task1 = asyncio.create_task(hold_connection())
        task2 = asyncio.create_task(hold_connection())

        # Give time for connections to be acquired
        await asyncio.sleep(0.1)

        # Third should timeout
        pool_config.acquire_timeout = timedelta(milliseconds=100)
        with pytest.raises(asyncio.TimeoutError):
            async with pool.acquire():
                pass

        task1.cancel()
        task2.cancel()
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_pool_stats(pool_config):
    """Test pool statistics."""
    pool = MockPool(pool_config)
    await pool.initialize()

    try:
        stats = pool.get_stats()
        assert isinstance(stats, PoolStats)
        assert stats.total_connections >= 0
        assert stats.idle_connections >= 0
        assert stats.active_connections >= 0
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_pool_context_manager(pool_config):
    """Test pool as async context manager."""
    async with MockPool(pool_config) as pool:
        async with pool.acquire() as conn:
            assert isinstance(conn, MockConnection)

    # Pool should be closed after context exit


def test_pool_config_validation():
    """Test pool configuration validation."""
    # Valid config
    config = PoolConfig(min_connections=2, max_connections=10)
    assert config.min_connections == 2
    assert config.max_connections == 10

    # Invalid: min > max
    with pytest.raises(ValueError):
        PoolConfig(min_connections=10, max_connections=5)

    # Invalid: negative min
    with pytest.raises(ValueError):
        PoolConfig(min_connections=-1, max_connections=5)

    # Invalid: zero max
    with pytest.raises(ValueError):
        PoolConfig(min_connections=0, max_connections=0)
