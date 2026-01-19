"""
PostgreSQL connector for Open Forge.
Provides async connection and data access for PostgreSQL databases.
"""
from typing import Optional

from pydantic import Field

from connectors.base import ConnectorRegistry
from connectors.database.base_sql import BaseSQLConnector, SQLConnectorConfig


class PostgresConfig(SQLConnectorConfig):
    """Configuration for PostgreSQL connector."""
    connector_type: str = Field(default="postgres", frozen=True)
    port: int = Field(default=5432, description="PostgreSQL port")
    schema_name: str = Field(default="public", description="PostgreSQL schema")
    ssl_mode: Optional[str] = Field(
        default=None,
        description="SSL mode: disable, allow, prefer, require, verify-ca, verify-full"
    )

    @property
    def connection_string(self) -> str:
        """Generate async connection string for PostgreSQL."""
        ssl_param = f"?sslmode={self.ssl_mode}" if self.ssl_mode else ""
        return (
            f"postgresql+asyncpg://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}{ssl_param}"
        )


@ConnectorRegistry.register("postgres")
class PostgresConnector(BaseSQLConnector):
    """
    PostgreSQL database connector.

    Uses asyncpg for async operations through SQLAlchemy.

    Example:
        config = PostgresConfig(
            name="my-postgres",
            host="localhost",
            port=5432,
            username="user",
            password="pass",
            database="mydb"
        )
        async with PostgresConnector(config) as conn:
            schemas = await conn.fetch_schema()
            sample = await conn.fetch_sample("users", limit=10)
    """

    def __init__(self, config: PostgresConfig):
        super().__init__(config)
        self.config: PostgresConfig = config

    def _get_tables_query(self) -> str:
        """Return query to list tables in PostgreSQL."""
        schema = self.config.schema_name or "public"
        return f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{schema}'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """

    def _get_columns_query(self, table_name: str) -> str:
        """Return query to get column info for a PostgreSQL table."""
        schema = self.config.schema_name or "public"
        return f"""
            SELECT
                c.column_name,
                c.data_type,
                CASE WHEN c.is_nullable = 'YES' THEN true ELSE false END as is_nullable,
                CASE WHEN tc.constraint_type = 'PRIMARY KEY' THEN true ELSE false END as is_primary
            FROM information_schema.columns c
            LEFT JOIN information_schema.key_column_usage kcu
                ON c.table_name = kcu.table_name
                AND c.column_name = kcu.column_name
                AND c.table_schema = kcu.table_schema
            LEFT JOIN information_schema.table_constraints tc
                ON kcu.constraint_name = tc.constraint_name
                AND kcu.table_schema = tc.table_schema
                AND tc.constraint_type = 'PRIMARY KEY'
            WHERE c.table_name = '{table_name}'
            AND c.table_schema = '{schema}'
            ORDER BY c.ordinal_position
        """

    def _map_db_type(self, db_type: str) -> str:
        """Map PostgreSQL types to common type names."""
        type_map = {
            "integer": "int",
            "bigint": "long",
            "smallint": "short",
            "numeric": "decimal",
            "real": "float",
            "double precision": "double",
            "character varying": "string",
            "character": "string",
            "text": "string",
            "boolean": "boolean",
            "date": "date",
            "timestamp without time zone": "timestamp",
            "timestamp with time zone": "timestamp_tz",
            "time without time zone": "time",
            "time with time zone": "time_tz",
            "bytea": "binary",
            "json": "json",
            "jsonb": "json",
            "uuid": "uuid",
            "array": "array",
            "inet": "string",
            "cidr": "string",
            "macaddr": "string",
        }
        return type_map.get(db_type.lower(), db_type)

    async def list_schemas(self) -> list[str]:
        """List all schemas in the database."""
        query = """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
        """
        results = await self.execute_query(query)
        return [r["schema_name"] for r in results]

    async def get_table_size(self, table_name: str) -> dict:
        """Get size information for a table."""
        schema = self.config.schema_name or "public"
        query = f"""
            SELECT
                pg_size_pretty(pg_total_relation_size('{schema}.{table_name}')) as total_size,
                pg_size_pretty(pg_table_size('{schema}.{table_name}')) as table_size,
                pg_size_pretty(pg_indexes_size('{schema}.{table_name}')) as indexes_size
        """
        results = await self.execute_query(query)
        return results[0] if results else {}

    async def get_indexes(self, table_name: str) -> list[dict]:
        """Get index information for a table."""
        schema = self.config.schema_name or "public"
        query = f"""
            SELECT
                indexname as name,
                indexdef as definition
            FROM pg_indexes
            WHERE schemaname = '{schema}'
            AND tablename = '{table_name}'
        """
        return await self.execute_query(query)
