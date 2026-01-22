"""
Schema discovery utilities.

Provides common functionality for discovering and introspecting
data source schemas across different connector types.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from forge_connectors.core.base import ColumnInfo, SchemaObject

logger = logging.getLogger(__name__)


# Arrow type mapping from common database types
ARROW_TYPE_MAP: dict[str, str] = {
    # Integer types
    "int": "int64",
    "integer": "int64",
    "int2": "int16",
    "int4": "int32",
    "int8": "int64",
    "smallint": "int16",
    "bigint": "int64",
    "serial": "int32",
    "bigserial": "int64",
    # Float types
    "float": "float64",
    "float4": "float32",
    "float8": "float64",
    "real": "float32",
    "double": "float64",
    "double precision": "float64",
    "numeric": "decimal128",
    "decimal": "decimal128",
    # String types
    "char": "string",
    "varchar": "string",
    "character varying": "string",
    "text": "string",
    "string": "string",
    "nvarchar": "string",
    "nchar": "string",
    # Boolean
    "bool": "bool",
    "boolean": "bool",
    # Date/Time types
    "date": "date32",
    "time": "time64[us]",
    "timestamp": "timestamp[us]",
    "timestamp without time zone": "timestamp[us]",
    "timestamp with time zone": "timestamp[us, tz=UTC]",
    "timestamptz": "timestamp[us, tz=UTC]",
    "datetime": "timestamp[us]",
    # Binary types
    "bytea": "binary",
    "blob": "binary",
    "binary": "binary",
    "varbinary": "binary",
    # JSON types
    "json": "string",
    "jsonb": "string",
    # UUID
    "uuid": "string",
    # Arrays (simplified to string for now)
    "array": "string",
}


def map_to_arrow_type(db_type: str) -> str:
    """
    Map a database type to an Arrow type.

    Args:
        db_type: Database-specific type name.

    Returns:
        Corresponding Arrow type string.
    """
    # Normalize type name
    normalized = db_type.lower().strip()

    # Handle parameterized types (e.g., "varchar(255)", "numeric(10,2)")
    if "(" in normalized:
        normalized = normalized.split("(")[0].strip()

    # Handle array types
    if normalized.endswith("[]"):
        return "list<" + map_to_arrow_type(normalized[:-2]) + ">"

    return ARROW_TYPE_MAP.get(normalized, "string")


class SchemaDiscovery(ABC):
    """
    Abstract base for schema discovery implementations.

    Each connector category (SQL, API, etc.) implements its own
    discovery strategy while sharing common utilities.
    """

    @abstractmethod
    async def discover_objects(self) -> list[SchemaObject]:
        """
        Discover all available objects in the data source.

        Returns:
            List of SchemaObject descriptions.
        """
        ...

    @abstractmethod
    async def get_object_schema(self, object_name: str) -> SchemaObject:
        """
        Get detailed schema for a specific object.

        Args:
            object_name: Name of the object.

        Returns:
            SchemaObject with column details.
        """
        ...


class SQLSchemaDiscovery(SchemaDiscovery):
    """
    Schema discovery for SQL databases using information_schema.

    Works with most SQL databases that support the ANSI information_schema.
    """

    def __init__(
        self,
        execute_query: Any,  # Callable to execute SQL queries
        catalog: str | None = None,
        schema: str = "public",
    ):
        """
        Initialize SQL schema discovery.

        Args:
            execute_query: Async callable that executes SQL and returns rows.
            catalog: Database/catalog name (optional).
            schema: Schema name to discover (default: "public").
        """
        self.execute_query = execute_query
        self.catalog = catalog
        self.schema = schema

    async def discover_objects(self) -> list[SchemaObject]:
        """Discover tables and views using information_schema."""
        query = """
            SELECT
                table_name,
                table_type
            FROM information_schema.tables
            WHERE table_schema = $1
            ORDER BY table_name
        """

        rows = await self.execute_query(query, self.schema)
        objects: list[SchemaObject] = []

        for row in rows:
            table_name = row["table_name"]
            table_type = row["table_type"].lower()
            obj_type = "view" if "view" in table_type else "table"

            objects.append(
                SchemaObject(
                    name=table_name,
                    schema_name=self.schema,
                    object_type=obj_type,
                    columns=[],  # Will be populated on detailed discovery
                    supports_incremental=obj_type == "table",
                )
            )

        return objects

    async def get_object_schema(self, object_name: str) -> SchemaObject:
        """Get detailed schema for a table/view."""
        # Get columns
        column_query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """

        column_rows = await self.execute_query(column_query, self.schema, object_name)

        # Get primary key columns
        pk_query = """
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

        pk_rows = await self.execute_query(pk_query, self.schema, object_name)
        pk_columns = {row["column_name"] for row in pk_rows}

        columns: list[ColumnInfo] = []
        for row in column_rows:
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

        # Check object type
        type_query = """
            SELECT table_type
            FROM information_schema.tables
            WHERE table_schema = $1 AND table_name = $2
        """
        type_rows = await self.execute_query(type_query, self.schema, object_name)
        obj_type = "table"
        if type_rows:
            obj_type = "view" if "view" in type_rows[0]["table_type"].lower() else "table"

        return SchemaObject(
            name=object_name,
            schema_name=self.schema,
            object_type=obj_type,
            columns=columns,
            primary_key=list(pk_columns) if pk_columns else None,
            supports_incremental=obj_type == "table",
            supports_cdc=obj_type == "table",  # May need connector-specific check
        )

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
