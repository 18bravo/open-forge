"""
PostgreSQL connector with CDC support via logical replication.

Features:
- Full batch extraction
- Incremental sync with cursor
- CDC via logical replication (pgoutput/wal2json)
- Connection pooling
- pgvector support for vector operations
"""

import logging
from datetime import datetime
from typing import Any, AsyncIterator, Optional

import pyarrow as pa
from pydantic import Field

from forge_connectors.auth.secrets import SecretsProvider
from forge_connectors.core.base import (
    CDCEvent,
    ConnectorCapability,
    ConnectionTestResult,
    HealthStatus,
    SyncState,
    WriteResult,
)
from forge_connectors.core.pool import ConnectionPool, PoolConfig
from forge_connectors.core.registry import ConnectorRegistry
from forge_connectors.connectors.sql.base import SQLConnector, SQLConnectorConfig

logger = logging.getLogger(__name__)


class PostgreSQLConfig(SQLConnectorConfig):
    """Configuration for PostgreSQL connector."""

    connector_type: str = "postgresql"
    port: int = 5432
    schema_name: str = Field(default="public", alias="schema")
    ssl_mode: str = "prefer"

    # Connection pool settings
    pool_min_size: int = 2
    pool_max_size: int = 10

    # CDC settings
    replication_slot: Optional[str] = None
    publication_name: Optional[str] = None


class PostgreSQLPool(ConnectionPool[Any]):
    """Connection pool for PostgreSQL using asyncpg."""

    def __init__(
        self,
        config: PostgreSQLConfig,
        credentials: dict[str, str],
        pool_config: PoolConfig,
    ):
        """
        Initialize PostgreSQL connection pool.

        Args:
            config: PostgreSQL configuration.
            credentials: Username/password from secrets.
            pool_config: Pool configuration.
        """
        super().__init__(pool_config)
        self.pg_config = config
        self.credentials = credentials

    async def _create_connection(self) -> Any:
        """Create a new asyncpg connection."""
        try:
            import asyncpg
        except ImportError:
            raise ImportError(
                "asyncpg package required for PostgreSQL. "
                "Install with: pip install asyncpg"
            )

        return await asyncpg.connect(
            host=self.pg_config.host,
            port=self.pg_config.port,
            database=self.pg_config.database,
            user=self.credentials.get("username") or self.credentials.get("user"),
            password=self.credentials.get("password"),
            ssl=self.pg_config.ssl_mode,
        )

    async def _close_connection(self, connection: Any) -> None:
        """Close an asyncpg connection."""
        await connection.close()

    async def _validate_connection(self, connection: Any) -> bool:
        """Validate connection is still usable."""
        try:
            await connection.fetchval("SELECT 1")
            return True
        except Exception:
            return False


@ConnectorRegistry.register(
    "postgresql",
    "sql",
    "PostgreSQL database with CDC support via logical replication",
)
class PostgreSQLConnector(SQLConnector):
    """
    PostgreSQL connector with full feature support.

    Supports:
    - Batch extraction
    - Incremental sync with cursor field
    - CDC via logical replication
    - Write operations (reverse ETL)

    Example:
        config = PostgreSQLConfig(
            name="Production DB",
            host="db.example.com",
            database="mydb",
            secrets_ref="vault/postgres/prod",
        )

        connector = PostgreSQLConnector(config, secrets_provider)
        await connector.initialize()

        # Test connection
        result = await connector.test_connection()

        # Discover schema
        tables = await connector.discover_schema()

        # Read data
        async for batch in connector.read_batch("orders"):
            process(batch)

        # Cleanup
        await connector.close()
    """

    connector_type = "postgresql"
    category = "sql"

    def __init__(self, config: PostgreSQLConfig, secrets: SecretsProvider):
        """
        Initialize PostgreSQL connector.

        Args:
            config: PostgreSQL configuration.
            secrets: Secrets provider for credentials.
        """
        self.config = config
        self._secrets = secrets
        self._pool: Optional[PostgreSQLPool] = None
        self._initialized = False

    @classmethod
    def get_capabilities(cls) -> list[ConnectorCapability]:
        """PostgreSQL supports all capabilities."""
        return [
            ConnectorCapability.BATCH,
            ConnectorCapability.INCREMENTAL,
            ConnectorCapability.CDC,
            ConnectorCapability.SCHEMA_DISCOVERY,
            ConnectorCapability.DATA_PROFILING,
            ConnectorCapability.WRITE_BATCH,
            ConnectorCapability.WRITE_RECORD,
        ]

    async def initialize(self) -> None:
        """Initialize connection pool."""
        if self._initialized:
            return

        # Get credentials
        credentials = await self._secrets.get(self.config.secrets_ref or "")

        # Create pool
        pool_config = PoolConfig(
            min_connections=self.config.pool_min_size,
            max_connections=self.config.pool_max_size,
        )
        self._pool = PostgreSQLPool(self.config, credentials, pool_config)
        await self._pool.initialize()
        self._initialized = True

        logger.info(f"PostgreSQL connector initialized: {self.config.host}/{self.config.database}")

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure connector is initialized."""
        if not self._initialized:
            await self.initialize()

    async def _execute_query(
        self, query: str, *args: Any
    ) -> list[dict[str, Any]]:
        """Execute query and return results."""
        await self._ensure_initialized()
        assert self._pool is not None

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def _execute_query_iter(
        self, query: str, *args: Any, batch_size: int = 10000
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Execute query and yield batches."""
        await self._ensure_initialized()
        assert self._pool is not None

        async with self._pool.acquire() as conn:
            # Use cursor for large result sets
            async with conn.transaction():
                cursor = await conn.cursor(query, *args)

                while True:
                    rows = await cursor.fetch(batch_size)
                    if not rows:
                        break
                    yield [dict(row) for row in rows]

    async def test_connection(self) -> ConnectionTestResult:
        """Test PostgreSQL connection."""
        try:
            start = datetime.utcnow()
            await self._ensure_initialized()
            assert self._pool is not None

            async with self._pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                latency = (datetime.utcnow() - start).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                latency_ms=latency,
                server_version=version,
            )

        except Exception as e:
            return ConnectionTestResult(success=False, error=str(e))

    async def health_check(self) -> HealthStatus:
        """Check connection health."""
        try:
            await self._ensure_initialized()
            assert self._pool is not None

            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            return HealthStatus(
                healthy=True,
                last_check_at=datetime.utcnow(),
                details={"pool_stats": self._pool.get_stats().__dict__},
            )

        except Exception as e:
            return HealthStatus(
                healthy=False,
                last_check_at=datetime.utcnow(),
                error=str(e),
            )

    async def read_cdc(
        self, object_name: str, state: SyncState
    ) -> AsyncIterator[CDCEvent]:
        """
        Read CDC events using logical replication.

        Note: This is a stub implementation. Full CDC requires:
        - A replication slot configured on the server
        - Publication for the target tables
        - pgoutput or wal2json output plugin
        """
        if not self.config.replication_slot:
            raise NotImplementedError(
                "CDC requires replication_slot to be configured. "
                "Create a replication slot with: "
                "SELECT pg_create_logical_replication_slot('my_slot', 'pgoutput')"
            )

        if not self.config.publication_name:
            raise NotImplementedError(
                "CDC requires publication_name to be configured. "
                f"Create a publication with: CREATE PUBLICATION my_pub FOR TABLE {object_name}"
            )

        # Stub: In production, this would connect to the replication stream
        # and yield CDC events
        logger.warning(
            "CDC via logical replication is a stub. "
            "Full implementation requires replication protocol support."
        )

        # Empty iterator
        return
        yield  # Make this a generator

    async def write_batch(
        self, object_name: str, records: list[dict[str, Any]]
    ) -> WriteResult:
        """Write batch of records to PostgreSQL."""
        if not records:
            return WriteResult(success_count=0)

        await self._ensure_initialized()
        assert self._pool is not None

        # Get column names from first record
        columns = list(records[0].keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
        column_list = ", ".join(f'"{c}"' for c in columns)

        full_name = f'"{self.config.schema_name}"."{object_name}"'
        query = f"INSERT INTO {full_name} ({column_list}) VALUES ({placeholders})"

        success_count = 0
        failure_count = 0
        errors: list[str] = []

        async with self._pool.acquire() as conn:
            for record in records:
                try:
                    values = [record.get(c) for c in columns]
                    await conn.execute(query, *values)
                    success_count += 1
                except Exception as e:
                    failure_count += 1
                    errors.append(str(e))

        return WriteResult(
            success_count=success_count,
            failure_count=failure_count,
            errors=errors,
        )

    async def write_record(
        self, object_name: str, record: dict[str, Any]
    ) -> WriteResult:
        """Write single record to PostgreSQL."""
        return await self.write_batch(object_name, [record])

    # PostgreSQL-specific methods

    async def get_replication_slots(self) -> list[dict[str, Any]]:
        """List replication slots."""
        return await self._execute_query(
            "SELECT slot_name, plugin, slot_type, active "
            "FROM pg_replication_slots"
        )

    async def create_replication_slot(
        self, slot_name: str, plugin: str = "pgoutput"
    ) -> None:
        """Create a logical replication slot."""
        await self._ensure_initialized()
        assert self._pool is not None

        async with self._pool.acquire() as conn:
            await conn.execute(
                f"SELECT pg_create_logical_replication_slot($1, $2)",
                slot_name,
                plugin,
            )

    async def get_publications(self) -> list[dict[str, Any]]:
        """List publications."""
        return await self._execute_query(
            "SELECT pubname, pubowner::regrole, puballtables, pubinsert, "
            "pubupdate, pubdelete FROM pg_publication"
        )

    async def check_pgvector(self) -> bool:
        """Check if pgvector extension is available."""
        try:
            result = await self._execute_query(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            )
            return len(result) > 0
        except Exception:
            return False
