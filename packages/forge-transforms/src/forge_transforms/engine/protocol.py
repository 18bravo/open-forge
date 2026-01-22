"""
Transform Engine Protocol

Defines the interface that all transform engines must implement.
Currently only DataFusion is supported (Spark/Flink deferred per consolidated architecture).
"""

from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Any, Protocol, runtime_checkable

import pyarrow as pa


class ExecutionStatus(str, Enum):
    """Status of a transform execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionConfig:
    """Configuration for transform execution.

    Attributes:
        batch_size: Number of rows to process per batch.
        timeout: Maximum execution time.
        memory_limit_mb: Maximum memory usage in megabytes.
        parallelism: Number of parallel execution threads.
        enable_caching: Whether to cache intermediate results.
    """

    batch_size: int = 10000
    timeout: timedelta = timedelta(minutes=30)
    memory_limit_mb: int = 4096
    parallelism: int = 4
    enable_caching: bool = True


@dataclass
class ExecutionMetrics:
    """Metrics collected during transform execution.

    Attributes:
        rows_processed: Total number of rows processed.
        bytes_processed: Total bytes processed.
        execution_time_ms: Time taken in milliseconds.
        peak_memory_mb: Peak memory usage in megabytes.
        partitions_processed: Number of partitions processed.
    """

    rows_processed: int = 0
    bytes_processed: int = 0
    execution_time_ms: int = 0
    peak_memory_mb: float = 0.0
    partitions_processed: int = 0


@dataclass
class ExecutionResult:
    """Result of a transform execution.

    Attributes:
        status: The execution status.
        data: The resulting data as an Arrow table (if successful).
        metrics: Execution metrics.
        error: Error message if execution failed.
        warnings: Any warnings generated during execution.
    """

    status: ExecutionStatus
    data: pa.Table | None = None
    metrics: ExecutionMetrics = field(default_factory=ExecutionMetrics)
    error: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.COMPLETED

    @property
    def row_count(self) -> int:
        """Get the number of rows in the result."""
        if self.data is None:
            return 0
        return self.data.num_rows


@runtime_checkable
class TransformEngine(Protocol):
    """Protocol for transform execution engines.

    This protocol defines the interface that all transform engines must implement.
    Per the consolidated architecture, only DataFusion is implemented for MVP.
    Spark and Flink support is deferred.

    Example:
        ```python
        engine = DataFusionEngine()
        await engine.initialize()

        # Execute SQL transform
        result = await engine.execute_sql(
            "SELECT * FROM customers WHERE active = true",
            context=session_context,
        )

        if result.is_success:
            print(f"Processed {result.row_count} rows")
        ```
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the engine and any required resources."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the engine and release resources."""
        ...

    @abstractmethod
    async def execute_sql(
        self,
        sql: str,
        config: ExecutionConfig | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Execute a SQL transform.

        Args:
            sql: The SQL query to execute.
            config: Optional execution configuration.
            parameters: Optional query parameters.

        Returns:
            ExecutionResult containing the transformed data or error.
        """
        ...

    @abstractmethod
    async def execute_plan(
        self,
        plan: "LogicalPlan",
        config: ExecutionConfig | None = None,
    ) -> ExecutionResult:
        """Execute a logical plan.

        Args:
            plan: The logical plan to execute.
            config: Optional execution configuration.

        Returns:
            ExecutionResult containing the transformed data or error.
        """
        ...

    @abstractmethod
    def register_table(
        self,
        name: str,
        data: pa.Table,
    ) -> None:
        """Register an Arrow table for use in queries.

        Args:
            name: The table name to register.
            data: The Arrow table data.
        """
        ...

    @abstractmethod
    def register_udf(
        self,
        name: str,
        func: "UserDefinedFunction",
    ) -> None:
        """Register a user-defined function.

        Args:
            name: The function name.
            func: The UDF implementation.
        """
        ...

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Get the engine name."""
        ...

    @property
    @abstractmethod
    def engine_version(self) -> str:
        """Get the engine version."""
        ...


class LogicalPlan:
    """Represents a logical query plan.

    This is a placeholder for the actual logical plan representation
    that will be built out during implementation.
    """

    def __init__(self, operations: list[dict[str, Any]] | None = None):
        self.operations = operations or []

    def add_operation(self, operation: dict[str, Any]) -> "LogicalPlan":
        """Add an operation to the plan."""
        self.operations.append(operation)
        return self


class UserDefinedFunction(Protocol):
    """Protocol for user-defined functions."""

    @property
    def name(self) -> str:
        """Get the function name."""
        ...

    @property
    def return_type(self) -> pa.DataType:
        """Get the return type."""
        ...

    def __call__(self, *args: Any) -> Any:
        """Execute the function."""
        ...
