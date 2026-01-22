"""
Incremental sync strategy for cursor-based extraction.

Handles incremental extraction using:
- Cursor fields (timestamp, sequence, etc.)
- Checkpoint persistence
- Resumable syncs
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Optional

import pyarrow as pa

from forge_connectors.core.base import BaseConnector, SyncState

logger = logging.getLogger(__name__)


@dataclass
class IncrementalConfig:
    """Configuration for incremental sync operations."""

    cursor_field: str  # Column to use as cursor
    batch_size: int = 10000
    lookback_window: Optional[int] = None  # Rows to re-read for late arrivals
    checkpoint_interval: int = 10000  # Checkpoint every N records


class IncrementalSyncStrategy:
    """
    Strategy for incremental extraction using a cursor field.

    Tracks position using a cursor field (typically timestamp or sequence)
    and only extracts new/modified records since last sync.

    Example:
        config = IncrementalConfig(cursor_field="updated_at")
        strategy = IncrementalSyncStrategy(connector, config)

        # Resume from saved state
        state = await state_store.get(job_id)
        async for batch, new_state in strategy.extract("orders", state):
            await writer.write(destination, batch)
            await state_store.save(job_id, new_state)
    """

    def __init__(self, connector: BaseConnector, config: IncrementalConfig):
        """
        Initialize incremental sync strategy.

        Args:
            connector: Source connector.
            config: Incremental configuration.
        """
        self.connector = connector
        self.config = config

    async def extract(
        self, object_name: str, state: Optional[SyncState] = None
    ) -> AsyncIterator[tuple[pa.RecordBatch, SyncState]]:
        """
        Extract incremental data from an object.

        Args:
            object_name: Name of the object to extract.
            state: Previous sync state for resumption.

        Yields:
            Tuple of (RecordBatch, updated SyncState).
        """
        current_state = state or SyncState()
        records_since_checkpoint = 0
        max_cursor_value: Optional[str] = current_state.cursor

        async for batch in self.connector.read_batch(object_name, state=current_state):
            # Track the maximum cursor value in this batch
            batch_max_cursor = self._get_max_cursor(batch)
            if batch_max_cursor and (not max_cursor_value or batch_max_cursor > max_cursor_value):
                max_cursor_value = batch_max_cursor

            records_since_checkpoint += batch.num_rows

            # Create updated state
            new_state = SyncState(
                cursor=max_cursor_value,
                last_sync_at=datetime.utcnow(),
                metadata={
                    "cursor_field": self.config.cursor_field,
                    "records_processed": current_state.metadata.get("records_processed", 0)
                    + batch.num_rows,
                },
            )

            yield batch, new_state

            # Update current state for checkpointing
            if records_since_checkpoint >= self.config.checkpoint_interval:
                current_state = new_state
                records_since_checkpoint = 0
                logger.debug(f"Checkpoint: cursor={max_cursor_value}")

        logger.info(
            f"Incremental extraction complete for {object_name}, "
            f"cursor={max_cursor_value}"
        )

    def _get_max_cursor(self, batch: pa.RecordBatch) -> Optional[str]:
        """Extract maximum cursor value from batch."""
        if self.config.cursor_field not in batch.schema.names:
            return None

        cursor_col = batch.column(self.config.cursor_field)
        if cursor_col.null_count == len(cursor_col):
            return None

        # Get max value
        max_val = cursor_col.to_pylist()
        non_null_values = [v for v in max_val if v is not None]
        if not non_null_values:
            return None

        max_cursor = max(non_null_values)

        # Convert to string for storage
        if isinstance(max_cursor, datetime):
            return max_cursor.isoformat()
        return str(max_cursor)

    async def detect_cursor_field(self, object_name: str) -> Optional[str]:
        """
        Auto-detect a suitable cursor field.

        Looks for timestamp or sequence columns that could be used for
        incremental sync.

        Args:
            object_name: Name of the object.

        Returns:
            Best cursor field name or None.
        """
        try:
            schemas = await self.connector.discover_schema()
            obj_schema = next(
                (s for s in schemas if s.name == object_name or s.full_name == object_name),
                None,
            )
            if not obj_schema:
                return None

            # Prefer columns marked as cursor fields
            cursor_cols = [c for c in obj_schema.columns if c.is_cursor_field]
            if cursor_cols:
                # Prefer timestamp types
                for col in cursor_cols:
                    if "timestamp" in col.data_type.lower() or "datetime" in col.data_type.lower():
                        return col.name
                return cursor_cols[0].name

            # Fall back to common naming patterns
            common_names = ["updated_at", "modified_at", "last_modified", "timestamp", "created_at"]
            for name in common_names:
                if any(c.name.lower() == name for c in obj_schema.columns):
                    return name

            return None
        except Exception as e:
            logger.warning(f"Could not detect cursor field: {e}")
            return None
