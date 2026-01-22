"""
Reverse ETL (writeback) engine for pushing data to operational systems.

Handles:
- Upsert, insert, update operations
- Batch writes with error handling
- Field mapping from ontology to target
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from forge_connectors.core.base import BaseConnector, WriteResult

logger = logging.getLogger(__name__)


class WriteMode(str, Enum):
    """Supported write modes for reverse ETL."""

    INSERT = "insert"  # Insert only, fail on duplicates
    UPDATE = "update"  # Update only, fail if not exists
    UPSERT = "upsert"  # Insert or update based on key


@dataclass
class WritebackJob:
    """
    Definition of a writeback (reverse ETL) job.

    Describes source query, target, and field mappings.
    """

    id: str
    connection_id: str
    connector_type: str
    target_object: str  # e.g., 'salesforce.Contact'
    source_query: str  # Query against data warehouse or ontology
    mapping: dict[str, str]  # Source field -> Target field
    mode: WriteMode = WriteMode.UPSERT
    key_fields: list[str] = field(default_factory=list)  # Fields for upsert matching
    batch_size: int = 100
    fail_on_error: bool = False  # Whether to stop on first error
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WritebackResult:
    """Result of a writeback operation."""

    success: bool
    job_id: str
    records_attempted: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class WritebackEngine:
    """
    Engine for reverse ETL operations.

    Pushes data from the data platform back to operational systems
    like CRM, ERP, or transactional databases.

    Example:
        engine = WritebackEngine(
            connector_factory=connector_factory,
            query_executor=ontology_query,
        )

        result = await engine.execute_writeback(job)
    """

    def __init__(
        self,
        connector_factory: Any,  # Factory to create connector instances
        query_executor: Any,  # Callable to execute source queries
    ):
        """
        Initialize the writeback engine.

        Args:
            connector_factory: Factory for creating connector instances.
            query_executor: Executor for source queries.
        """
        self.connector_factory = connector_factory
        self.query_executor = query_executor

    async def execute_writeback(self, job: WritebackJob) -> WritebackResult:
        """
        Execute a writeback job.

        Args:
            job: The writeback job to execute.

        Returns:
            WritebackResult with outcome details.
        """
        logger.info(f"Starting writeback job {job.id}: {job.target_object}")

        result = WritebackResult(
            success=True,
            job_id=job.id,
            started_at=datetime.utcnow(),
        )

        try:
            # Create target connector
            connector = await self.connector_factory.create(
                job.connector_type, job.connection_id
            )

            # Query source data
            records = await self.query_executor(job.source_query)
            result.records_attempted = len(records)

            # Map fields and write in batches
            for batch_start in range(0, len(records), job.batch_size):
                batch_end = min(batch_start + job.batch_size, len(records))
                batch_records = records[batch_start:batch_end]

                # Apply field mapping
                mapped_records = [
                    self._map_record(record, job.mapping) for record in batch_records
                ]

                # Write batch
                try:
                    write_result = await self._write_batch(
                        connector, job.target_object, mapped_records, job.mode
                    )
                    result.records_succeeded += write_result.success_count
                    result.records_failed += write_result.failure_count

                    if write_result.errors:
                        result.errors.extend(
                            [{"batch": batch_start, "error": e} for e in write_result.errors]
                        )

                    if job.fail_on_error and write_result.failure_count > 0:
                        result.success = False
                        break

                except Exception as e:
                    error_msg = f"Batch {batch_start}-{batch_end} failed: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append({"batch": batch_start, "error": error_msg})
                    result.records_failed += len(mapped_records)

                    if job.fail_on_error:
                        result.success = False
                        break

        except Exception as e:
            logger.error(f"Writeback job {job.id} failed: {e}")
            result.success = False
            result.errors.append({"error": str(e)})

        result.completed_at = datetime.utcnow()
        result.success = result.success and result.records_failed == 0

        logger.info(
            f"Writeback complete: {result.records_succeeded}/{result.records_attempted} "
            f"succeeded, {result.records_failed} failed"
        )

        return result

    def _map_record(
        self, record: dict[str, Any], mapping: dict[str, str]
    ) -> dict[str, Any]:
        """
        Apply field mapping to a record.

        Args:
            record: Source record.
            mapping: Source field -> Target field mapping.

        Returns:
            Mapped record with target field names.
        """
        mapped: dict[str, Any] = {}

        for source_field, target_field in mapping.items():
            if source_field in record:
                mapped[target_field] = record[source_field]

        return mapped

    async def _write_batch(
        self,
        connector: BaseConnector,
        target_object: str,
        records: list[dict[str, Any]],
        mode: WriteMode,
    ) -> WriteResult:
        """
        Write a batch of records using the appropriate method.

        Args:
            connector: Target connector.
            target_object: Target object name.
            records: Records to write.
            mode: Write mode.

        Returns:
            WriteResult with counts.
        """
        return await connector.write_batch(target_object, records)

    async def validate_job(self, job: WritebackJob) -> list[str]:
        """
        Validate a writeback job configuration.

        Args:
            job: Job to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        errors: list[str] = []

        if not job.target_object:
            errors.append("target_object is required")

        if not job.source_query:
            errors.append("source_query is required")

        if not job.mapping:
            errors.append("mapping is required")

        if job.mode == WriteMode.UPSERT and not job.key_fields:
            errors.append("key_fields required for upsert mode")

        return errors

    async def preview_writeback(
        self, job: WritebackJob, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Preview records that would be written.

        Args:
            job: Writeback job.
            limit: Maximum records to preview.

        Returns:
            List of mapped records.
        """
        # Execute source query with limit
        preview_query = f"({job.source_query}) LIMIT {limit}"
        try:
            records = await self.query_executor(preview_query)
        except Exception:
            # If adding LIMIT fails, just execute and slice
            records = await self.query_executor(job.source_query)
            records = records[:limit]

        return [self._map_record(r, job.mapping) for r in records]
