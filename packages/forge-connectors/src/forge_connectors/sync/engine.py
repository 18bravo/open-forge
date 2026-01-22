"""
Unified sync engine that orchestrates data synchronization across all modes.

The sync engine supports:
- Full/batch extraction
- Incremental extraction with cursor-based checkpointing
- CDC (Change Data Capture) with merge operations
- Streaming continuous ingestion
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import pyarrow as pa

from forge_connectors.core.base import BaseConnector, CDCEvent, SyncState

logger = logging.getLogger(__name__)


class SyncMode(str, Enum):
    """Supported synchronization modes."""

    FULL = "full"  # Complete extraction, replace destination
    INCREMENTAL = "incremental"  # Cursor-based incremental append
    CDC = "cdc"  # Change data capture with merge
    STREAMING = "streaming"  # Continuous real-time stream


@dataclass
class SyncJob:
    """
    Definition of a sync job.

    Describes what to sync, how to sync it, and where to write.
    """

    id: str
    connection_id: str
    connector_type: str
    object_name: str
    mode: SyncMode
    destination: str  # Target location (e.g., Iceberg table path)
    cursor_field: Optional[str] = None  # For incremental mode
    state: Optional[SyncState] = None
    schedule: Optional[str] = None  # Cron expression for scheduling
    batch_size: int = 10000
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SyncResult:
    """Result of a sync operation."""

    success: bool
    job_id: str
    mode: SyncMode
    records_read: int = 0
    records_written: int = 0
    bytes_written: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    changes: Optional[dict[str, int]] = None  # For CDC: {'inserts': N, 'updates': N, 'deletes': N}
    new_state: Optional[SyncState] = None


class StateStore(ABC):
    """
    Abstract interface for persisting sync state.

    Implementations store checkpoint state in database, file, etc.
    """

    @abstractmethod
    async def get(self, job_id: str) -> Optional[SyncState]:
        """Get the current state for a job."""
        ...

    @abstractmethod
    async def save(self, job_id: str, state: SyncState) -> None:
        """Save state for a job."""
        ...

    @abstractmethod
    async def delete(self, job_id: str) -> None:
        """Delete state for a job."""
        ...


class InMemoryStateStore(StateStore):
    """In-memory state store for testing."""

    def __init__(self) -> None:
        self._states: dict[str, SyncState] = {}

    async def get(self, job_id: str) -> Optional[SyncState]:
        return self._states.get(job_id)

    async def save(self, job_id: str, state: SyncState) -> None:
        self._states[job_id] = state

    async def delete(self, job_id: str) -> None:
        self._states.pop(job_id, None)


class DataWriter(ABC):
    """
    Abstract interface for writing data to destinations.

    Implementations write to Iceberg, Parquet, databases, etc.
    """

    @abstractmethod
    async def write(
        self,
        destination: str,
        batch: pa.RecordBatch,
        mode: str = "append",
    ) -> int:
        """
        Write a batch of records.

        Args:
            destination: Target location.
            batch: Data to write.
            mode: Write mode ('append', 'overwrite').

        Returns:
            Number of bytes written.
        """
        ...

    @abstractmethod
    async def merge(
        self,
        destination: str,
        record: dict[str, Any],
        key: dict[str, Any],
    ) -> None:
        """
        Merge a record (upsert) based on key.

        Args:
            destination: Target location.
            record: Record data.
            key: Primary key values.
        """
        ...

    @abstractmethod
    async def delete(
        self,
        destination: str,
        key: dict[str, Any],
    ) -> None:
        """
        Delete a record by key.

        Args:
            destination: Target location.
            key: Primary key values.
        """
        ...


class SyncEngine:
    """
    Orchestrates data synchronization across all modes.

    The sync engine creates connector instances, manages state,
    and delegates to mode-specific strategies.

    Example:
        engine = SyncEngine(
            connector_factory=connector_factory,
            state_store=state_store,
            writer=iceberg_writer,
        )

        result = await engine.execute_sync(job)
    """

    def __init__(
        self,
        connector_factory: Any,  # Factory to create connector instances
        state_store: StateStore,
        writer: DataWriter,
        checkpoint_interval: int = 10000,
    ):
        """
        Initialize the sync engine.

        Args:
            connector_factory: Factory for creating connector instances.
            state_store: Store for persisting sync state.
            writer: Writer for destination data.
            checkpoint_interval: How often to checkpoint during sync.
        """
        self.connector_factory = connector_factory
        self.state_store = state_store
        self.writer = writer
        self.checkpoint_interval = checkpoint_interval

    async def execute_sync(self, job: SyncJob) -> SyncResult:
        """
        Execute a sync job.

        Args:
            job: The sync job to execute.

        Returns:
            SyncResult with outcome details.
        """
        logger.info(f"Starting sync job {job.id}: {job.object_name} ({job.mode.value})")

        try:
            # Create connector
            connector = await self.connector_factory.create(
                job.connector_type, job.connection_id
            )

            # Get or initialize state
            state = await self.state_store.get(job.id) or SyncState()

            # Execute based on mode
            match job.mode:
                case SyncMode.FULL:
                    return await self._sync_full(connector, job, state)
                case SyncMode.INCREMENTAL:
                    return await self._sync_incremental(connector, job, state)
                case SyncMode.CDC:
                    return await self._sync_cdc(connector, job, state)
                case SyncMode.STREAMING:
                    return await self._sync_streaming(connector, job, state)

        except Exception as e:
            logger.error(f"Sync job {job.id} failed: {e}")
            return SyncResult(
                success=False,
                job_id=job.id,
                mode=job.mode,
                error=str(e),
                completed_at=datetime.utcnow(),
            )

    async def _sync_full(
        self, connector: BaseConnector, job: SyncJob, state: SyncState
    ) -> SyncResult:
        """Execute full table extraction."""
        records_written = 0
        bytes_written = 0
        first_batch = True

        async for batch in connector.read_batch(job.object_name):
            # First batch overwrites, subsequent append
            mode = "overwrite" if first_batch else "append"
            bytes_written += await self.writer.write(job.destination, batch, mode=mode)
            records_written += batch.num_rows
            first_batch = False

            logger.debug(f"Wrote batch: {batch.num_rows} rows")

        # Save final state
        new_state = await connector.get_sync_state(job.object_name)
        await self.state_store.save(job.id, new_state)

        return SyncResult(
            success=True,
            job_id=job.id,
            mode=SyncMode.FULL,
            records_read=records_written,
            records_written=records_written,
            bytes_written=bytes_written,
            completed_at=datetime.utcnow(),
            new_state=new_state,
        )

    async def _sync_incremental(
        self, connector: BaseConnector, job: SyncJob, state: SyncState
    ) -> SyncResult:
        """Execute incremental extraction with cursor."""
        records_written = 0
        bytes_written = 0
        current_state = state

        async for batch in connector.read_batch(job.object_name, state=state):
            bytes_written += await self.writer.write(job.destination, batch, mode="append")
            records_written += batch.num_rows

            # Checkpoint periodically
            if records_written % self.checkpoint_interval == 0:
                current_state = await connector.get_sync_state(job.object_name)
                await self.state_store.save(job.id, current_state)
                logger.debug(f"Checkpoint at {records_written} records")

        # Final state save
        new_state = await connector.get_sync_state(job.object_name)
        await self.state_store.save(job.id, new_state)

        return SyncResult(
            success=True,
            job_id=job.id,
            mode=SyncMode.INCREMENTAL,
            records_read=records_written,
            records_written=records_written,
            bytes_written=bytes_written,
            completed_at=datetime.utcnow(),
            new_state=new_state,
        )

    async def _sync_cdc(
        self, connector: BaseConnector, job: SyncJob, state: SyncState
    ) -> SyncResult:
        """Execute CDC sync with merge operations."""
        changes: dict[str, int] = {"inserts": 0, "updates": 0, "deletes": 0}
        current_state = state

        async for event in connector.read_cdc(job.object_name, state):
            event: CDCEvent
            match event.operation:
                case "INSERT":
                    # Convert single record to batch for writing
                    await self._write_single_record(job.destination, event.record)
                    changes["inserts"] += 1
                case "UPDATE":
                    if event.key:
                        await self.writer.merge(job.destination, event.record, event.key)
                    changes["updates"] += 1
                case "DELETE":
                    if event.key:
                        await self.writer.delete(job.destination, event.key)
                    changes["deletes"] += 1

            # Update state after each event
            current_state = event.state

            # Checkpoint periodically
            total_changes = sum(changes.values())
            if total_changes % self.checkpoint_interval == 0:
                await self.state_store.save(job.id, current_state)

        await self.state_store.save(job.id, current_state)

        return SyncResult(
            success=True,
            job_id=job.id,
            mode=SyncMode.CDC,
            records_read=sum(changes.values()),
            records_written=changes["inserts"] + changes["updates"],
            completed_at=datetime.utcnow(),
            changes=changes,
            new_state=current_state,
        )

    async def _sync_streaming(
        self, connector: BaseConnector, job: SyncJob, state: SyncState
    ) -> SyncResult:
        """
        Execute continuous streaming sync.

        Note: This is a simplified implementation. Production streaming
        would run continuously with proper shutdown handling.
        """
        records_written = 0
        batch_records: list[dict[str, Any]] = []

        async for record in connector.read_stream(job.object_name):
            batch_records.append(record)

            # Batch writes for efficiency
            if len(batch_records) >= job.batch_size:
                batch = self._records_to_batch(batch_records)
                await self.writer.write(job.destination, batch, mode="append")
                records_written += len(batch_records)
                batch_records = []

        # Write remaining records
        if batch_records:
            batch = self._records_to_batch(batch_records)
            await self.writer.write(job.destination, batch, mode="append")
            records_written += len(batch_records)

        return SyncResult(
            success=True,
            job_id=job.id,
            mode=SyncMode.STREAMING,
            records_read=records_written,
            records_written=records_written,
            completed_at=datetime.utcnow(),
        )

    async def _write_single_record(self, destination: str, record: dict[str, Any]) -> None:
        """Helper to write a single record as a batch."""
        batch = self._records_to_batch([record])
        await self.writer.write(destination, batch, mode="append")

    def _records_to_batch(self, records: list[dict[str, Any]]) -> pa.RecordBatch:
        """Convert list of records to PyArrow RecordBatch."""
        if not records:
            return pa.RecordBatch.from_pylist([])

        # Infer schema from first record
        table = pa.Table.from_pylist(records)
        return table.to_batches()[0] if table.num_rows > 0 else pa.RecordBatch.from_pylist([])
