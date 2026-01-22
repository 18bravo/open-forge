"""
SQL Transform

Provides SQL-based data transformations using DataFusion's SQL execution.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

import pyarrow as pa
from pydantic import Field

from forge_transforms.transforms.base import (
    Transform,
    TransformConfig,
    TransformResult,
    TransformStatus,
)

if TYPE_CHECKING:
    from forge_transforms.engine.protocol import TransformEngine


class SQLTransformConfig(TransformConfig):
    """Configuration for SQL transforms.

    Attributes:
        sql: The SQL query to execute.
        input_table_name: Name to use for input data in the query.
        parameters: Optional query parameters.
    """

    sql: str = Field(..., description="SQL query to execute")
    input_table_name: str = Field("input", description="Table name for input data")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Query parameters",
    )


class SQLTransform(Transform):
    """SQL-based data transformation.

    Executes a SQL query against input data using the DataFusion engine.
    The input data is registered as a table with the configured name,
    and the SQL query is executed against it.

    Example:
        ```python
        config = SQLTransformConfig(
            transform_id="filter_active",
            sql="SELECT * FROM input WHERE status = 'active'",
        )
        transform = SQLTransform(config)

        result = await transform.execute(engine, input_data)
        if result.is_success:
            print(f"Filtered to {result.row_count} rows")
        ```
    """

    def __init__(self, config: SQLTransformConfig):
        """Initialize the SQL transform.

        Args:
            config: The SQL transform configuration.
        """
        super().__init__(config)
        self._sql_config = config

    @property
    def transform_type(self) -> str:
        """Get the transform type identifier."""
        return "sql"

    @property
    def sql(self) -> str:
        """Get the SQL query."""
        return self._sql_config.sql

    async def execute(
        self,
        engine: "TransformEngine",
        input_data: pa.Table | None = None,
    ) -> TransformResult:
        """Execute the SQL transform.

        Args:
            engine: The transform engine to use.
            input_data: Optional input data to transform.

        Returns:
            TransformResult with the query results.
        """
        started_at = datetime.utcnow()

        try:
            # Register input data if provided
            if input_data is not None:
                engine.register_table(
                    self._sql_config.input_table_name,
                    input_data,
                )

            # Execute the SQL
            result = await engine.execute_sql(
                self._sql_config.sql,
                parameters=self._sql_config.parameters,
            )

            completed_at = datetime.utcnow()

            if result.is_success:
                return self._create_result(
                    status=TransformStatus.COMPLETED,
                    data=result.data,
                    started_at=started_at,
                    completed_at=completed_at,
                    rows_processed=result.metrics.rows_processed,
                    execution_time_ms=result.metrics.execution_time_ms,
                )
            else:
                return self._create_result(
                    status=TransformStatus.FAILED,
                    error=result.error,
                    started_at=started_at,
                    completed_at=completed_at,
                )

        except Exception as e:
            return self._create_result(
                status=TransformStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow(),
            )

    def validate(self) -> list[str]:
        """Validate the SQL transform configuration.

        Returns:
            List of validation errors. Empty if valid.
        """
        errors: list[str] = []

        if not self._sql_config.sql.strip():
            errors.append("SQL query cannot be empty")

        # Basic SQL injection prevention (simple checks)
        sql_lower = self._sql_config.sql.lower()
        dangerous_patterns = ["drop table", "drop database", "truncate", "delete from"]
        for pattern in dangerous_patterns:
            if pattern in sql_lower:
                errors.append(f"Potentially dangerous SQL pattern detected: {pattern}")

        return errors

    def to_sql(self) -> str:
        """Get the SQL representation.

        Returns:
            The SQL query string.
        """
        return self._sql_config.sql


def create_sql_transform(
    transform_id: str,
    sql: str,
    name: str = "",
    input_table_name: str = "input",
    **kwargs: Any,
) -> SQLTransform:
    """Factory function to create a SQL transform.

    Args:
        transform_id: Unique identifier for the transform.
        sql: The SQL query to execute.
        name: Optional human-readable name.
        input_table_name: Name for the input table.
        **kwargs: Additional configuration options.

    Returns:
        A configured SQLTransform instance.

    Example:
        ```python
        transform = create_sql_transform(
            transform_id="aggregate_sales",
            sql="SELECT region, SUM(amount) as total FROM sales GROUP BY region",
            input_table_name="sales",
        )
        ```
    """
    config = SQLTransformConfig(
        transform_id=transform_id,
        sql=sql,
        name=name,
        input_table_name=input_table_name,
        **kwargs,
    )
    return SQLTransform(config)
