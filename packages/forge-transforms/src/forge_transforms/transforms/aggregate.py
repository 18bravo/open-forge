"""
Aggregate Transforms

Provides aggregation-based data transformations with common aggregate
functions and grouping capabilities.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, TYPE_CHECKING

import pyarrow as pa
from pydantic import Field

from forge_transforms.transforms.base import (
    Transform,
    TransformConfig,
    TransformResult,
    TransformStatus,
)
from forge_transforms.transforms.expression import Expression, ColumnExpression

if TYPE_CHECKING:
    from forge_transforms.engine.protocol import TransformEngine


class AggregateFunction(str, Enum):
    """Standard aggregate functions."""

    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    FIRST = "FIRST"
    LAST = "LAST"
    STDDEV = "STDDEV"
    VARIANCE = "VARIANCE"


class AggregateSpec:
    """Specification for a single aggregation.

    Attributes:
        function: The aggregate function to apply.
        column: The column to aggregate.
        alias: The output column name.
        filter_expr: Optional filter expression for this aggregation.
    """

    def __init__(
        self,
        function: AggregateFunction,
        column: str,
        alias: str | None = None,
        filter_expr: Expression | None = None,
    ):
        """Initialize aggregate specification.

        Args:
            function: The aggregate function.
            column: The column to aggregate.
            alias: Optional output alias (defaults to func_column).
            filter_expr: Optional FILTER clause expression.
        """
        self.function = function
        self.column = column
        self.alias = alias or f"{function.value.lower()}_{column}"
        self.filter_expr = filter_expr

    def to_sql(self) -> str:
        """Convert to SQL aggregate expression.

        Returns:
            SQL string for this aggregation.
        """
        if self.function == AggregateFunction.COUNT_DISTINCT:
            expr = f"COUNT(DISTINCT {self.column})"
        else:
            expr = f"{self.function.value}({self.column})"

        if self.filter_expr:
            expr = f"{expr} FILTER (WHERE {self.filter_expr.to_sql()})"

        return f"{expr} AS {self.alias}"


class AggregateConfig(TransformConfig):
    """Configuration for aggregate transforms.

    Attributes:
        aggregations: List of aggregate specifications.
        group_by: Columns to group by.
        having: Optional HAVING clause expression.
        order_by: Optional ORDER BY specifications.
        limit: Optional LIMIT value.
        input_table_name: Name for the input table.
    """

    aggregations: list[AggregateSpec] = Field(
        default_factory=list,
        description="Aggregate specifications",
    )
    group_by: list[str] = Field(
        default_factory=list,
        description="GROUP BY columns",
    )
    having: Expression | None = Field(
        None,
        description="HAVING clause expression",
    )
    order_by: list[tuple[str, str]] = Field(
        default_factory=list,
        description="ORDER BY (column, ASC/DESC)",
    )
    limit: int | None = Field(None, ge=0, description="LIMIT value")
    input_table_name: str = Field("input", description="Input table name")

    model_config = {"arbitrary_types_allowed": True}


class AggregateTransform(Transform):
    """Aggregation-based data transformation.

    Provides a high-level interface for creating aggregate queries
    with grouping, filtering, and ordering.

    Example:
        ```python
        config = AggregateConfig(
            transform_id="sales_by_region",
            aggregations=[
                AggregateSpec(AggregateFunction.SUM, "amount", "total_sales"),
                AggregateSpec(AggregateFunction.COUNT, "*", "order_count"),
                AggregateSpec(AggregateFunction.AVG, "amount", "avg_order"),
            ],
            group_by=["region", "product_category"],
            order_by=[("total_sales", "DESC")],
            limit=100,
        )
        transform = AggregateTransform(config)
        result = await transform.execute(engine, sales_data)
        ```
    """

    def __init__(self, config: AggregateConfig):
        """Initialize the aggregate transform.

        Args:
            config: The aggregate transform configuration.
        """
        super().__init__(config)
        self._agg_config = config

    @property
    def transform_type(self) -> str:
        """Get the transform type identifier."""
        return "aggregate"

    async def execute(
        self,
        engine: "TransformEngine",
        input_data: pa.Table | None = None,
    ) -> TransformResult:
        """Execute the aggregate transform.

        Args:
            engine: The transform engine to use.
            input_data: Optional input data to transform.

        Returns:
            TransformResult with the aggregated results.
        """
        started_at = datetime.utcnow()

        try:
            # Validate first
            errors = self.validate()
            if errors:
                return self._create_result(
                    status=TransformStatus.FAILED,
                    error=f"Validation failed: {'; '.join(errors)}",
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                )

            # Register input data if provided
            if input_data is not None:
                engine.register_table(
                    self._agg_config.input_table_name,
                    input_data,
                )

            # Convert to SQL and execute
            sql = self.to_sql()
            result = await engine.execute_sql(sql)

            completed_at = datetime.utcnow()

            if result.is_success:
                return self._create_result(
                    status=TransformStatus.COMPLETED,
                    data=result.data,
                    started_at=started_at,
                    completed_at=completed_at,
                    rows_processed=result.metrics.rows_processed,
                    groups_created=result.data.num_rows if result.data else 0,
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
        """Validate the aggregate transform configuration.

        Returns:
            List of validation errors. Empty if valid.
        """
        errors: list[str] = []

        if not self._agg_config.aggregations:
            errors.append("At least one aggregation is required")

        return errors

    def to_sql(self) -> str:
        """Convert the aggregate transform to SQL.

        Returns:
            SQL query string.
        """
        parts: list[str] = []

        # Build SELECT clause
        select_items: list[str] = []

        # Add group by columns first
        for col in self._agg_config.group_by:
            select_items.append(col)

        # Add aggregations
        for agg in self._agg_config.aggregations:
            select_items.append(agg.to_sql())

        parts.append(f"SELECT {', '.join(select_items)}")

        # FROM clause
        parts.append(f"FROM {self._agg_config.input_table_name}")

        # GROUP BY clause
        if self._agg_config.group_by:
            parts.append(f"GROUP BY {', '.join(self._agg_config.group_by)}")

        # HAVING clause
        if self._agg_config.having:
            parts.append(f"HAVING {self._agg_config.having.to_sql()}")

        # ORDER BY clause
        if self._agg_config.order_by:
            order_items = [f"{col} {direction}" for col, direction in self._agg_config.order_by]
            parts.append(f"ORDER BY {', '.join(order_items)}")

        # LIMIT clause
        if self._agg_config.limit is not None:
            parts.append(f"LIMIT {self._agg_config.limit}")

        return " ".join(parts)


def create_aggregate_transform(
    transform_id: str,
    aggregations: list[tuple[AggregateFunction, str, str | None]],
    group_by: list[str] | None = None,
    input_table_name: str = "input",
    **kwargs: Any,
) -> AggregateTransform:
    """Factory function to create an aggregate transform.

    Args:
        transform_id: Unique identifier for the transform.
        aggregations: List of (function, column, alias) tuples.
        group_by: Optional list of columns to group by.
        input_table_name: Name for the input table.
        **kwargs: Additional configuration options.

    Returns:
        A configured AggregateTransform instance.

    Example:
        ```python
        transform = create_aggregate_transform(
            transform_id="summary",
            aggregations=[
                (AggregateFunction.SUM, "amount", "total"),
                (AggregateFunction.COUNT, "*", "count"),
            ],
            group_by=["category"],
        )
        ```
    """
    agg_specs = [
        AggregateSpec(func, col, alias)
        for func, col, alias in aggregations
    ]

    config = AggregateConfig(
        transform_id=transform_id,
        aggregations=agg_specs,
        group_by=group_by or [],
        input_table_name=input_table_name,
        **kwargs,
    )
    return AggregateTransform(config)
