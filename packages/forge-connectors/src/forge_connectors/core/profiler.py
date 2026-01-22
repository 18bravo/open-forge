"""
Data profiling utilities.

Provides functionality for computing statistical profiles of data objects,
including null counts, distinct counts, min/max values, and sample values.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from forge_connectors.core.base import DataProfile

logger = logging.getLogger(__name__)


class DataProfiler(ABC):
    """
    Abstract base for data profiling implementations.

    Subclasses implement database-specific profiling queries.
    """

    @abstractmethod
    async def profile(self, object_name: str) -> DataProfile:
        """
        Generate a statistical profile for an object.

        Args:
            object_name: Name of the object to profile.

        Returns:
            DataProfile with computed statistics.
        """
        ...


class SQLDataProfiler(DataProfiler):
    """
    Data profiler for SQL databases.

    Generates profiles using SQL queries against the source database.
    """

    def __init__(
        self,
        execute_query: Any,  # Callable to execute SQL queries
        get_columns: Any,  # Callable to get column info
        schema: str = "public",
        sample_size: int = 5,
    ):
        """
        Initialize SQL data profiler.

        Args:
            execute_query: Async callable that executes SQL and returns rows.
            get_columns: Async callable that returns column metadata.
            schema: Schema name.
            sample_size: Number of sample values to collect per column.
        """
        self.execute_query = execute_query
        self.get_columns = get_columns
        self.schema = schema
        self.sample_size = sample_size

    async def profile(self, object_name: str) -> DataProfile:
        """Generate profile using SQL queries."""
        full_name = f"{self.schema}.{object_name}" if self.schema else object_name

        # Get column info
        columns = await self.get_columns(object_name)
        column_names = [c.name for c in columns]

        # Get row count
        count_query = f"SELECT COUNT(*) as cnt FROM {full_name}"
        count_result = await self.execute_query(count_query)
        row_count = count_result[0]["cnt"] if count_result else 0

        if row_count == 0:
            return DataProfile(
                object_name=object_name,
                row_count=0,
                column_count=len(column_names),
                profiled_at=datetime.utcnow(),
            )

        # Build profiling queries for each column
        null_counts: dict[str, int] = {}
        distinct_counts: dict[str, int] = {}
        min_values: dict[str, Any] = {}
        max_values: dict[str, Any] = {}
        sample_values: dict[str, list[Any]] = {}

        for col in column_names:
            try:
                # Null count
                null_query = f'SELECT COUNT(*) as cnt FROM {full_name} WHERE "{col}" IS NULL'
                null_result = await self.execute_query(null_query)
                null_counts[col] = null_result[0]["cnt"] if null_result else 0

                # Distinct count (approximate for large tables)
                distinct_query = f'SELECT COUNT(DISTINCT "{col}") as cnt FROM {full_name}'
                distinct_result = await self.execute_query(distinct_query)
                distinct_counts[col] = distinct_result[0]["cnt"] if distinct_result else 0

                # Min/Max (only for comparable types)
                col_info = next((c for c in columns if c.name == col), None)
                if col_info and self._is_comparable(col_info.data_type):
                    minmax_query = f'SELECT MIN("{col}") as min_val, MAX("{col}") as max_val FROM {full_name}'
                    minmax_result = await self.execute_query(minmax_query)
                    if minmax_result:
                        min_val = minmax_result[0]["min_val"]
                        max_val = minmax_result[0]["max_val"]
                        if min_val is not None:
                            min_values[col] = self._serialize_value(min_val)
                        if max_val is not None:
                            max_values[col] = self._serialize_value(max_val)

                # Sample values
                sample_query = f"""
                    SELECT DISTINCT "{col}" as val
                    FROM {full_name}
                    WHERE "{col}" IS NOT NULL
                    LIMIT {self.sample_size}
                """
                sample_result = await self.execute_query(sample_query)
                if sample_result:
                    sample_values[col] = [
                        self._serialize_value(r["val"]) for r in sample_result
                    ]

            except Exception as e:
                logger.warning(f"Failed to profile column {col}: {e}")

        return DataProfile(
            object_name=object_name,
            row_count=row_count,
            column_count=len(column_names),
            null_counts=null_counts,
            distinct_counts=distinct_counts,
            min_values=min_values,
            max_values=max_values,
            sample_values=sample_values,
            profiled_at=datetime.utcnow(),
        )

    def _is_comparable(self, data_type: str) -> bool:
        """Check if a type supports MIN/MAX operations."""
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
