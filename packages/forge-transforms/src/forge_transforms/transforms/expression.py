"""
Expression-Based Transforms

Provides expression-based data transformations using a composable
expression tree that compiles to SQL.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
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


class Expression(ABC):
    """Abstract base class for expressions.

    Expressions form a tree that can be compiled to SQL. They support
    common operations like arithmetic, comparisons, and function calls.

    Example:
        ```python
        # Build expression: (price * quantity) > 1000
        expr = FunctionExpression(
            ">",
            FunctionExpression("*", ColumnExpression("price"), ColumnExpression("quantity")),
            LiteralExpression(1000),
        )
        sql = expr.to_sql()  # "(price * quantity) > 1000"
        ```
    """

    @abstractmethod
    def to_sql(self) -> str:
        """Convert the expression to SQL.

        Returns:
            SQL string representation of the expression.
        """
        ...

    @abstractmethod
    def get_columns(self) -> set[str]:
        """Get all column references in this expression.

        Returns:
            Set of column names referenced by this expression.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_sql()})"


class ColumnExpression(Expression):
    """Expression referencing a column.

    Example:
        ```python
        col = ColumnExpression("price")
        col.to_sql()  # "price"

        # With table alias
        col = ColumnExpression("price", table_alias="t")
        col.to_sql()  # "t.price"
        ```
    """

    def __init__(self, column_name: str, table_alias: str | None = None):
        """Initialize column expression.

        Args:
            column_name: The column name.
            table_alias: Optional table alias.
        """
        self.column_name = column_name
        self.table_alias = table_alias

    def to_sql(self) -> str:
        """Convert to SQL column reference."""
        if self.table_alias:
            return f"{self.table_alias}.{self.column_name}"
        return self.column_name

    def get_columns(self) -> set[str]:
        """Get columns - returns this column."""
        return {self.column_name}


class LiteralExpression(Expression):
    """Expression representing a literal value.

    Example:
        ```python
        LiteralExpression(42).to_sql()       # "42"
        LiteralExpression("hello").to_sql()  # "'hello'"
        LiteralExpression(True).to_sql()     # "TRUE"
        LiteralExpression(None).to_sql()     # "NULL"
        ```
    """

    def __init__(self, value: Any):
        """Initialize literal expression.

        Args:
            value: The literal value.
        """
        self.value = value

    def to_sql(self) -> str:
        """Convert to SQL literal."""
        if self.value is None:
            return "NULL"
        if isinstance(self.value, bool):
            return "TRUE" if self.value else "FALSE"
        if isinstance(self.value, str):
            # Escape single quotes
            escaped = self.value.replace("'", "''")
            return f"'{escaped}'"
        if isinstance(self.value, (int, float)):
            return str(self.value)
        return str(self.value)

    def get_columns(self) -> set[str]:
        """Get columns - literals have no columns."""
        return set()


class FunctionExpression(Expression):
    """Expression representing a function call or operator.

    Supports both SQL functions and operators.

    Example:
        ```python
        # Function call: UPPER(name)
        FunctionExpression("UPPER", ColumnExpression("name")).to_sql()

        # Binary operator: price > 100
        FunctionExpression(">", ColumnExpression("price"), LiteralExpression(100)).to_sql()

        # Arithmetic: price * 1.1
        FunctionExpression("*", ColumnExpression("price"), LiteralExpression(1.1)).to_sql()
        ```
    """

    # Operators that should be formatted as infix
    INFIX_OPERATORS = {
        "+", "-", "*", "/", "%",
        "=", "!=", "<>", "<", ">", "<=", ">=",
        "AND", "OR",
        "LIKE", "ILIKE", "IN", "NOT IN",
    }

    def __init__(self, function_name: str, *args: Expression):
        """Initialize function expression.

        Args:
            function_name: The function or operator name.
            *args: The function arguments.
        """
        self.function_name = function_name.upper()
        self.args = list(args)

    def to_sql(self) -> str:
        """Convert to SQL function call or operator expression."""
        if self.function_name in self.INFIX_OPERATORS and len(self.args) == 2:
            # Binary infix operator
            left = self.args[0].to_sql()
            right = self.args[1].to_sql()
            return f"({left} {self.function_name} {right})"

        # Standard function call
        args_sql = ", ".join(arg.to_sql() for arg in self.args)
        return f"{self.function_name}({args_sql})"

    def get_columns(self) -> set[str]:
        """Get all columns from all arguments."""
        columns: set[str] = set()
        for arg in self.args:
            columns.update(arg.get_columns())
        return columns


class ExpressionTransformConfig(TransformConfig):
    """Configuration for expression transforms.

    Attributes:
        select_expressions: Expressions for SELECT clause (alias -> expression).
        filter_expression: Optional WHERE clause expression.
        group_by_columns: Optional GROUP BY columns.
        having_expression: Optional HAVING clause expression.
        order_by: Optional ORDER BY specifications.
        limit: Optional LIMIT value.
        input_table_name: Name for the input table.
    """

    select_expressions: dict[str, Expression] = Field(
        default_factory=dict,
        description="SELECT expressions (alias -> expression)",
    )
    filter_expression: Expression | None = Field(
        None, description="WHERE clause expression"
    )
    group_by_columns: list[str] = Field(
        default_factory=list, description="GROUP BY columns"
    )
    having_expression: Expression | None = Field(
        None, description="HAVING clause expression"
    )
    order_by: list[tuple[str, str]] = Field(
        default_factory=list, description="ORDER BY (column, ASC/DESC)"
    )
    limit: int | None = Field(None, ge=0, description="LIMIT value")
    input_table_name: str = Field("input", description="Input table name")

    model_config = {"arbitrary_types_allowed": True}


class ExpressionTransform(Transform):
    """Expression-based data transformation.

    Builds SQL queries from expression trees, providing a programmatic
    way to construct transforms without writing raw SQL.

    Example:
        ```python
        config = ExpressionTransformConfig(
            transform_id="calc_total",
            select_expressions={
                "id": ColumnExpression("id"),
                "total": FunctionExpression("*",
                    ColumnExpression("price"),
                    ColumnExpression("quantity")
                ),
            },
            filter_expression=FunctionExpression(">",
                ColumnExpression("quantity"),
                LiteralExpression(0)
            ),
        )
        transform = ExpressionTransform(config)
        result = await transform.execute(engine, data)
        ```
    """

    def __init__(self, config: ExpressionTransformConfig):
        """Initialize the expression transform.

        Args:
            config: The expression transform configuration.
        """
        super().__init__(config)
        self._expr_config = config

    @property
    def transform_type(self) -> str:
        """Get the transform type identifier."""
        return "expression"

    async def execute(
        self,
        engine: "TransformEngine",
        input_data: pa.Table | None = None,
    ) -> TransformResult:
        """Execute the expression transform.

        Args:
            engine: The transform engine to use.
            input_data: Optional input data to transform.

        Returns:
            TransformResult with the query results.
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
                    self._expr_config.input_table_name,
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
        """Validate the expression transform configuration.

        Returns:
            List of validation errors. Empty if valid.
        """
        errors: list[str] = []

        if not self._expr_config.select_expressions:
            errors.append("At least one SELECT expression is required")

        return errors

    def to_sql(self) -> str:
        """Convert the expression transform to SQL.

        Returns:
            SQL query string.
        """
        parts: list[str] = []

        # SELECT clause
        if self._expr_config.select_expressions:
            select_items = [
                f"{expr.to_sql()} AS {alias}"
                for alias, expr in self._expr_config.select_expressions.items()
            ]
            parts.append(f"SELECT {', '.join(select_items)}")
        else:
            parts.append("SELECT *")

        # FROM clause
        parts.append(f"FROM {self._expr_config.input_table_name}")

        # WHERE clause
        if self._expr_config.filter_expression:
            parts.append(f"WHERE {self._expr_config.filter_expression.to_sql()}")

        # GROUP BY clause
        if self._expr_config.group_by_columns:
            parts.append(f"GROUP BY {', '.join(self._expr_config.group_by_columns)}")

        # HAVING clause
        if self._expr_config.having_expression:
            parts.append(f"HAVING {self._expr_config.having_expression.to_sql()}")

        # ORDER BY clause
        if self._expr_config.order_by:
            order_items = [f"{col} {direction}" for col, direction in self._expr_config.order_by]
            parts.append(f"ORDER BY {', '.join(order_items)}")

        # LIMIT clause
        if self._expr_config.limit is not None:
            parts.append(f"LIMIT {self._expr_config.limit}")

        return " ".join(parts)
