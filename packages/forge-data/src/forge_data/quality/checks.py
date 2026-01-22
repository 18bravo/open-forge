"""
Quality check implementations.

Provides an abstract base class for quality checks and concrete implementations
for common check types: freshness, completeness, and schema validation.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class CheckSeverity(str, Enum):
    """Severity level for quality check results."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CheckResult(BaseModel):
    """Result of a quality check execution."""

    check_id: str
    check_type: str
    dataset_id: str
    passed: bool
    severity: CheckSeverity
    message: str
    details: dict[str, Any] | None = None
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    execution_ms: int = 0


class DataContext(Protocol):
    """Protocol for data access during check execution."""

    async def get_max_timestamp(self, dataset_id: str, column: str) -> datetime | None:
        """Get the maximum timestamp value from a column."""
        ...

    async def get_null_stats(
        self, dataset_id: str, columns: list[str]
    ) -> dict[str, float]:
        """Get null percentage for specified columns."""
        ...

    async def get_schema(self, dataset_id: str) -> dict[str, Any]:
        """Get the schema of a dataset."""
        ...

    async def get_row_count(self, dataset_id: str) -> int:
        """Get the row count of a dataset."""
        ...


class QualityCheck(ABC):
    """
    Abstract base class for all quality checks.

    Subclasses must implement:
    - check_type property: Return the check type identifier
    - execute method: Execute the check and return results

    Example:
        class MyCustomCheck(QualityCheck):
            @property
            def check_type(self) -> str:
                return "my_custom_check"

            async def execute(self, data_context: DataContext) -> CheckResult:
                # Implement check logic
                return self._result(passed=True, message="Check passed")
    """

    def __init__(
        self,
        check_id: str,
        dataset_id: str,
        severity: CheckSeverity = CheckSeverity.ERROR,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize a quality check.

        Args:
            check_id: Unique identifier for this check instance
            dataset_id: ID of the dataset to check
            severity: Severity level if check fails
            config: Check-specific configuration
        """
        self.check_id = check_id
        self.dataset_id = dataset_id
        self.severity = severity
        self.config = config or {}

    @property
    @abstractmethod
    def check_type(self) -> str:
        """Return the check type identifier."""
        ...

    @abstractmethod
    async def execute(self, data_context: DataContext) -> CheckResult:
        """
        Execute the check and return results.

        Args:
            data_context: Context providing data access methods

        Returns:
            CheckResult with pass/fail status and details
        """
        ...

    def _result(
        self,
        passed: bool,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> CheckResult:
        """Helper to create a CheckResult with common fields populated."""
        return CheckResult(
            check_id=self.check_id,
            check_type=self.check_type,
            dataset_id=self.dataset_id,
            passed=passed,
            severity=self.severity,
            message=message,
            details=details,
            executed_at=datetime.utcnow(),
            execution_ms=0,  # Set by runner
        )


class FreshnessCheck(QualityCheck):
    """
    Check that data has been updated within expected timeframe.

    Config options:
        max_age_hours: Maximum allowed age in hours (default: 24)
        timestamp_column: Column containing timestamps (default: "updated_at")
    """

    @property
    def check_type(self) -> str:
        return "freshness"

    async def execute(self, data_context: DataContext) -> CheckResult:
        max_age_hours = self.config.get("max_age_hours", 24)
        timestamp_column = self.config.get("timestamp_column", "updated_at")

        latest = await data_context.get_max_timestamp(self.dataset_id, timestamp_column)

        if latest is None:
            return self._result(
                passed=False,
                message=f"No timestamps found in column '{timestamp_column}'",
                details={"timestamp_column": timestamp_column},
            )

        age = datetime.utcnow() - latest
        max_age = timedelta(hours=max_age_hours)
        passed = age <= max_age

        return self._result(
            passed=passed,
            message=f"Data age: {age}. Max allowed: {max_age}",
            details={
                "latest_timestamp": latest.isoformat(),
                "age_hours": age.total_seconds() / 3600,
                "max_age_hours": max_age_hours,
            },
        )


class CompletenessCheck(QualityCheck):
    """
    Check for null/missing values in specified columns.

    Config options:
        columns: List of columns to check (required)
        max_null_percentage: Maximum allowed null percentage (default: 0.0)
    """

    @property
    def check_type(self) -> str:
        return "completeness"

    async def execute(self, data_context: DataContext) -> CheckResult:
        columns = self.config.get("columns", [])
        max_null_pct = self.config.get("max_null_percentage", 0.0)

        if not columns:
            return self._result(
                passed=False,
                message="No columns specified for completeness check",
                details={"config": self.config},
            )

        stats = await data_context.get_null_stats(self.dataset_id, columns)

        failed_columns = []
        for col, null_pct in stats.items():
            if null_pct > max_null_pct:
                failed_columns.append(
                    {
                        "column": col,
                        "null_percentage": null_pct,
                        "threshold": max_null_pct,
                    }
                )

        passed = len(failed_columns) == 0

        return self._result(
            passed=passed,
            message=f"Completeness check: {len(failed_columns)} columns exceed null threshold",
            details={
                "column_stats": stats,
                "failed_columns": failed_columns,
                "threshold": max_null_pct,
            },
        )


class SchemaCheck(QualityCheck):
    """
    Validate dataset schema against expected structure.

    Config options:
        expected_columns: Dict of column_name -> expected_type
        allow_extra_columns: Whether to allow columns not in expected (default: True)
        require_all_columns: Whether all expected columns must exist (default: True)
    """

    @property
    def check_type(self) -> str:
        return "schema"

    async def execute(self, data_context: DataContext) -> CheckResult:
        expected_columns = self.config.get("expected_columns", {})
        allow_extra = self.config.get("allow_extra_columns", True)
        require_all = self.config.get("require_all_columns", True)

        actual_schema = await data_context.get_schema(self.dataset_id)
        actual_columns = actual_schema.get("columns", {})

        issues: list[dict[str, Any]] = []

        # Check for missing expected columns
        if require_all:
            for col, expected_type in expected_columns.items():
                if col not in actual_columns:
                    issues.append(
                        {
                            "type": "missing_column",
                            "column": col,
                            "expected_type": expected_type,
                        }
                    )

        # Check for type mismatches
        for col, expected_type in expected_columns.items():
            if col in actual_columns:
                actual_type = actual_columns[col]
                if actual_type != expected_type:
                    issues.append(
                        {
                            "type": "type_mismatch",
                            "column": col,
                            "expected_type": expected_type,
                            "actual_type": actual_type,
                        }
                    )

        # Check for unexpected columns
        if not allow_extra:
            for col in actual_columns:
                if col not in expected_columns:
                    issues.append(
                        {
                            "type": "unexpected_column",
                            "column": col,
                        }
                    )

        passed = len(issues) == 0

        return self._result(
            passed=passed,
            message=f"Schema check: {len(issues)} issues found",
            details={
                "issues": issues,
                "expected_columns": expected_columns,
                "actual_columns": actual_columns,
            },
        )
