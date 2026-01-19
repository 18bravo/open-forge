"""
Integration tests for PostgreSQL connector.

Tests real PostgreSQL connections, schema discovery, and data fetching.
"""
import pytest
import pytest_asyncio
from datetime import datetime

from tests.integration.conftest import requires_postgres


pytestmark = [pytest.mark.integration, requires_postgres]


class TestPostgresConnectorConnection:
    """Tests for PostgreSQL connector connection management."""

    @pytest.mark.asyncio
    async def test_connector_creation(self, test_env):
        """Test creating a PostgreSQL connector."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig

        config = PostgresConfig(
            name="test-postgres",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username=test_env["DATABASE__USER"],
            password=test_env["DATABASE__PASSWORD"],
            database=test_env["DATABASE__NAME"],
        )

        connector = PostgresConnector(config)

        assert connector is not None
        assert connector.config.host == test_env["DATABASE__HOST"]

    @pytest.mark.asyncio
    async def test_connector_connect(self, test_env):
        """Test connecting to PostgreSQL."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig

        config = PostgresConfig(
            name="test-postgres-connect",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username=test_env["DATABASE__USER"],
            password=test_env["DATABASE__PASSWORD"],
            database=test_env["DATABASE__NAME"],
        )

        connector = PostgresConnector(config)

        await connector.connect()

        try:
            from connectors.base import ConnectionStatus
            assert connector.status == ConnectionStatus.CONNECTED
        finally:
            await connector.disconnect()

    @pytest.mark.asyncio
    async def test_connector_disconnect(self, test_env):
        """Test disconnecting from PostgreSQL."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig
        from connectors.base import ConnectionStatus

        config = PostgresConfig(
            name="test-postgres-disconnect",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username=test_env["DATABASE__USER"],
            password=test_env["DATABASE__PASSWORD"],
            database=test_env["DATABASE__NAME"],
        )

        connector = PostgresConnector(config)

        await connector.connect()
        await connector.disconnect()

        assert connector.status == ConnectionStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_connection_test(self, test_env):
        """Test connection testing functionality."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig

        config = PostgresConfig(
            name="test-postgres-test",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username=test_env["DATABASE__USER"],
            password=test_env["DATABASE__PASSWORD"],
            database=test_env["DATABASE__NAME"],
        )

        connector = PostgresConnector(config)

        result = await connector.test_connection()

        assert result.success is True
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_invalid_connection(self, test_env):
        """Test connection with invalid credentials."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig

        config = PostgresConfig(
            name="test-invalid",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username="invalid_user",
            password="invalid_password",
            database="nonexistent_db",
        )

        connector = PostgresConnector(config)

        result = await connector.test_connection()

        assert result.success is False


class TestPostgresSchemaDiscovery:
    """Tests for schema discovery functionality."""

    @pytest.mark.asyncio
    async def test_list_schemas(self, test_env, async_db_session):
        """Test listing database schemas."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig
        from sqlalchemy import text

        # Create a test schema
        await async_db_session.execute(
            text("CREATE SCHEMA IF NOT EXISTS test_schema_discovery")
        )
        await async_db_session.commit()

        config = PostgresConfig(
            name="test-list-schemas",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username=test_env["DATABASE__USER"],
            password=test_env["DATABASE__PASSWORD"],
            database=test_env["DATABASE__NAME"],
        )

        async with PostgresConnector(config) as connector:
            schemas = await connector.list_schemas()

            assert isinstance(schemas, list)
            assert "public" in schemas

        # Clean up
        await async_db_session.execute(
            text("DROP SCHEMA IF EXISTS test_schema_discovery")
        )
        await async_db_session.commit()

    @pytest.mark.asyncio
    async def test_fetch_schema(self, test_env, async_db_session):
        """Test fetching table schema information."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig
        from sqlalchemy import text

        # Create a test table
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS connector_schema_test (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(200),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        await async_db_session.commit()

        config = PostgresConfig(
            name="test-fetch-schema",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username=test_env["DATABASE__USER"],
            password=test_env["DATABASE__PASSWORD"],
            database=test_env["DATABASE__NAME"],
        )

        try:
            async with PostgresConnector(config) as connector:
                schemas = await connector.fetch_schema()

                # Find our test table
                test_table = None
                for s in schemas:
                    if s.name == "connector_schema_test":
                        test_table = s
                        break

                if test_table:
                    field_names = [f.name for f in test_table.fields]
                    assert "id" in field_names
                    assert "name" in field_names
                    assert "email" in field_names
        finally:
            # Clean up
            await async_db_session.execute(
                text("DROP TABLE IF EXISTS connector_schema_test")
            )
            await async_db_session.commit()


class TestPostgresDataFetching:
    """Tests for data fetching functionality."""

    @pytest.mark.asyncio
    async def test_execute_query(self, test_env, async_db_session):
        """Test executing a query."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig
        from sqlalchemy import text

        # Create and populate a test table
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS query_test (
                id SERIAL PRIMARY KEY,
                value INTEGER NOT NULL
            )
        """))
        await async_db_session.execute(text("""
            INSERT INTO query_test (value) VALUES (10), (20), (30)
            ON CONFLICT DO NOTHING
        """))
        await async_db_session.commit()

        config = PostgresConfig(
            name="test-query",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username=test_env["DATABASE__USER"],
            password=test_env["DATABASE__PASSWORD"],
            database=test_env["DATABASE__NAME"],
        )

        try:
            async with PostgresConnector(config) as connector:
                results = await connector.execute_query(
                    "SELECT * FROM query_test ORDER BY id"
                )

                assert len(results) >= 3
        finally:
            await async_db_session.execute(
                text("DROP TABLE IF EXISTS query_test")
            )
            await async_db_session.commit()

    @pytest.mark.asyncio
    async def test_fetch_sample(self, test_env, async_db_session):
        """Test fetching sample data from a table."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig
        from sqlalchemy import text

        # Create and populate a test table
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS sample_test (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                score DECIMAL(5,2)
            )
        """))
        await async_db_session.execute(text("""
            INSERT INTO sample_test (name, score)
            VALUES ('Alice', 95.5), ('Bob', 87.0), ('Charlie', 92.3)
            ON CONFLICT DO NOTHING
        """))
        await async_db_session.commit()

        config = PostgresConfig(
            name="test-sample",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username=test_env["DATABASE__USER"],
            password=test_env["DATABASE__PASSWORD"],
            database=test_env["DATABASE__NAME"],
        )

        try:
            async with PostgresConnector(config) as connector:
                sample = await connector.fetch_sample("sample_test", limit=2)

                assert sample.sample_size <= 2
                assert len(sample.schema.fields) > 0
        finally:
            await async_db_session.execute(
                text("DROP TABLE IF EXISTS sample_test")
            )
            await async_db_session.commit()

    @pytest.mark.asyncio
    async def test_get_table_size(self, test_env, async_db_session):
        """Test getting table size information."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig
        from sqlalchemy import text

        # Create a test table
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS size_test (
                id SERIAL PRIMARY KEY,
                data TEXT
            )
        """))
        await async_db_session.execute(text("""
            INSERT INTO size_test (data)
            SELECT repeat('x', 1000) FROM generate_series(1, 100)
            ON CONFLICT DO NOTHING
        """))
        await async_db_session.commit()

        config = PostgresConfig(
            name="test-size",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username=test_env["DATABASE__USER"],
            password=test_env["DATABASE__PASSWORD"],
            database=test_env["DATABASE__NAME"],
        )

        try:
            async with PostgresConnector(config) as connector:
                size_info = await connector.get_table_size("size_test")

                assert "total_size" in size_info
        finally:
            await async_db_session.execute(
                text("DROP TABLE IF EXISTS size_test")
            )
            await async_db_session.commit()

    @pytest.mark.asyncio
    async def test_get_indexes(self, test_env, async_db_session):
        """Test getting index information."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig
        from sqlalchemy import text

        # Create a test table with index
        await async_db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS index_test (
                id SERIAL PRIMARY KEY,
                email VARCHAR(200) UNIQUE
            )
        """))
        await async_db_session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_index_test_email
            ON index_test(email)
        """))
        await async_db_session.commit()

        config = PostgresConfig(
            name="test-indexes",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username=test_env["DATABASE__USER"],
            password=test_env["DATABASE__PASSWORD"],
            database=test_env["DATABASE__NAME"],
        )

        try:
            async with PostgresConnector(config) as connector:
                indexes = await connector.get_indexes("index_test")

                assert isinstance(indexes, list)
                # Should have at least the primary key index
                assert len(indexes) >= 1
        finally:
            await async_db_session.execute(
                text("DROP TABLE IF EXISTS index_test")
            )
            await async_db_session.commit()


class TestPostgresContextManager:
    """Tests for context manager usage."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self, test_env):
        """Test using connector as async context manager."""
        from connectors.database.postgres import PostgresConnector, PostgresConfig
        from connectors.base import ConnectionStatus

        config = PostgresConfig(
            name="test-context",
            host=test_env["DATABASE__HOST"],
            port=int(test_env["DATABASE__PORT"]),
            username=test_env["DATABASE__USER"],
            password=test_env["DATABASE__PASSWORD"],
            database=test_env["DATABASE__NAME"],
        )

        async with PostgresConnector(config) as connector:
            assert connector.status == ConnectionStatus.CONNECTED

            results = await connector.execute_query("SELECT 1 as value")
            assert results[0]["value"] == 1

        # After exiting context, should be disconnected
        assert connector.status == ConnectionStatus.DISCONNECTED
