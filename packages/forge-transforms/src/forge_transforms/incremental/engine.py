"""
Incremental Processing Engine

Provides incremental data processing capabilities with watermark tracking
and checkpoint-based recovery.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TYPE_CHECKING

import pyarrow as pa
from pydantic import BaseModel, Field

from forge_transforms.incremental.checkpoints import (
    Checkpoint,
    CheckpointMetadata,
    CheckpointStore,
    MemoryCheckpointStore,
)

if TYPE_CHECKING:
    from forge_transforms.engine.protocol import TransformEngine
    from forge_transforms.transforms.base import Transform


class ProcessingMode(str, Enum):
    """Incremental processing modes."""

    APPEND = "append"  # Process only new data
    UPSERT = "upsert"  # Update existing + insert new
    FULL_REFRESH = "full_refresh"  # Reprocess everything


class WatermarkStrategy(str, Enum):
    """Strategies for watermark management."""

    TIMESTAMP = "timestamp"  # Use timestamp column as watermark
    SEQUENCE = "sequence"  # Use sequence/offset as watermark
    PARTITION = "partition"  # Use partition ID as watermark


class IncrementalConfig(BaseModel):
    """Configuration for incremental processing.

    Attributes:
        processor_id: Unique identifier for this processor.
        mode: The processing mode.
        watermark_strategy: Strategy for tracking progress.
        watermark_column: Column to use for watermark (for TIMESTAMP/SEQUENCE).
        checkpoint_interval: How often to create checkpoints.
        checkpoint_keep_count: Number of checkpoints to retain.
        batch_size: Number of rows per batch.
        max_batches_per_run: Maximum batches to process in one run.
    """

    processor_id: str = Field(..., description="Unique processor identifier")
    mode: ProcessingMode = Field(ProcessingMode.APPEND, description="Processing mode")
    watermark_strategy: WatermarkStrategy = Field(
        WatermarkStrategy.TIMESTAMP, description="Watermark strategy"
    )
    watermark_column: str = Field("updated_at", description="Watermark column name")
    checkpoint_interval: int = Field(1000, ge=1, description="Rows between checkpoints")
    checkpoint_keep_count: int = Field(5, ge=1, description="Checkpoints to retain")
    batch_size: int = Field(10000, ge=1, description="Rows per batch")
    max_batches_per_run: int | None = Field(None, ge=1, description="Max batches per run")


@dataclass
class IncrementalState:
    """Internal state for incremental processing.

    Attributes:
        watermark: Current watermark value.
        last_processed_at: When data was last processed.
        total_rows_processed: Total rows processed across all runs.
        current_run_rows: Rows processed in current run.
    """

    watermark: str | None = None
    last_processed_at: datetime | None = None
    total_rows_processed: int = 0
    current_run_rows: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "watermark": self.watermark,
            "last_processed_at": self.last_processed_at.isoformat() if self.last_processed_at else None,
            "total_rows_processed": self.total_rows_processed,
            "current_run_rows": self.current_run_rows,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IncrementalState":
        """Create from dictionary."""
        return cls(
            watermark=data.get("watermark"),
            last_processed_at=datetime.fromisoformat(data["last_processed_at"]) if data.get("last_processed_at") else None,
            total_rows_processed=data.get("total_rows_processed", 0),
            current_run_rows=data.get("current_run_rows", 0),
        )


@dataclass
class ProcessingResult:
    """Result of incremental processing.

    Attributes:
        success: Whether processing completed successfully.
        rows_processed: Number of rows processed in this run.
        batches_processed: Number of batches processed.
        new_watermark: The new watermark value after processing.
        checkpoint_id: ID of the checkpoint created (if any).
        error: Error message if processing failed.
        metrics: Additional metrics.
    """

    success: bool
    rows_processed: int = 0
    batches_processed: int = 0
    new_watermark: str | None = None
    checkpoint_id: str | None = None
    error: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)


class IncrementalProcessor:
    """Incremental data processing engine.

    Provides watermark-based incremental processing with checkpoint support
    for reliable, resumable data transformation.

    Example:
        ```python
        config = IncrementalConfig(
            processor_id="sales_incremental",
            mode=ProcessingMode.APPEND,
            watermark_column="created_at",
            checkpoint_interval=5000,
        )
        processor = IncrementalProcessor(config)

        # Process incrementally
        result = await processor.process(
            engine=datafusion_engine,
            transform=my_transform,
            source_table="raw_sales",
        )

        print(f"Processed {result.rows_processed} new rows")
        print(f"New watermark: {result.new_watermark}")
        ```
    """

    def __init__(
        self,
        config: IncrementalConfig,
        checkpoint_store: CheckpointStore | None = None,
    ):
        """Initialize the incremental processor.

        Args:
            config: Processor configuration.
            checkpoint_store: Optional checkpoint store (defaults to memory).
        """
        self.config = config
        self.checkpoint_store = checkpoint_store or MemoryCheckpointStore()
        self._state = IncrementalState()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the processor, loading latest checkpoint if available."""
        if self._initialized:
            return

        # Try to load the latest checkpoint
        latest = await self.checkpoint_store.get_latest(self.config.processor_id)
        if latest:
            self._state = IncrementalState.from_dict(latest.state)

        self._initialized = True

    async def process(
        self,
        engine: "TransformEngine",
        transform: "Transform",
        source_table: str,
    ) -> ProcessingResult:
        """Process data incrementally.

        Args:
            engine: The transform engine to use.
            transform: The transform to apply.
            source_table: Name of the source table (must be registered).

        Returns:
            ProcessingResult with processing statistics.
        """
        if not self._initialized:
            await self.initialize()

        start_time = datetime.utcnow()
        self._state.current_run_rows = 0
        batches_processed = 0

        try:
            # Build query with watermark filter
            watermark_filter = self._build_watermark_filter()

            # Process in batches
            while True:
                # Check batch limit
                if (
                    self.config.max_batches_per_run
                    and batches_processed >= self.config.max_batches_per_run
                ):
                    break

                # Execute transform (the transform handles the actual query)
                # In a full implementation, we would:
                # 1. Query source with watermark filter and LIMIT
                # 2. Apply transform
                # 3. Update watermark
                # 4. Checkpoint periodically

                # For now, return a placeholder result
                # Full implementation would process actual data
                batches_processed += 1

                # Create checkpoint if needed
                if self._state.current_run_rows >= self.config.checkpoint_interval:
                    await self._create_checkpoint()

                # For scaffold, break after one iteration
                break

            # Create final checkpoint
            checkpoint_id = await self._create_checkpoint()

            # Cleanup old checkpoints
            await self.checkpoint_store.cleanup(
                self.config.processor_id,
                self.config.checkpoint_keep_count,
            )

            return ProcessingResult(
                success=True,
                rows_processed=self._state.current_run_rows,
                batches_processed=batches_processed,
                new_watermark=self._state.watermark,
                checkpoint_id=checkpoint_id,
                metrics={
                    "processing_time_ms": int(
                        (datetime.utcnow() - start_time).total_seconds() * 1000
                    ),
                },
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                rows_processed=self._state.current_run_rows,
                batches_processed=batches_processed,
                error=str(e),
            )

    def _build_watermark_filter(self) -> str | None:
        """Build SQL filter clause based on watermark.

        Returns:
            SQL WHERE clause or None if no watermark.
        """
        if self._state.watermark is None:
            return None

        col = self.config.watermark_column

        if self.config.watermark_strategy == WatermarkStrategy.TIMESTAMP:
            return f"{col} > '{self._state.watermark}'"
        elif self.config.watermark_strategy == WatermarkStrategy.SEQUENCE:
            return f"{col} > {self._state.watermark}"
        elif self.config.watermark_strategy == WatermarkStrategy.PARTITION:
            return f"{col} > '{self._state.watermark}'"

        return None

    async def _create_checkpoint(self) -> str:
        """Create a new checkpoint.

        Returns:
            The checkpoint ID.
        """
        checkpoint_id = str(uuid.uuid4())

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            transform_id=self.config.processor_id,
            state=self._state.to_dict(),
            metadata=CheckpointMetadata(
                created_at=datetime.utcnow(),
                rows_processed=self._state.total_rows_processed,
                watermark=self._state.watermark,
            ),
        )

        await self.checkpoint_store.save(checkpoint)
        return checkpoint_id

    def update_watermark(self, new_watermark: str) -> None:
        """Update the watermark value.

        Args:
            new_watermark: The new watermark value.
        """
        self._state.watermark = new_watermark
        self._state.last_processed_at = datetime.utcnow()

    def record_rows_processed(self, count: int) -> None:
        """Record rows processed.

        Args:
            count: Number of rows processed.
        """
        self._state.current_run_rows += count
        self._state.total_rows_processed += count

    async def reset(self) -> None:
        """Reset the processor state.

        Clears all checkpoints and resets the watermark.
        """
        self._state = IncrementalState()

        # Delete all checkpoints for this processor
        checkpoints = await self.checkpoint_store.list(
            self.config.processor_id, limit=1000
        )
        for checkpoint in checkpoints:
            await self.checkpoint_store.delete(checkpoint.checkpoint_id)

    @property
    def current_watermark(self) -> str | None:
        """Get the current watermark value."""
        return self._state.watermark

    @property
    def total_rows_processed(self) -> int:
        """Get total rows processed across all runs."""
        return self._state.total_rows_processed
