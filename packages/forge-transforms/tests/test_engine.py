"""
Tests for the transform engine.

These tests verify the engine protocol and basic DataFusionEngine behavior.
Note: Full DataFusion integration tests require the datafusion package.
"""

import pytest

from forge_transforms.engine import (
    ExecutionConfig,
    ExecutionResult,
    ExecutionStatus,
    ExecutionMetrics,
    SessionConfig,
    UDFRegistry,
    UDFMetadata,
    ScalarUDF,
    AggregateUDF,
)
from forge_transforms.engine.protocol import LogicalPlan

# Skip DataFusion tests if not installed
try:
    import datafusion
    DATAFUSION_AVAILABLE = True
except ImportError:
    DATAFUSION_AVAILABLE = False


class TestExecutionConfig:
    """Test ExecutionConfig defaults and validation."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ExecutionConfig()

        assert config.batch_size == 10000
        assert config.memory_limit_mb == 4096
        assert config.parallelism == 4
        assert config.enable_caching is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ExecutionConfig(
            batch_size=5000,
            memory_limit_mb=8192,
            parallelism=8,
        )

        assert config.batch_size == 5000
        assert config.memory_limit_mb == 8192
        assert config.parallelism == 8


class TestExecutionResult:
    """Test ExecutionResult behavior."""

    def test_successful_result(self):
        """Test successful execution result."""
        result = ExecutionResult(status=ExecutionStatus.COMPLETED)
        assert result.is_success is True
        assert result.error is None

    def test_failed_result(self):
        """Test failed execution result."""
        result = ExecutionResult(
            status=ExecutionStatus.FAILED,
            error="Query syntax error",
        )
        assert result.is_success is False
        assert result.error == "Query syntax error"

    def test_row_count_no_data(self):
        """Test row count when no data."""
        result = ExecutionResult(status=ExecutionStatus.COMPLETED)
        assert result.row_count == 0


class TestExecutionMetrics:
    """Test ExecutionMetrics."""

    def test_default_metrics(self):
        """Test default metric values."""
        metrics = ExecutionMetrics()

        assert metrics.rows_processed == 0
        assert metrics.bytes_processed == 0
        assert metrics.execution_time_ms == 0

    def test_custom_metrics(self):
        """Test metrics with custom values."""
        metrics = ExecutionMetrics(
            rows_processed=1000,
            bytes_processed=50000,
            execution_time_ms=150,
            peak_memory_mb=256.5,
        )

        assert metrics.rows_processed == 1000
        assert metrics.peak_memory_mb == 256.5


class TestSessionConfig:
    """Test SessionConfig."""

    def test_default_config(self):
        """Test default session config."""
        config = SessionConfig()

        assert config.max_memory_mb == 4096
        assert config.target_partitions == 4
        assert config.batch_size == 8192
        assert config.enable_object_store is False

    def test_custom_config(self):
        """Test custom session config."""
        config = SessionConfig(
            max_memory_mb=16384,
            target_partitions=16,
            temp_dir="/tmp/datafusion",
        )

        assert config.max_memory_mb == 16384
        assert config.target_partitions == 16
        assert config.temp_dir == "/tmp/datafusion"


class TestLogicalPlan:
    """Test LogicalPlan placeholder."""

    def test_create_plan(self):
        """Test creating a logical plan."""
        plan = LogicalPlan()
        assert plan.operations == []

    def test_add_operation(self):
        """Test adding operations to plan."""
        plan = LogicalPlan()
        plan.add_operation({"type": "filter", "condition": "x > 5"})
        plan.add_operation({"type": "project", "columns": ["a", "b"]})

        assert len(plan.operations) == 2


class TestUDFMetadata:
    """Test UDF metadata."""

    def test_create_metadata(self):
        """Test creating UDF metadata."""
        import pyarrow as pa

        meta = UDFMetadata(
            name="my_func",
            description="A test function",
            input_types=[pa.int64(), pa.int64()],
            return_type=pa.int64(),
            is_deterministic=True,
        )

        assert meta.name == "my_func"
        assert len(meta.input_types) == 2


class TestUDFRegistry:
    """Test UDF registry."""

    def test_empty_registry(self):
        """Test empty registry."""
        registry = UDFRegistry()
        assert registry.list_names() == []

    def test_register_and_get(self):
        """Test registering and retrieving UDFs."""
        import pyarrow as pa

        class TestScalar(ScalarUDF):
            @property
            def metadata(self):
                return UDFMetadata(name="test_scalar", return_type=pa.int64())

            def evaluate(self, *args):
                return args[0]

        registry = UDFRegistry()
        udf = TestScalar()
        registry.register(udf)

        assert "test_scalar" in registry.list_names()
        assert registry.get("test_scalar") is not None

    def test_deregister(self):
        """Test deregistering UDFs."""
        import pyarrow as pa

        class TestScalar(ScalarUDF):
            @property
            def metadata(self):
                return UDFMetadata(name="to_remove", return_type=pa.int64())

            def evaluate(self, *args):
                return args[0]

        registry = UDFRegistry()
        registry.register(TestScalar())

        assert registry.deregister("to_remove") is True
        assert registry.deregister("nonexistent") is False
        assert "to_remove" not in registry.list_names()

    def test_clear_registry(self):
        """Test clearing the registry."""
        import pyarrow as pa

        class TestScalar(ScalarUDF):
            @property
            def metadata(self):
                return UDFMetadata(name="test", return_type=pa.int64())

            def evaluate(self, *args):
                return args[0]

        registry = UDFRegistry()
        registry.register(TestScalar())
        registry.clear()

        assert registry.list_names() == []


@pytest.mark.skipif(not DATAFUSION_AVAILABLE, reason="DataFusion not installed")
class TestDataFusionEngine:
    """Integration tests for DataFusionEngine (requires datafusion)."""

    @pytest.mark.asyncio
    async def test_engine_lifecycle(self):
        """Test engine initialization and shutdown."""
        from forge_transforms.engine import DataFusionEngine

        engine = DataFusionEngine()
        await engine.initialize()

        assert engine.engine_name == "DataFusion"

        await engine.shutdown()

    @pytest.mark.asyncio
    async def test_simple_query(self):
        """Test executing a simple query."""
        import pyarrow as pa
        from forge_transforms.engine import DataFusionEngine

        engine = DataFusionEngine()
        await engine.initialize()

        # Create test data
        data = pa.table({
            "id": [1, 2, 3],
            "value": [10, 20, 30],
        })
        engine.register_table("test", data)

        # Execute query
        result = await engine.execute_sql("SELECT * FROM test WHERE value > 15")

        assert result.is_success
        assert result.row_count == 2

        await engine.shutdown()
