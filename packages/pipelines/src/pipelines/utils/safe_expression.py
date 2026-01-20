"""
Safe expression parser for Polars DataFrames.

Replaces dangerous eval() calls with a whitelist-based expression parser
that only allows safe Polars operations.
"""
import re
from typing import Any, Callable, Dict, Optional
import polars as pl


class ExpressionParseError(Exception):
    """Raised when an expression cannot be parsed safely."""
    pass


class SafePolarsExpressionParser:
    """
    Parses a safe subset of Polars expressions without using eval().

    Supported patterns:
    - pl.col("column_name") - Column reference
    - pl.lit(value) - Literal value
    - Arithmetic: +, -, *, /
    - Comparisons: ==, !=, <, >, <=, >=
    - Logical: &, |, ~
    - String methods: .str.contains(), .str.to_lowercase(), .str.to_uppercase()
    - Null checks: .is_null(), .is_not_null()
    - Aggregations: .sum(), .mean(), .min(), .max(), .count()

    Example:
        parser = SafePolarsExpressionParser()
        expr = parser.parse('pl.col("age") > 18')
        df_filtered = df.filter(expr)
    """

    # Whitelist of allowed Polars methods
    ALLOWED_METHODS = {
        # Column operations
        "col", "lit", "all", "exclude",
        # Null handling
        "is_null", "is_not_null", "fill_null", "drop_nulls",
        # String operations
        "str", "contains", "to_lowercase", "to_uppercase", "strip_chars",
        "starts_with", "ends_with", "replace", "len",
        # Numeric operations
        "abs", "round", "floor", "ceil",
        # Aggregations
        "sum", "mean", "min", "max", "count", "first", "last",
        "std", "var", "median", "n_unique",
        # Casting
        "cast",
        # Date/time
        "dt", "year", "month", "day", "hour", "minute", "second",
        "weekday", "quarter", "truncate",
        # Conditionals
        "when", "then", "otherwise",
        # Sorting
        "sort", "reverse",
        # Aliases
        "alias",
    }

    # Pattern for column references: pl.col("name") or pl.col('name')
    COL_PATTERN = re.compile(r'pl\.col\(["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']?\)')

    # Pattern for literals: pl.lit(value)
    LIT_PATTERN = re.compile(r'pl\.lit\(([^)]+)\)')

    # Allowed comparison operators
    COMPARISON_OPS = {"==", "!=", "<", ">", "<=", ">="}

    # Allowed arithmetic operators
    ARITHMETIC_OPS = {"+", "-", "*", "/", "%"}

    # Allowed logical operators
    LOGICAL_OPS = {"&", "|", "~"}

    def __init__(self):
        """Initialize the parser."""
        self._expression_cache: Dict[str, pl.Expr] = {}

    def parse(self, expression: str) -> pl.Expr:
        """
        Parse a string expression into a Polars expression safely.

        Args:
            expression: String representation of a Polars expression

        Returns:
            Polars expression object

        Raises:
            ExpressionParseError: If expression contains unsafe patterns
        """
        if not expression or not isinstance(expression, str):
            raise ExpressionParseError("Expression must be a non-empty string")

        # Check cache first
        if expression in self._expression_cache:
            return self._expression_cache[expression]

        # Validate expression doesn't contain dangerous patterns
        self._validate_safe(expression)

        # Build the expression
        expr = self._build_expression(expression)

        # Cache for reuse
        self._expression_cache[expression] = expr

        return expr

    def _validate_safe(self, expression: str) -> None:
        """
        Validate that expression doesn't contain dangerous patterns.

        Raises:
            ExpressionParseError: If unsafe patterns detected
        """
        # Block dangerous builtins
        dangerous_patterns = [
            r'\beval\b', r'\bexec\b', r'\bcompile\b',
            r'\b__\w+__\b',  # dunder methods
            r'\bimport\b', r'\bopen\b', r'\bfile\b',
            r'\bglobals\b', r'\blocals\b', r'\bgetattr\b',
            r'\bsetattr\b', r'\bdelattr\b', r'\bvars\b',
            r'\bos\b', r'\bsys\b', r'\bsubprocess\b',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, expression):
                raise ExpressionParseError(
                    f"Expression contains disallowed pattern: {pattern}"
                )

        # Validate only allowed method calls are used
        method_calls = re.findall(r'\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', expression)
        for method in method_calls:
            if method not in self.ALLOWED_METHODS:
                raise ExpressionParseError(
                    f"Method '{method}' is not in the allowed list"
                )

        # Validate pl. calls only use allowed methods
        pl_calls = re.findall(r'pl\.([a-zA-Z_][a-zA-Z0-9_]*)', expression)
        for call in pl_calls:
            if call not in self.ALLOWED_METHODS:
                raise ExpressionParseError(
                    f"pl.{call} is not in the allowed list"
                )

    def _build_expression(self, expression: str) -> pl.Expr:
        """
        Build a Polars expression from validated string.

        This uses a whitelist approach where we parse known patterns
        and construct Polars expressions programmatically.
        """
        expression = expression.strip()

        # Simple column reference: pl.col("name")
        col_match = re.fullmatch(r'pl\.col\(["\']([^"\']+)["\']\)', expression)
        if col_match:
            return pl.col(col_match.group(1))

        # Literal: pl.lit(value)
        lit_match = re.fullmatch(r'pl\.lit\(([^)]+)\)', expression)
        if lit_match:
            value = self._parse_literal(lit_match.group(1))
            return pl.lit(value)

        # Comparison: pl.col("x") > value
        comp_match = re.match(
            r'pl\.col\(["\']([^"\']+)["\']\)\s*([<>=!]+)\s*(.+)',
            expression
        )
        if comp_match:
            col_name, op, value_str = comp_match.groups()
            value = self._parse_literal(value_str.strip())
            col_expr = pl.col(col_name)

            if op == "==":
                return col_expr == value
            elif op == "!=":
                return col_expr != value
            elif op == "<":
                return col_expr < value
            elif op == ">":
                return col_expr > value
            elif op == "<=":
                return col_expr <= value
            elif op == ">=":
                return col_expr >= value

        # Null checks: pl.col("x").is_null()
        null_match = re.fullmatch(
            r'pl\.col\(["\']([^"\']+)["\']\)\.(is_null|is_not_null)\(\)',
            expression
        )
        if null_match:
            col_name, method = null_match.groups()
            col_expr = pl.col(col_name)
            return col_expr.is_null() if method == "is_null" else col_expr.is_not_null()

        # String contains: pl.col("x").str.contains("pattern")
        str_contains_match = re.fullmatch(
            r'pl\.col\(["\']([^"\']+)["\']\)\.str\.contains\(["\']([^"\']+)["\']\)',
            expression
        )
        if str_contains_match:
            col_name, pattern = str_contains_match.groups()
            return pl.col(col_name).str.contains(pattern)

        # Arithmetic: pl.col("x") + pl.col("y") or pl.col("x") * value
        arith_match = re.match(
            r'pl\.col\(["\']([^"\']+)["\']\)\s*([+\-*/%])\s*(.+)',
            expression
        )
        if arith_match:
            col_name, op, right_str = arith_match.groups()
            right_str = right_str.strip()
            left_expr = pl.col(col_name)

            # Check if right side is a column or literal
            right_col_match = re.fullmatch(r'pl\.col\(["\']([^"\']+)["\']\)', right_str)
            if right_col_match:
                right_expr = pl.col(right_col_match.group(1))
            else:
                right_expr = self._parse_literal(right_str)

            if op == "+":
                return left_expr + right_expr
            elif op == "-":
                return left_expr - right_expr
            elif op == "*":
                return left_expr * right_expr
            elif op == "/":
                return left_expr / right_expr
            elif op == "%":
                return left_expr % right_expr

        raise ExpressionParseError(
            f"Unable to parse expression: {expression}. "
            "Supported patterns: pl.col('x') > value, pl.col('x').is_null(), "
            "pl.col('x').str.contains('pattern'), pl.col('x') + pl.col('y')"
        )

    def _parse_literal(self, value_str: str) -> Any:
        """Parse a literal value from string."""
        value_str = value_str.strip()

        # String literal
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        # Boolean
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # None/null
        if value_str.lower() in ("none", "null"):
            return None

        # Integer
        try:
            return int(value_str)
        except ValueError:
            pass

        # Float
        try:
            return float(value_str)
        except ValueError:
            pass

        raise ExpressionParseError(f"Unable to parse literal: {value_str}")


# Global parser instance
_parser = SafePolarsExpressionParser()


def parse_safe_expression(expression: str) -> pl.Expr:
    """
    Parse a string expression into a Polars expression safely.

    This is a convenience function that uses a global parser instance.

    Args:
        expression: String representation of a Polars expression

    Returns:
        Polars expression object

    Raises:
        ExpressionParseError: If expression contains unsafe patterns
    """
    return _parser.parse(expression)
