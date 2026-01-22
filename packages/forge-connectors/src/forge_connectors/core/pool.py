"""
Connection pooling utilities.

Provides configuration and base classes for connection pool management.
Individual connectors implement their own pooling using these abstractions.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Connection type


@dataclass
class PoolConfig:
    """
    Configuration for connection pools.

    Attributes:
        min_connections: Minimum connections to keep in pool.
        max_connections: Maximum connections allowed.
        max_idle_time: Close connections idle longer than this.
        health_check_interval: How often to check connection health.
        acquire_timeout: Max time to wait for a connection.
        max_lifetime: Maximum time a connection can live.
    """

    min_connections: int = 2
    max_connections: int = 20
    max_idle_time: timedelta = field(default_factory=lambda: timedelta(minutes=10))
    health_check_interval: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    acquire_timeout: timedelta = field(default_factory=lambda: timedelta(seconds=5))
    max_lifetime: timedelta = field(default_factory=lambda: timedelta(hours=1))

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.min_connections < 0:
            raise ValueError("min_connections must be >= 0")
        if self.max_connections < 1:
            raise ValueError("max_connections must be >= 1")
        if self.min_connections > self.max_connections:
            raise ValueError("min_connections must be <= max_connections")


@dataclass
class PoolStats:
    """Statistics for a connection pool."""

    total_connections: int = 0
    idle_connections: int = 0
    active_connections: int = 0
    waiting_requests: int = 0
    total_acquired: int = 0
    total_released: int = 0
    total_timeouts: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PooledConnection(Generic[T]):
    """Wrapper for a pooled connection with metadata."""

    connection: T
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: datetime = field(default_factory=datetime.utcnow)
    use_count: int = 0

    def mark_used(self) -> None:
        """Mark connection as used."""
        self.last_used_at = datetime.utcnow()
        self.use_count += 1

    def is_expired(self, max_lifetime: timedelta) -> bool:
        """Check if connection has exceeded its lifetime."""
        return datetime.utcnow() - self.created_at > max_lifetime

    def is_stale(self, max_idle_time: timedelta) -> bool:
        """Check if connection has been idle too long."""
        return datetime.utcnow() - self.last_used_at > max_idle_time


class ConnectionPool(ABC, Generic[T]):
    """
    Abstract base class for connection pools.

    Subclasses implement connection creation, validation, and cleanup.
    The base class handles pool lifecycle and statistics.

    Example:
        class PostgresPool(ConnectionPool[asyncpg.Connection]):
            async def _create_connection(self) -> asyncpg.Connection:
                return await asyncpg.connect(...)

            async def _close_connection(self, conn: asyncpg.Connection) -> None:
                await conn.close()

            async def _validate_connection(self, conn: asyncpg.Connection) -> bool:
                try:
                    await conn.fetchval("SELECT 1")
                    return True
                except:
                    return False

        pool = PostgresPool(config)
        await pool.initialize()

        async with pool.acquire() as conn:
            result = await conn.fetch("SELECT * FROM users")
    """

    def __init__(self, config: PoolConfig) -> None:
        """
        Initialize the pool with configuration.

        Args:
            config: Pool configuration settings.
        """
        self.config = config
        self._pool: list[PooledConnection[T]] = []
        self._in_use: set[PooledConnection[T]] = set()
        self._lock = asyncio.Lock()
        self._semaphore: asyncio.Semaphore | None = None
        self._stats = PoolStats()
        self._initialized = False
        self._closed = False
        self._health_check_task: asyncio.Task[None] | None = None

    @abstractmethod
    async def _create_connection(self) -> T:
        """
        Create a new connection.

        Returns:
            A new connection instance.
        """
        ...

    @abstractmethod
    async def _close_connection(self, connection: T) -> None:
        """
        Close a connection.

        Args:
            connection: The connection to close.
        """
        ...

    @abstractmethod
    async def _validate_connection(self, connection: T) -> bool:
        """
        Validate that a connection is still usable.

        Args:
            connection: The connection to validate.

        Returns:
            True if connection is valid, False otherwise.
        """
        ...

    async def initialize(self) -> None:
        """
        Initialize the pool, creating minimum connections.
        """
        if self._initialized:
            return

        self._semaphore = asyncio.Semaphore(self.config.max_connections)

        # Create minimum connections
        for _ in range(self.config.min_connections):
            try:
                conn = await self._create_connection()
                self._pool.append(PooledConnection(connection=conn))
                self._stats.total_connections += 1
            except Exception as e:
                logger.warning(f"Failed to create initial connection: {e}")

        self._initialized = True

        # Start background health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info(
            f"Pool initialized with {len(self._pool)} connections "
            f"(min: {self.config.min_connections}, max: {self.config.max_connections})"
        )

    async def close(self) -> None:
        """
        Close the pool and all connections.
        """
        if self._closed:
            return

        self._closed = True

        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        async with self._lock:
            for pooled in self._pool:
                try:
                    await self._close_connection(pooled.connection)
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")

            for pooled in self._in_use:
                try:
                    await self._close_connection(pooled.connection)
                except Exception as e:
                    logger.warning(f"Error closing in-use connection: {e}")

            self._pool.clear()
            self._in_use.clear()

        logger.info("Pool closed")

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[T]:
        """
        Acquire a connection from the pool.

        Yields:
            A connection to use.

        Raises:
            asyncio.TimeoutError: If no connection available within timeout.
            RuntimeError: If pool is closed or not initialized.
        """
        if not self._initialized:
            raise RuntimeError("Pool not initialized. Call initialize() first.")
        if self._closed:
            raise RuntimeError("Pool is closed")

        assert self._semaphore is not None

        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.config.acquire_timeout.total_seconds(),
            )
        except asyncio.TimeoutError:
            self._stats.total_timeouts += 1
            raise asyncio.TimeoutError("Timed out waiting for connection from pool")

        pooled: PooledConnection[T] | None = None
        try:
            pooled = await self._get_connection()
            pooled.mark_used()
            self._stats.total_acquired += 1
            yield pooled.connection
        finally:
            if pooled is not None:
                await self._return_connection(pooled)
            self._semaphore.release()

    async def _get_connection(self) -> PooledConnection[T]:
        """Get a connection from pool or create new one."""
        async with self._lock:
            # Try to get an existing connection
            while self._pool:
                pooled = self._pool.pop(0)

                # Check if connection is too old
                if pooled.is_expired(self.config.max_lifetime):
                    await self._close_connection(pooled.connection)
                    self._stats.total_connections -= 1
                    continue

                # Check if connection is stale
                if pooled.is_stale(self.config.max_idle_time):
                    if not await self._validate_connection(pooled.connection):
                        await self._close_connection(pooled.connection)
                        self._stats.total_connections -= 1
                        continue

                self._in_use.add(pooled)
                self._stats.idle_connections = len(self._pool)
                self._stats.active_connections = len(self._in_use)
                return pooled

            # Create a new connection
            conn = await self._create_connection()
            pooled = PooledConnection(connection=conn)
            self._in_use.add(pooled)
            self._stats.total_connections += 1
            self._stats.idle_connections = len(self._pool)
            self._stats.active_connections = len(self._in_use)
            return pooled

    async def _return_connection(self, pooled: PooledConnection[T]) -> None:
        """Return a connection to the pool."""
        async with self._lock:
            self._in_use.discard(pooled)

            # Check if connection should be discarded
            if pooled.is_expired(self.config.max_lifetime):
                await self._close_connection(pooled.connection)
                self._stats.total_connections -= 1
            else:
                self._pool.append(pooled)

            self._stats.total_released += 1
            self._stats.idle_connections = len(self._pool)
            self._stats.active_connections = len(self._in_use)

    async def _health_check_loop(self) -> None:
        """Background task to check connection health."""
        while not self._closed:
            try:
                await asyncio.sleep(self.config.health_check_interval.total_seconds())

                async with self._lock:
                    valid_connections: list[PooledConnection[T]] = []
                    for pooled in self._pool:
                        if await self._validate_connection(pooled.connection):
                            valid_connections.append(pooled)
                        else:
                            await self._close_connection(pooled.connection)
                            self._stats.total_connections -= 1
                            logger.debug("Closed unhealthy connection")

                    self._pool = valid_connections
                    self._stats.idle_connections = len(self._pool)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Error in health check loop: {e}")

    def get_stats(self) -> PoolStats:
        """
        Get current pool statistics.

        Returns:
            PoolStats with current metrics.
        """
        return PoolStats(
            total_connections=self._stats.total_connections,
            idle_connections=len(self._pool),
            active_connections=len(self._in_use),
            waiting_requests=0,  # Would need more tracking for this
            total_acquired=self._stats.total_acquired,
            total_released=self._stats.total_released,
            total_timeouts=self._stats.total_timeouts,
            created_at=self._stats.created_at,
        )

    async def __aenter__(self) -> "ConnectionPool[T]":
        """Support async context manager."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up on context exit."""
        await self.close()
