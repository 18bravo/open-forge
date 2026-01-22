"""
Tests for quality check module.

Verifies the QualityCheck ABC and concrete implementations work correctly.
"""

from datetime import datetime, timedelta
from typing import Any

import pytest

from forge_data.quality import (
    CheckResult,
    CheckSeverity,
    CompletenessCheck,
    FreshnessCheck,
    QualityCheck,
    SchemaCheck,
)
from forge_data.quality.checks import DataContext


class MockDataContext:
    """Mock data context for testing."""

    def __init__(self, data: dict[str, Any] | None = None):
        self.data = data or {}

    async def get_max_timestamp(self, dataset_id: str, column: str) -> datetime | None:
        return self.data.get("max_timestamp")

    async def get_null_stats(
        self, dataset_id: str, columns: list[str]
    ) -> dict[str, float]:
        return self.data.get("null_stats", {})

    async def get_schema(self, dataset_id: str) -> dict[str, Any]:
        return self.data.get("schema", {"columns": {}})

    async def get_row_count(self, dataset_id: str) -> int:
        return self.data.get("row_count", 0)


class TestQualityCheckABC:
    """Test the QualityCheck abstract base class."""

    def test_cannot_instantiate_abc(self):
        """Test that QualityCheck cannot be instantiated directly."""
        with pytest.raises(TypeError):
            QualityCheck(
                check_id="test",
                dataset_id="ds",
            )

    def test_custom_check_implementation(self):
        """Test implementing a custom check."""

        class AlwaysPassCheck(QualityCheck):
            @property
            def check_type(self) -> str:
                return "always_pass"

            async def execute(self, data_context: DataContext) -> CheckResult:
                return self._result(passed=True, message="Always passes")

        check = AlwaysPassCheck(check_id="test", dataset_id="ds")
        assert check.check_type == "always_pass"


class TestFreshnessCheck:
    """Test freshness check implementation."""

    @pytest.mark.asyncio
    async def test_fresh_data_passes(self):
        """Test that fresh data passes the check."""
        context = MockDataContext({
            "max_timestamp": datetime.utcnow() - timedelta(hours=1)
        })

        check = FreshnessCheck(
            check_id="freshness-1",
            dataset_id="test_dataset",
            config={"max_age_hours": 24},
        )

        result = await check.execute(context)

        assert result.passed is True
        assert "Data age" in result.message

    @pytest.mark.asyncio
    async def test_stale_data_fails(self):
        """Test that stale data fails the check."""
        context = MockDataContext({
            "max_timestamp": datetime.utcnow() - timedelta(hours=48)
        })

        check = FreshnessCheck(
            check_id="freshness-1",
            dataset_id="test_dataset",
            config={"max_age_hours": 24},
        )

        result = await check.execute(context)

        assert result.passed is False

    @pytest.mark.asyncio
    async def test_no_timestamp_fails(self):
        """Test that missing timestamps fail the check."""
        context = MockDataContext({"max_timestamp": None})

        check = FreshnessCheck(
            check_id="freshness-1",
            dataset_id="test_dataset",
        )

        result = await check.execute(context)

        assert result.passed is False
        assert "No timestamps found" in result.message


class TestCompletenessCheck:
    """Test completeness check implementation."""

    @pytest.mark.asyncio
    async def test_complete_data_passes(self):
        """Test that data with no nulls passes."""
        context = MockDataContext({
            "null_stats": {"col1": 0.0, "col2": 0.0}
        })

        check = CompletenessCheck(
            check_id="completeness-1",
            dataset_id="test_dataset",
            config={
                "columns": ["col1", "col2"],
                "max_null_percentage": 0.0,
            },
        )

        result = await check.execute(context)

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_incomplete_data_fails(self):
        """Test that data with nulls above threshold fails."""
        context = MockDataContext({
            "null_stats": {"col1": 5.0, "col2": 10.0}
        })

        check = CompletenessCheck(
            check_id="completeness-1",
            dataset_id="test_dataset",
            config={
                "columns": ["col1", "col2"],
                "max_null_percentage": 1.0,
            },
        )

        result = await check.execute(context)

        assert result.passed is False
        assert result.details is not None
        assert len(result.details["failed_columns"]) == 2

    @pytest.mark.asyncio
    async def test_no_columns_specified(self):
        """Test that check fails gracefully with no columns."""
        context = MockDataContext()

        check = CompletenessCheck(
            check_id="completeness-1",
            dataset_id="test_dataset",
            config={},  # No columns specified
        )

        result = await check.execute(context)

        assert result.passed is False
        assert "No columns specified" in result.message


class TestSchemaCheck:
    """Test schema check implementation."""

    @pytest.mark.asyncio
    async def test_matching_schema_passes(self):
        """Test that matching schema passes."""
        context = MockDataContext({
            "schema": {
                "columns": {
                    "id": "integer",
                    "name": "string",
                }
            }
        })

        check = SchemaCheck(
            check_id="schema-1",
            dataset_id="test_dataset",
            config={
                "expected_columns": {
                    "id": "integer",
                    "name": "string",
                }
            },
        )

        result = await check.execute(context)

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_missing_column_fails(self):
        """Test that missing columns fail."""
        context = MockDataContext({
            "schema": {
                "columns": {"id": "integer"}
            }
        })

        check = SchemaCheck(
            check_id="schema-1",
            dataset_id="test_dataset",
            config={
                "expected_columns": {
                    "id": "integer",
                    "name": "string",
                },
                "require_all_columns": True,
            },
        )

        result = await check.execute(context)

        assert result.passed is False
        assert result.details is not None
        assert any(
            issue["type"] == "missing_column"
            for issue in result.details["issues"]
        )

    @pytest.mark.asyncio
    async def test_type_mismatch_fails(self):
        """Test that type mismatches fail."""
        context = MockDataContext({
            "schema": {
                "columns": {"id": "string"}  # Wrong type
            }
        })

        check = SchemaCheck(
            check_id="schema-1",
            dataset_id="test_dataset",
            config={
                "expected_columns": {"id": "integer"}
            },
        )

        result = await check.execute(context)

        assert result.passed is False
        assert any(
            issue["type"] == "type_mismatch"
            for issue in result.details["issues"]
        )


class TestCheckSeverity:
    """Test check severity levels."""

    def test_severity_values(self):
        """Test that all severity values are defined."""
        assert CheckSeverity.INFO == "info"
        assert CheckSeverity.WARNING == "warning"
        assert CheckSeverity.ERROR == "error"
        assert CheckSeverity.CRITICAL == "critical"

    def test_check_with_severity(self):
        """Test creating check with different severities."""
        for severity in CheckSeverity:
            check = FreshnessCheck(
                check_id="test",
                dataset_id="ds",
                severity=severity,
            )
            assert check.severity == severity
