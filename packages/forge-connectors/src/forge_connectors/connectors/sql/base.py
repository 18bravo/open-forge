"""
Base class for SQL database connectors.

Provides shared functionality for SQL databases including:
- Schema discovery via information_schema
- Cursor-based pagination
- Type mapping to Arrow
"""

from abc import abstractmethod
from datetime import datetime
from typing import Any, AsyncIterator, Optional

import pyarrow as pa
from pydantic import Field

from forge_connectors.core.base import (
    BaseConnector,
    ColumnInfo,
    ConnectorCapability,
    ConnectorConfig,
    ConnectionTestResult,
    DataProfile,
    HealthStatus,
    SchemaObject,
    SyncState,
)
from forge_connectors.core.discovery import map_to_arrow_type


class SQLConnectorConfig(ConnectorConfig):
    """Base configuration for SQL connectors."""

    host: str
    port: int
    database: str
    schema_name: str = Field(default="public", alias="schema")
    ssl_mode: str = "prefer"

    model_config = {"extra": "forbid", "populate_by_name": True}


class SQLConnector(BaseConnector):
    """
    Base class for SQL database connectors.

    Provides common functionality for SQL databases:
    - Schema discovery using information_schema
    - Cursor-based batch reading
    - Data profiling using SQL aggregations

    Subclasses must implement:
    - _get_connection(): Get database connection
    - _execute_query(): Execute SQL and return rows
    """

    category = "sql"

    @classmethod
    def get_capabilities(cls) -> list[ConnectorCapability]:
        """SQL connectors support batch, incremental, and profiling."""
        return [
            ConnectorCapability.BATCH,
            ConnectorCapability.INCREMENTAL,
            ConnectorCapability.SCHEMA_DISCOVERY,
            ConnectorCapability.DATA_PROFILING,
        ]

    @abstractmethod
    async def _execute_query(
        self, query: str, *args: Any
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL query and return results as list of dicts.

        Args:
            query: SQL query with $N placeholders.
            *args: Query parameters.

        Returns:
            List of row dictionaries.
        """
        ...

    @abstractmethod
    async def _execute_query_iter(
        self, query: str, *args: Any, batch_size: int = 10000
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """
        Execute a SQL query and yield results in batches.

        Args:
            query: SQL query.
            *args: Query parameters.
            batch_size: Rows per batch.

        Yields:
            Lists of row dictionaries.
        """
        ...

    async def discover_schema(self) -> list[SchemaObject]:
        """Discover tables and views using information_schema."""
        config: SQLConnectorConfig = self.config  # type: ignore

        query = """
            SELECT
                table_name,
                table_type
            FROM information_schema.tables
            WHERE table_schema = $1
            ORDER BY table_name
        """

        rows = await self._execute_query(query, config.schema_name)
        objects: list[SchemaObject] = []

        for row in rows:
            table_name = row["table_name"]
            table_type = row["table_type"].lower()
            obj_type = "view" if "view" in table_type else "table"

            # Get columns for this table
            columns = await self._get_columns(table_name)
            pk_columns = await self._get_primary_key(table_name)

            objects.append(
                SchemaObject(
                    name=table_name,
                    schema_name=config.schema_name,
                    object_type=obj_type,
                    columns=columns,
                    primary_key=pk_columns if pk_columns else None,
                    supports_incremental=obj_type == "table",
                    supports_cdc=obj_type == "table",
                )
            )

        return objects

    async def _get_columns(self, table_name: str) -> list[ColumnInfo]:
        """Get column information for a table."""
        config: SQLConnectorConfig = self.config  # type: ignore

        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                ordinal_position
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """

        rows = await self._execute_query(query, config.schema_name, table_name)
        pk_columns = set(await self._get_primary_key(table_name))

        columns: list[ColumnInfo] = []
        for row in rows:
            col_name = row["column_name"]
            db_type = row["data_type"]

            columns.append(
                ColumnInfo(
                    name=col_name,
                    data_type=db_type,
                    arrow_type=map_to_arrow_type(db_type),
                    nullable=row["is_nullable"].upper() == "YES",
                    is_primary_key=col_name in pk_columns,
                    is_cursor_field=self._is_cursor_candidate(db_type),
                )
            )

        return columns

    async def _get_primary_key(self, table_name: str) -> list[str]:
        """Get primary key columns for a table."""
        config: SQLConnectorConfig = self.config  # type: ignore

        query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = $1
                AND tc.table_name = $2
                AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
        """

        rows = await self._execute_query(query, config.schema_name, table_name)
        return [row["column_name"] for row in rows]

    def _is_cursor_candidate(self, db_type: str) -> bool:
        """Check if a column type can be used as an incremental cursor."""
        cursor_types = {
            "timestamp",
            "timestamptz",
            "timestamp without time zone",
            "timestamp with time zone",
            "datetime",
            "date",
            "int",
            "integer",
            "bigint",
            "serial",
            "bigserial",
        }
        return db_type.lower() in cursor_types

    async def get_sample_data(
        self, object_name: str, limit: int = 100
    ) -> pa.Table:
        """Get sample data from a table."""
        config: SQLConnectorConfig = self.config  # type: ignore
        full_name = f'"{config.schema_name}"."{object_name}"'

        query = f"SELECT * FROM {full_name} LIMIT {limit}"
        rows = await self._execute_query(query)

        if not rows:
            return pa.Table.from_pylist([])

        return pa.Table.from_pylist(rows)

    async def read_batch(
        self, object_name: str, state: Optional[SyncState] = None
    ) -> AsyncIterator[pa.RecordBatch]:
        """Read data in batches with optional cursor-based resumption."""
        config: SQLConnectorConfig = self.config  # type: ignore
        full_name = f'"{config.schema_name}"."{object_name}"'

        # Build query with optional cursor filter
        if state and state.cursor and state.metadata.get("cursor_field"):
            cursor_field = state.metadata["cursor_field"]
            query = f"""
                SELECT * FROM {full_name}
                WHERE "{cursor_field}" > $1
                ORDER BY "{cursor_field}"
            """
            args = (state.cursor,)
        else:
            query = f"SELECT * FROM {full_name}"
            args = ()

        async for batch_rows in self._execute_query_iter(query, *args):
            if not batch_rows:
                continue

            table = pa.Table.from_pylist(batch_rows)
            for batch in table.to_batches():
                yield batch

    async def get_sync_state(self, object_name: str) -> SyncState:
        """Get current sync state (row count for now)."""
        config: SQLConnectorConfig = self.config  # type: ignore
        full_name = f'"{config.schema_name}"."{object_name}"'

        query = f"SELECT COUNT(*) as cnt FROM {full_name}"
        rows = await self._execute_query(query)
        row_count = rows[0]["cnt"] if rows else 0

        return SyncState(
            last_sync_at=datetime.utcnow(),
            metadata={"row_count": row_count},
        )

    async def profile_data(self, object_name: str) -> DataProfile:
        """Generate statistical profile for a table."""
        config: SQLConnectorConfig = self.config  # type: ignore
        full_name = f'"{config.schema_name}"."{object_name}"'

        # Get columns
        columns = await self._get_columns(object_name)

        # Get row count
        count_result = await self._execute_query(f"SELECT COUNT(*) as cnt FROM {full_name}")
        row_count = count_result[0]["cnt"] if count_result else 0

        if row_count == 0:
            return DataProfile(
                object_name=object_name,
                row_count=0,
                column_count=len(columns),
            )

        null_counts: dict[str, int] = {}
        distinct_counts: dict[str, int] = {}
        min_values: dict[str, Any] = {}
        max_values: dict[str, Any] = {}
        sample_values: dict[str, list[Any]] = {}

        for col in columns:
            try:
                # Null count
                null_result = await self._execute_query(
                    f'SELECT COUNT(*) as cnt FROM {full_name} WHERE "{col.name}" IS NULL'
                )
                null_counts[col.name] = null_result[0]["cnt"] if null_result else 0

                # Distinct count
                distinct_result = await self._execute_query(
                    f'SELECT COUNT(DISTINCT "{col.name}") as cnt FROM {full_name}'
                )
                distinct_counts[col.name] = distinct_result[0]["cnt"] if distinct_result else 0

                # Min/Max for comparable types
                if self._is_comparable(col.data_type):
                    minmax_result = await self._execute_query(
                        f'SELECT MIN("{col.name}") as min_val, MAX("{col.name}") as max_val '
                        f"FROM {full_name}"
                    )
                    if minmax_result:
                        if minmax_result[0]["min_val"] is not None:
                            min_values[col.name] = self._serialize_value(
                                minmax_result[0]["min_val"]
                            )
                        if minmax_result[0]["max_val"] is not None:
                            max_values[col.name] = self._serialize_value(
                                minmax_result[0]["max_val"]
                            )

                # Sample values
                sample_result = await self._execute_query(
                    f'SELECT DISTINCT "{col.name}" as val FROM {full_name} '
                    f'WHERE "{col.name}" IS NOT NULL LIMIT 5'
                )
                if sample_result:
                    sample_values[col.name] = [
                        self._serialize_value(r["val"]) for r in sample_result
                    ]

            except Exception:
                # Skip columns that fail profiling
                pass

        return DataProfile(
            object_name=object_name,
            row_count=row_count,
            column_count=len(columns),
            null_counts=null_counts,
            distinct_counts=distinct_counts,
            min_values=min_values,
            max_values=max_values,
            sample_values=sample_values,
        )

    def _is_comparable(self, data_type: str) -> bool:
        """Check if type supports MIN/MAX."""
        comparable_types = {
            "int",
            "integer",
            "bigint",
            "smallint",
            "float",
            "double",
            "numeric",
            "decimal",
            "date",
            "timestamp",
            "timestamptz",
            "datetime",
            "varchar",
            "char",
            "text",
        }
        return data_type.lower().split("(")[0] in comparable_types

    def _serialize_value(self, value: Any) -> Any:
        """Convert value to JSON-serializable format."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, bytes):
            return value.hex()
        return value

    # SQL-specific utility methods

    async def execute_query(self, query: str, *args: Any) -> pa.Table:
        """
        Execute arbitrary SQL query and return as Arrow table.

        Args:
            query: SQL query.
            *args: Query parameters.

        Returns:
            PyArrow Table with results.
        """
        rows = await self._execute_query(query, *args)
        return pa.Table.from_pylist(rows) if rows else pa.Table.from_pylist([])

    async def get_table_ddl(self, table_name: str) -> str:
        """
        Get DDL for a table.

        Note: This is a simplified version. Full DDL generation
        varies by database.
        """
        columns = await self._get_columns(table_name)
        pk_cols = await self._get_primary_key(table_name)

        col_defs = []
        for col in columns:
            nullable = "" if col.nullable else " NOT NULL"
            col_defs.append(f'    "{col.name}" {col.data_type}{nullable}')

        if pk_cols:
            pk_def = f'    PRIMARY KEY ({", ".join(f\'"{c}\'' for c in pk_cols)})'
            col_defs.append(pk_def)

        config: SQLConnectorConfig = self.config  # type: ignore
        return (
            f'CREATE TABLE "{config.schema_name}"."{table_name}" (\n'
            + ",\n".join(col_defs)
            + "\n);"
        )

    async def get_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        config: SQLConnectorConfig = self.config  # type: ignore
        full_name = f'"{config.schema_name}"."{table_name}"'
        result = await self._execute_query(f"SELECT COUNT(*) as cnt FROM {full_name}")
        return result[0]["cnt"] if result else 0
