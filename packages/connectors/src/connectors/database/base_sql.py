"""
Base SQL connector for relational databases.
Provides common functionality for PostgreSQL, MySQL, and other SQL databases.
"""
import time
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import Field
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection

from connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectionStatus,
    ConnectionTestResult,
    DataSchema,
    SchemaField,
    SampleData,
)


class SQLConnectorConfig(ConnectorConfig):
    """Configuration for SQL database connectors."""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(..., description="Database port")
    username: str = Field(..., description="Database username")
    password: str = Field(default="", description="Database password")
    database: str = Field(..., description="Database name")
    schema_name: Optional[str] = Field(default=None, description="Schema name (if applicable)")
    pool_size: int = Field(default=5, description="Connection pool size")
    pool_recycle: int = Field(default=3600, description="Connection recycle time in seconds")
    ssl_mode: Optional[str] = Field(default=None, description="SSL mode for connection")

    @property
    @abstractmethod
    def connection_string(self) -> str:
        """Generate the async connection string for the database."""
        pass


class BaseSQLConnector(BaseConnector):
    """
    Base connector for SQL databases.
    Provides common SQL operations using SQLAlchemy async engine.
    """

    def __init__(self, config: SQLConnectorConfig):
        super().__init__(config)
        self.config: SQLConnectorConfig = config
        self._engine: Optional[AsyncEngine] = None

    @property
    def engine(self) -> AsyncEngine:
        """Get the SQLAlchemy async engine."""
        if self._engine is None:
            raise RuntimeError("Connector not connected. Call connect() first.")
        return self._engine

    async def connect(self) -> None:
        """Establish connection to the database."""
        self._status = ConnectionStatus.CONNECTING
        try:
            self._engine = create_async_engine(
                self.config.connection_string,
                pool_size=self.config.pool_size,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,
            )
            # Test connection
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            self._status = ConnectionStatus.CONNECTED
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            raise RuntimeError(f"Failed to connect to database: {e}") from e

    async def disconnect(self) -> None:
        """Close the database connection."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
        self._status = ConnectionStatus.DISCONNECTED

    async def test_connection(self) -> ConnectionTestResult:
        """Test the database connection."""
        start_time = time.time()
        try:
            if not self._engine:
                # Create temporary engine for testing
                engine = create_async_engine(self.config.connection_string)
                try:
                    async with engine.connect() as conn:
                        await conn.execute(text("SELECT 1"))
                finally:
                    await engine.dispose()
            else:
                async with self._engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))

            latency_ms = (time.time() - start_time) * 1000
            return ConnectionTestResult(
                success=True,
                message="Connection successful",
                latency_ms=latency_ms,
                details={
                    "host": self.config.host,
                    "port": self.config.port,
                    "database": self.config.database,
                }
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                latency_ms=latency_ms,
                details={"error": str(e)}
            )

    @abstractmethod
    def _get_tables_query(self) -> str:
        """Return SQL query to list tables in the database."""
        pass

    @abstractmethod
    def _get_columns_query(self, table_name: str) -> str:
        """Return SQL query to get column information for a table."""
        pass

    @abstractmethod
    def _map_db_type(self, db_type: str) -> str:
        """Map database-specific type to a common type name."""
        pass

    async def fetch_schema(self, source: Optional[str] = None) -> List[DataSchema]:
        """
        Fetch schema information from the database.

        Args:
            source: Optional table name. If None, returns all tables.

        Returns:
            List of DataSchema objects.
        """
        schemas = []
        async with self.engine.connect() as conn:
            if source:
                tables = [source]
            else:
                result = await conn.execute(text(self._get_tables_query()))
                tables = [row[0] for row in result.fetchall()]

            for table_name in tables:
                columns_query = self._get_columns_query(table_name)
                result = await conn.execute(text(columns_query))
                rows = result.fetchall()

                fields = []
                primary_keys = []
                for row in rows:
                    field = SchemaField(
                        name=row[0],
                        data_type=self._map_db_type(row[1]),
                        nullable=row[2] if len(row) > 2 else True,
                        metadata={"original_type": row[1]}
                    )
                    fields.append(field)
                    if len(row) > 3 and row[3]:  # is_primary_key
                        primary_keys.append(row[0])

                schemas.append(DataSchema(
                    name=table_name,
                    fields=fields,
                    primary_key=primary_keys if primary_keys else None,
                ))

        return schemas

    async def fetch_sample(
        self,
        source: str,
        limit: int = 100
    ) -> SampleData:
        """
        Fetch sample data from a table.

        Args:
            source: Table name.
            limit: Maximum number of rows.

        Returns:
            SampleData with schema and rows.
        """
        # First get the schema
        schemas = await self.fetch_schema(source)
        if not schemas:
            raise ValueError(f"Table not found: {source}")
        schema = schemas[0]

        # Get sample data
        async with self.engine.connect() as conn:
            # Get total count
            count_result = await conn.execute(
                text(f"SELECT COUNT(*) FROM {source}")
            )
            total_count = count_result.scalar()

            # Get sample rows
            result = await conn.execute(
                text(f"SELECT * FROM {source} LIMIT :limit"),
                {"limit": limit}
            )
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

        return SampleData(
            schema=schema,
            rows=rows,
            total_count=total_count,
            sample_size=len(rows)
        )

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query string.
            parameters: Optional query parameters.

        Returns:
            List of dictionaries representing rows.
        """
        async with self.engine.connect() as conn:
            result = await conn.execute(text(query), parameters or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
