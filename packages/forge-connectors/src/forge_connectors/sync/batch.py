"""
Batch sync strategy for full table extraction.

Handles complete extraction of data objects with:
- Configurable batch sizes
- Memory-efficient streaming
- Schema inference
"""

import logging
from dataclasses import dataclass
from typing import AsyncIterator, Optional

import pyarrow as pa

from forge_connectors.core.base import BaseConnector, SyncState

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch sync operations."""

    batch_size: int = 10000
    max_rows: Optional[int] = None  # Limit total rows (for testing)
    include_columns: Optional[list[str]] = None  # Columns to include
    exclude_columns: Optional[list[str]] = None  # Columns to exclude


class BatchSyncStrategy:
    """
    Strategy for full batch extraction.

    Reads all data from source in batches, optionally filtering columns.

    Example:
        strategy = BatchSyncStrategy(connector, config)
        async for batch in strategy.extract("orders"):
            await writer.write(destination, batch)
    """

    def __init__(self, connector: BaseConnector, config: Optional[BatchConfig] = None):
        """
        Initialize batch sync strategy.

        Args:
            connector: Source connector.
            config: Batch configuration.
        """
        self.connector = connector
        self.config = config or BatchConfig()

    async def extract(self, object_name: str) -> AsyncIterator[pa.RecordBatch]:
        """
        Extract all data from an object in batches.

        Args:
            object_name: Name of the object to extract.

        Yields:
            PyArrow RecordBatch for each chunk.
        """
        total_rows = 0

        async for batch in self.connector.read_batch(object_name):
            # Apply column filtering if configured
            if self.config.include_columns or self.config.exclude_columns:
                batch = self._filter_columns(batch)

            # Check row limit
            if self.config.max_rows:
                remaining = self.config.max_rows - total_rows
                if remaining <= 0:
                    break
                if batch.num_rows > remaining:
                    batch = batch.slice(0, remaining)

            total_rows += batch.num_rows
            yield batch

            if self.config.max_rows and total_rows >= self.config.max_rows:
                break

        logger.info(f"Batch extraction complete: {total_rows} rows from {object_name}")

    def _filter_columns(self, batch: pa.RecordBatch) -> pa.RecordBatch:
        """Filter columns based on configuration."""
        columns = list(batch.schema.names)

        if self.config.include_columns:
            columns = [c for c in columns if c in self.config.include_columns]
        elif self.config.exclude_columns:
            columns = [c for c in columns if c not in self.config.exclude_columns]

        if set(columns) == set(batch.schema.names):
            return batch

        # Select only the desired columns
        indices = [batch.schema.get_field_index(c) for c in columns]
        return pa.RecordBatch.from_arrays(
            [batch.column(i) for i in indices],
            names=columns,
        )

    async def get_estimated_size(self, object_name: str) -> Optional[int]:
        """
        Get estimated row count for planning.

        Args:
            object_name: Name of the object.

        Returns:
            Estimated row count or None if unavailable.
        """
        try:
            state = await self.connector.get_sync_state(object_name)
            return state.metadata.get("row_count")
        except Exception:
            return None
