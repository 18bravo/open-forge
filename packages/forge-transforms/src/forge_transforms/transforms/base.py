"""
Transform Base Classes

Provides the abstract base class for all transform types and common
configuration and result types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pyarrow as pa
from pydantic import BaseModel, Field


class TransformStatus(str, Enum):
    """Status of a transform execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransformConfig(BaseModel):
    """Base configuration for transforms.

    Attributes:
        transform_id: Unique identifier for this transform.
        name: Human-readable name.
        description: Optional description.
        tags: Optional tags for categorization.
        timeout_seconds: Maximum execution time in seconds.
        retry_count: Number of retries on failure.
    """

    transform_id: str = Field(..., description="Unique transform identifier")
    name: str = Field("", description="Human-readable name")
    description: str = Field("", description="Optional description")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    timeout_seconds: int = Field(1800, ge=1, le=86400, description="Timeout in seconds")
    retry_count: int = Field(0, ge=0, le=5, description="Number of retries")

    model_config = {"extra": "allow"}


@dataclass
class TransformResult:
    """Result of a transform execution.

    Attributes:
        status: The execution status.
        data: The resulting Arrow table (if successful).
        error: Error message if failed.
        started_at: When execution started.
        completed_at: When execution completed.
        metrics: Execution metrics.
    """

    status: TransformStatus
    data: pa.Table | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if the transform completed successfully."""
        return self.status == TransformStatus.COMPLETED

    @property
    def duration_ms(self) -> int | None:
        """Get execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None

    @property
    def row_count(self) -> int:
        """Get the number of rows in the result."""
        if self.data is None:
            return 0
        return self.data.num_rows


class Transform(ABC):
    """Abstract base class for data transforms.

    All transform types (SQL, Expression, Aggregate) inherit from this class.
    Transforms define data transformation logic that can be executed by
    a TransformEngine.

    Example:
        ```python
        class MyTransform(Transform):
            @property
            def transform_type(self) -> str:
                return "my_transform"

            async def execute(self, engine: TransformEngine, input_data: pa.Table) -> TransformResult:
                # Implementation
                ...

            def validate(self) -> list[str]:
                # Validation logic
                return []

        transform = MyTransform(config)
        result = await transform.execute(engine, data)
        ```
    """

    def __init__(self, config: TransformConfig):
        """Initialize the transform with configuration.

        Args:
            config: The transform configuration.
        """
        self.config = config

    @property
    @abstractmethod
    def transform_type(self) -> str:
        """Get the transform type identifier.

        Returns:
            A string identifying the transform type (e.g., "sql", "expression").
        """
        ...

    @abstractmethod
    async def execute(
        self,
        engine: "TransformEngine",
        input_data: pa.Table | None = None,
    ) -> TransformResult:
        """Execute the transform.

        Args:
            engine: The transform engine to use for execution.
            input_data: Optional input data table.

        Returns:
            TransformResult containing the output data or error.
        """
        ...

    @abstractmethod
    def validate(self) -> list[str]:
        """Validate the transform configuration.

        Returns:
            List of validation error messages. Empty if valid.
        """
        ...

    @abstractmethod
    def to_sql(self) -> str:
        """Convert the transform to SQL representation.

        Returns:
            SQL string representing this transform.

        Raises:
            NotImplementedError: If SQL conversion is not supported.
        """
        ...

    def _create_result(
        self,
        status: TransformStatus,
        data: pa.Table | None = None,
        error: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        **metrics: Any,
    ) -> TransformResult:
        """Helper to create a TransformResult.

        Args:
            status: The execution status.
            data: The resulting data.
            error: Error message if failed.
            started_at: When execution started.
            completed_at: When execution completed.
            **metrics: Additional metrics.

        Returns:
            A TransformResult instance.
        """
        return TransformResult(
            status=status,
            data=data,
            error=error,
            started_at=started_at,
            completed_at=completed_at,
            metrics=metrics,
        )


# Type alias for forward reference
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from forge_transforms.engine.protocol import TransformEngine
