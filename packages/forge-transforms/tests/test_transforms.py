"""
Tests for transform classes.

Verifies the Transform ABC and concrete implementations work correctly.
"""

import pytest

from forge_transforms.transforms import (
    Transform,
    TransformConfig,
    TransformResult,
    TransformStatus,
    SQLTransform,
    SQLTransformConfig,
    AggregateTransform,
    AggregateConfig,
    AggregateFunction,
)
from forge_transforms.transforms.aggregate import AggregateSpec
from forge_transforms.transforms.expression import (
    ColumnExpression,
    LiteralExpression,
    FunctionExpression,
    ExpressionTransform,
    ExpressionTransformConfig,
)


class TestTransformConfig:
    """Test TransformConfig validation and behavior."""

    def test_basic_config_creation(self):
        """Test creating a basic transform config."""
        config = TransformConfig(
            transform_id="test-transform",
            name="Test Transform",
            description="A test transform",
        )
        assert config.transform_id == "test-transform"
        assert config.name == "Test Transform"
        assert config.timeout_seconds == 1800  # default

    def test_config_with_tags(self):
        """Test config with tags."""
        config = TransformConfig(
            transform_id="test",
            tags=["etl", "sales"],
        )
        assert config.tags == ["etl", "sales"]


class TestSQLTransform:
    """Test SQL transform implementation."""

    def test_sql_transform_creation(self):
        """Test creating a SQL transform."""
        config = SQLTransformConfig(
            transform_id="filter-active",
            sql="SELECT * FROM input WHERE active = true",
        )
        transform = SQLTransform(config)

        assert transform.transform_type == "sql"
        assert transform.sql == "SELECT * FROM input WHERE active = true"

    def test_sql_transform_validation_empty_sql(self):
        """Test validation fails for empty SQL."""
        config = SQLTransformConfig(
            transform_id="test",
            sql="   ",
        )
        transform = SQLTransform(config)
        errors = transform.validate()

        assert len(errors) > 0
        assert "cannot be empty" in errors[0].lower()

    def test_sql_transform_validation_dangerous_sql(self):
        """Test validation warns about dangerous SQL patterns."""
        config = SQLTransformConfig(
            transform_id="test",
            sql="DROP TABLE users",
        )
        transform = SQLTransform(config)
        errors = transform.validate()

        assert len(errors) > 0
        assert "dangerous" in errors[0].lower()

    def test_sql_transform_to_sql(self):
        """Test SQL transform returns its SQL."""
        sql = "SELECT id, name FROM users"
        config = SQLTransformConfig(transform_id="test", sql=sql)
        transform = SQLTransform(config)

        assert transform.to_sql() == sql


class TestExpressions:
    """Test expression classes."""

    def test_column_expression(self):
        """Test column expression to SQL."""
        col = ColumnExpression("price")
        assert col.to_sql() == "price"
        assert col.get_columns() == {"price"}

    def test_column_expression_with_alias(self):
        """Test column expression with table alias."""
        col = ColumnExpression("price", table_alias="t")
        assert col.to_sql() == "t.price"

    def test_literal_expression_int(self):
        """Test integer literal."""
        lit = LiteralExpression(42)
        assert lit.to_sql() == "42"
        assert lit.get_columns() == set()

    def test_literal_expression_string(self):
        """Test string literal with escaping."""
        lit = LiteralExpression("hello")
        assert lit.to_sql() == "'hello'"

        lit2 = LiteralExpression("it's")
        assert lit2.to_sql() == "'it''s'"

    def test_literal_expression_bool(self):
        """Test boolean literals."""
        assert LiteralExpression(True).to_sql() == "TRUE"
        assert LiteralExpression(False).to_sql() == "FALSE"

    def test_literal_expression_null(self):
        """Test NULL literal."""
        assert LiteralExpression(None).to_sql() == "NULL"

    def test_function_expression(self):
        """Test function expression."""
        func = FunctionExpression("UPPER", ColumnExpression("name"))
        assert func.to_sql() == "UPPER(name)"

    def test_binary_operator_expression(self):
        """Test binary operator expression."""
        expr = FunctionExpression(
            ">",
            ColumnExpression("price"),
            LiteralExpression(100),
        )
        assert expr.to_sql() == "(price > 100)"

    def test_nested_expression(self):
        """Test nested expression."""
        # (price * quantity) > 1000
        expr = FunctionExpression(
            ">",
            FunctionExpression(
                "*",
                ColumnExpression("price"),
                ColumnExpression("quantity"),
            ),
            LiteralExpression(1000),
        )
        assert expr.to_sql() == "((price * quantity) > 1000)"
        assert expr.get_columns() == {"price", "quantity"}


class TestExpressionTransform:
    """Test expression-based transform."""

    def test_expression_transform_to_sql(self):
        """Test expression transform generates correct SQL."""
        config = ExpressionTransformConfig(
            transform_id="test",
            select_expressions={
                "id": ColumnExpression("id"),
                "total": FunctionExpression(
                    "*",
                    ColumnExpression("price"),
                    ColumnExpression("qty"),
                ),
            },
            filter_expression=FunctionExpression(
                ">", ColumnExpression("qty"), LiteralExpression(0)
            ),
            input_table_name="orders",
        )
        transform = ExpressionTransform(config)
        sql = transform.to_sql()

        assert "SELECT" in sql
        assert "FROM orders" in sql
        assert "WHERE" in sql
        assert "(qty > 0)" in sql

    def test_expression_transform_validation(self):
        """Test expression transform validation."""
        # Empty select expressions should fail
        config = ExpressionTransformConfig(
            transform_id="test",
            select_expressions={},
        )
        transform = ExpressionTransform(config)
        errors = transform.validate()

        assert len(errors) > 0
        assert "SELECT" in errors[0]


class TestAggregateTransform:
    """Test aggregate transform."""

    def test_aggregate_spec_to_sql(self):
        """Test aggregate spec generates correct SQL."""
        spec = AggregateSpec(
            function=AggregateFunction.SUM,
            column="amount",
            alias="total_amount",
        )
        assert spec.to_sql() == "SUM(amount) AS total_amount"

    def test_aggregate_spec_count_distinct(self):
        """Test COUNT DISTINCT aggregate."""
        spec = AggregateSpec(
            function=AggregateFunction.COUNT_DISTINCT,
            column="customer_id",
            alias="unique_customers",
        )
        assert spec.to_sql() == "COUNT(DISTINCT customer_id) AS unique_customers"

    def test_aggregate_transform_to_sql(self):
        """Test aggregate transform generates correct SQL."""
        config = AggregateConfig(
            transform_id="sales-summary",
            aggregations=[
                AggregateSpec(AggregateFunction.SUM, "amount", "total"),
                AggregateSpec(AggregateFunction.COUNT, "*", "count"),
            ],
            group_by=["region"],
            order_by=[("total", "DESC")],
            limit=10,
            input_table_name="sales",
        )
        transform = AggregateTransform(config)
        sql = transform.to_sql()

        assert "SELECT region" in sql
        assert "SUM(amount) AS total" in sql
        assert "COUNT(*) AS count" in sql
        assert "FROM sales" in sql
        assert "GROUP BY region" in sql
        assert "ORDER BY total DESC" in sql
        assert "LIMIT 10" in sql


class TestTransformResult:
    """Test TransformResult behavior."""

    def test_successful_result(self):
        """Test successful result properties."""
        result = TransformResult(status=TransformStatus.COMPLETED)
        assert result.is_success is True

    def test_failed_result(self):
        """Test failed result properties."""
        result = TransformResult(
            status=TransformStatus.FAILED,
            error="Something went wrong",
        )
        assert result.is_success is False
        assert result.error == "Something went wrong"

    def test_row_count_no_data(self):
        """Test row count with no data."""
        result = TransformResult(status=TransformStatus.COMPLETED)
        assert result.row_count == 0
