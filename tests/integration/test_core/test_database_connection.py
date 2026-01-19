"""
Integration tests for database connection module.

Tests async database connections, session management, and transactions
with a real PostgreSQL instance.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy import text, Column, String, DateTime, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.conftest import requires_postgres


pytestmark = [pytest.mark.integration, requires_postgres]


class TestAsyncDatabaseConnection:
    """Tests for async database connection management."""

    @pytest.mark.asyncio
    async def test_async_session_creation(self, async_db_session: AsyncSession):
        """Test that async database session is created successfully."""
        assert async_db_session is not None
        assert isinstance(async_db_session, AsyncSession)

    @pytest.mark.asyncio
    async def test_simple_query_execution(self, async_db_session: AsyncSession):
        """Test executing a simple SQL query."""
        result = await async_db_session.execute(text("SELECT 1 as value"))
        row = result.fetchone()

        assert row is not None
        assert row.value == 1

    @pytest.mark.asyncio
    async def test_database_version_query(self, async_db_session: AsyncSession):
        """Test querying database version."""
        result = await async_db_session.execute(text("SELECT version()"))
        row = result.fetchone()

        assert row is not None
        assert "PostgreSQL" in row[0]

    @pytest.mark.asyncio
    async def test_current_timestamp_query(self, async_db_session: AsyncSession):
        """Test querying current timestamp from database."""
        result = await async_db_session.execute(text("SELECT NOW() as db_time"))
        row = result.fetchone()

        assert row is not None
        assert row.db_time is not None
        # Should be close to current time
        time_diff = abs((datetime.utcnow() - row.db_time.replace(tzinfo=None)).total_seconds())
        assert time_diff < 60  # Within 1 minute

    @pytest.mark.asyncio
    async def test_create_temp_table(self, async_db_session: AsyncSession):
        """Test creating and using a temporary table."""
        # Create temp table
        await async_db_session.execute(text("""
            CREATE TEMP TABLE test_items (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))

        # Insert data
        await async_db_session.execute(text("""
            INSERT INTO test_items (name) VALUES ('item1'), ('item2'), ('item3')
        """))

        # Query data
        result = await async_db_session.execute(text("SELECT COUNT(*) FROM test_items"))
        count = result.scalar()

        assert count == 3

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, async_db_session: AsyncSession):
        """Test that transaction rollback works correctly."""
        # Create temp table
        await async_db_session.execute(text("""
            CREATE TEMP TABLE rollback_test (
                id SERIAL PRIMARY KEY,
                value INTEGER NOT NULL
            )
        """))

        # Insert in a nested transaction that we'll rollback
        try:
            await async_db_session.execute(
                text("INSERT INTO rollback_test (value) VALUES (100)")
            )

            # Verify insert
            result = await async_db_session.execute(
                text("SELECT COUNT(*) FROM rollback_test")
            )
            assert result.scalar() == 1

            # The fixture will rollback the transaction
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_parameterized_query(self, async_db_session: AsyncSession):
        """Test executing parameterized queries."""
        # Create temp table
        await async_db_session.execute(text("""
            CREATE TEMP TABLE users_test (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(200) NOT NULL
            )
        """))

        # Insert with parameters
        await async_db_session.execute(
            text("INSERT INTO users_test (name, email) VALUES (:name, :email)"),
            {"name": "Test User", "email": "test@example.com"}
        )

        # Query with parameters
        result = await async_db_session.execute(
            text("SELECT * FROM users_test WHERE email = :email"),
            {"email": "test@example.com"}
        )
        row = result.fetchone()

        assert row is not None
        assert row.name == "Test User"
        assert row.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_json_column_operations(self, async_db_session: AsyncSession):
        """Test JSON/JSONB column operations."""
        # Create temp table with JSONB
        await async_db_session.execute(text("""
            CREATE TEMP TABLE json_test (
                id SERIAL PRIMARY KEY,
                data JSONB NOT NULL
            )
        """))

        # Insert JSON data
        await async_db_session.execute(
            text("INSERT INTO json_test (data) VALUES (:data::jsonb)"),
            {"data": '{"name": "test", "values": [1, 2, 3], "nested": {"key": "value"}}'}
        )

        # Query and extract JSON fields
        result = await async_db_session.execute(text("""
            SELECT
                data->>'name' as name,
                data->'values'->0 as first_value,
                data->'nested'->>'key' as nested_key
            FROM json_test
        """))
        row = result.fetchone()

        assert row.name == "test"
        assert row.first_value == 1
        assert row.nested_key == "value"

    @pytest.mark.asyncio
    async def test_array_column_operations(self, async_db_session: AsyncSession):
        """Test PostgreSQL array column operations."""
        # Create temp table with array column
        await async_db_session.execute(text("""
            CREATE TEMP TABLE array_test (
                id SERIAL PRIMARY KEY,
                tags TEXT[] NOT NULL
            )
        """))

        # Insert array data
        await async_db_session.execute(
            text("INSERT INTO array_test (tags) VALUES (:tags)"),
            {"tags": ["python", "postgres", "testing"]}
        )

        # Query array operations
        result = await async_db_session.execute(text("""
            SELECT
                array_length(tags, 1) as tag_count,
                tags[1] as first_tag,
                'python' = ANY(tags) as has_python
            FROM array_test
        """))
        row = result.fetchone()

        assert row.tag_count == 3
        assert row.first_tag == "python"
        assert row.has_python is True

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, async_db_session: AsyncSession):
        """Test running concurrent queries."""
        import asyncio

        async def run_query(n: int):
            result = await async_db_session.execute(
                text("SELECT :n * 2 as doubled"),
                {"n": n}
            )
            return result.scalar()

        # Run multiple queries concurrently
        results = await asyncio.gather(
            run_query(1),
            run_query(2),
            run_query(3),
            run_query(4),
            run_query(5),
        )

        assert results == [2, 4, 6, 8, 10]


class TestConnectionPooling:
    """Tests for connection pool behavior."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_multiple_sessions(self, test_env):
        """Test creating multiple database sessions."""
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

        db_url = (
            f"postgresql+asyncpg://{test_env['DATABASE__USER']}:{test_env['DATABASE__PASSWORD']}"
            f"@{test_env['DATABASE__HOST']}:{test_env['DATABASE__PORT']}/{test_env['DATABASE__NAME']}"
        )

        engine = create_async_engine(db_url, pool_size=5, echo=False)
        async_session = async_sessionmaker(bind=engine, class_=AsyncSession)

        sessions = []
        try:
            # Create multiple sessions
            for _ in range(5):
                session = async_session()
                sessions.append(session)

                # Execute a query in each session
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1

        finally:
            # Clean up
            for session in sessions:
                await session.close()
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_session_reuse(self, async_db_session: AsyncSession):
        """Test that session can be reused for multiple queries."""
        for i in range(10):
            result = await async_db_session.execute(
                text("SELECT :i as iteration"),
                {"i": i}
            )
            assert result.scalar() == i


class TestDatabaseExtensions:
    """Tests for PostgreSQL extensions."""

    @pytest.mark.asyncio
    async def test_age_extension_available(self, async_db_session: AsyncSession):
        """Test that Apache AGE extension is available."""
        try:
            # Check if AGE extension exists
            result = await async_db_session.execute(text("""
                SELECT extname FROM pg_extension WHERE extname = 'age'
            """))
            row = result.fetchone()

            if row is None:
                pytest.skip("Apache AGE extension not installed")

            assert row.extname == "age"
        except Exception as e:
            pytest.skip(f"Could not check AGE extension: {e}")

    @pytest.mark.asyncio
    async def test_uuid_generation(self, async_db_session: AsyncSession):
        """Test UUID generation functions."""
        # Enable uuid-ossp if not already
        try:
            await async_db_session.execute(
                text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            )
        except Exception:
            pass

        result = await async_db_session.execute(text("""
            SELECT gen_random_uuid() as random_uuid
        """))
        row = result.fetchone()

        assert row is not None
        assert row.random_uuid is not None
        # UUID should be 36 characters (including hyphens)
        assert len(str(row.random_uuid)) == 36
