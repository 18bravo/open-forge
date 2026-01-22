"""
Streaming sync strategy for continuous data ingestion.

Handles real-time streaming with:
- Continuous record consumption
- Micro-batch buffering
- Graceful shutdown
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Callable, Optional

import pyarrow as pa

from forge_connectors.core.base import BaseConnector

logger = logging.getLogger(__name__)


@dataclass
class StreamingConfig:
    """Configuration for streaming sync operations."""

    buffer_size: int = 1000  # Records to buffer before flush
    flush_interval: timedelta = field(default_factory=lambda: timedelta(seconds=10))
    max_batch_wait: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    shutdown_timeout: timedelta = field(default_factory=lambda: timedelta(seconds=60))


@dataclass
class StreamingStats:
    """Statistics for streaming operations."""

    records_received: int = 0
    records_written: int = 0
    batches_written: int = 0
    errors: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_record_at: Optional[datetime] = None


class StreamingSyncStrategy:
    """
    Strategy for continuous streaming ingestion.

    Consumes records continuously from streaming sources, buffering
    and flushing to destination in micro-batches.

    Example:
        config = StreamingConfig(buffer_size=1000, flush_interval=timedelta(seconds=5))
        strategy = StreamingSyncStrategy(connector, config)

        async def write_batch(batch: pa.RecordBatch) -> None:
            await writer.write(destination, batch)

        await strategy.start("orders_stream", write_batch)
    """

    def __init__(self, connector: BaseConnector, config: Optional[StreamingConfig] = None):
        """
        Initialize streaming sync strategy.

        Args:
            connector: Source connector (must support streaming).
            config: Streaming configuration.
        """
        self.connector = connector
        self.config = config or StreamingConfig()
        self._buffer: list[dict[str, Any]] = []
        self._running = False
        self._stats = StreamingStats()
        self._flush_task: Optional[asyncio.Task[None]] = None

    async def start(
        self,
        object_name: str,
        write_callback: Callable[[pa.RecordBatch], Any],
    ) -> StreamingStats:
        """
        Start continuous streaming ingestion.

        Args:
            object_name: Name of the stream/topic to consume.
            write_callback: Async callback to write batches.

        Returns:
            Final streaming statistics.
        """
        self._running = True
        self._stats = StreamingStats()

        # Start periodic flush task
        self._flush_task = asyncio.create_task(
            self._periodic_flush(write_callback)
        )

        try:
            async for record in self.connector.read_stream(object_name):
                if not self._running:
                    break

                self._buffer.append(record)
                self._stats.records_received += 1
                self._stats.last_record_at = datetime.utcnow()

                # Flush if buffer is full
                if len(self._buffer) >= self.config.buffer_size:
                    await self._flush_buffer(write_callback)

        except asyncio.CancelledError:
            logger.info("Streaming cancelled")
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            self._stats.errors += 1
            raise
        finally:
            # Final flush
            if self._buffer:
                await self._flush_buffer(write_callback)

            # Stop periodic flush
            if self._flush_task:
                self._flush_task.cancel()
                try:
                    await self._flush_task
                except asyncio.CancelledError:
                    pass

            self._running = False

        return self._stats

    async def stop(self) -> None:
        """
        Gracefully stop streaming.

        Allows current records to be processed before shutdown.
        """
        logger.info("Stopping streaming...")
        self._running = False

    async def _flush_buffer(
        self, write_callback: Callable[[pa.RecordBatch], Any]
    ) -> None:
        """Flush buffered records to destination."""
        if not self._buffer:
            return

        try:
            batch = self._records_to_batch(self._buffer)
            await write_callback(batch)
            self._stats.records_written += len(self._buffer)
            self._stats.batches_written += 1
            logger.debug(f"Flushed {len(self._buffer)} records")
        except Exception as e:
            logger.error(f"Failed to flush buffer: {e}")
            self._stats.errors += 1
            raise
        finally:
            self._buffer = []

    async def _periodic_flush(
        self, write_callback: Callable[[pa.RecordBatch], Any]
    ) -> None:
        """Periodically flush buffer based on time interval."""
        while self._running:
            try:
                await asyncio.sleep(self.config.flush_interval.total_seconds())
                if self._buffer and self._running:
                    await self._flush_buffer(write_callback)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")

    def _records_to_batch(self, records: list[dict[str, Any]]) -> pa.RecordBatch:
        """Convert list of records to PyArrow RecordBatch."""
        if not records:
            return pa.RecordBatch.from_pylist([])

        table = pa.Table.from_pylist(records)
        return table.to_batches()[0] if table.num_rows > 0 else pa.RecordBatch.from_pylist([])

    def get_stats(self) -> StreamingStats:
        """Get current streaming statistics."""
        return self._stats

    @property
    def is_running(self) -> bool:
        """Check if streaming is currently active."""
        return self._running

    async def consume_bounded(
        self,
        object_name: str,
        max_records: int,
        timeout: Optional[timedelta] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Consume a bounded number of records from stream.

        Useful for testing or bounded streaming scenarios.

        Args:
            object_name: Name of the stream/topic.
            max_records: Maximum records to consume.
            timeout: Maximum time to wait.

        Yields:
            Individual records from the stream.
        """
        records_consumed = 0
        start_time = datetime.utcnow()

        async for record in self.connector.read_stream(object_name):
            yield record
            records_consumed += 1

            if records_consumed >= max_records:
                break

            if timeout and datetime.utcnow() - start_time > timeout:
                logger.info(f"Streaming timeout after {timeout}")
                break
