"""
Base connector interfaces and data models.

This module defines the core abstractions that all connectors must implement:
- BaseConnector: Abstract base class for all connector implementations
- ConnectorConfig: Base configuration model extended by each connector type
- SyncState: Checkpoint state for incremental/CDC syncs
- SchemaObject: Discovered table/object/endpoint metadata
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Optional

import pyarrow as pa
from pydantic import BaseModel, Field


class ConnectorCapability(str, Enum):
    """Capabilities that a connector may support."""

    BATCH = "batch"
    INCREMENTAL = "incremental"
    CDC = "cdc"
    STREAMING = "streaming"
    WRITE_BATCH = "write_batch"
    WRITE_RECORD = "write_record"
    SCHEMA_DISCOVERY = "schema_discovery"
    DATA_PROFILING = "data_profiling"


class ConnectorConfig(BaseModel):
    """
    Base configuration for all connectors.

    Each connector type extends this with source-specific fields.
    Credentials should never be stored directly - use secrets_ref instead.
    """

    connector_type: str = Field(..., description="Type identifier (e.g., 'postgresql')")
    name: str = Field(..., description="User-friendly connection name")
    secrets_ref: Optional[str] = Field(
        default=None, description="Reference to external secrets (e.g., Vault path)"
    )

    model_config = {"extra": "forbid"}


class SyncState(BaseModel):
    """
    Checkpoint for incremental and CDC syncs.

    Stores cursor position and metadata to enable resumable syncs.
    """

    cursor: Optional[str] = Field(default=None, description="Cursor value for incremental sync")
    last_sync_at: Optional[datetime] = Field(
        default=None, description="Timestamp of last successful sync"
    )
    lsn: Optional[str] = Field(default=None, description="Log sequence number for CDC")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional connector-specific state"
    )


class ColumnInfo(BaseModel):
    """Schema information for a single column."""

    name: str
    data_type: str = Field(..., description="Source database type")
    arrow_type: Optional[str] = Field(default=None, description="Mapped Arrow type")
    nullable: bool = True
    description: Optional[str] = None
    is_primary_key: bool = False
    is_cursor_field: bool = Field(
        default=False, description="Can be used for incremental sync cursor"
    )


class SchemaObject(BaseModel):
    """
    Discovered table, view, collection, or endpoint.

    Represents a single syncable unit from the data source.
    """

    name: str = Field(..., description="Object name (table, collection, endpoint)")
    schema_name: Optional[str] = Field(default=None, description="Schema/namespace if applicable")
    object_type: str = Field(..., description="Type: 'table', 'view', 'collection', 'endpoint'")
    columns: list[ColumnInfo] = Field(default_factory=list)
    primary_key: Optional[list[str]] = Field(default=None, description="Primary key column(s)")
    supports_cdc: bool = Field(default=False, description="Whether CDC is available")
    supports_incremental: bool = Field(
        default=False, description="Whether incremental sync is available"
    )
    row_count: Optional[int] = Field(default=None, description="Estimated row count if available")

    @property
    def full_name(self) -> str:
        """Return fully qualified name (schema.name or just name)."""
        if self.schema_name:
            return f"{self.schema_name}.{self.name}"
        return self.name


class ConnectionTestResult(BaseModel):
    """Result of a connection test."""

    success: bool
    error: Optional[str] = None
    latency_ms: Optional[float] = Field(default=None, description="Connection latency in ms")
    server_version: Optional[str] = Field(default=None, description="Server version if available")


class HealthStatus(BaseModel):
    """Health check status for a connection."""

    healthy: bool
    last_check_at: datetime
    error: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class DataProfile(BaseModel):
    """Statistical profile of a data object."""

    object_name: str
    row_count: int
    column_count: int
    null_counts: dict[str, int] = Field(default_factory=dict)
    distinct_counts: dict[str, int] = Field(default_factory=dict)
    min_values: dict[str, Any] = Field(default_factory=dict)
    max_values: dict[str, Any] = Field(default_factory=dict)
    sample_values: dict[str, list[Any]] = Field(default_factory=dict)
    profiled_at: datetime = Field(default_factory=datetime.utcnow)


class CDCEvent(BaseModel):
    """Change data capture event."""

    operation: str = Field(..., description="'INSERT', 'UPDATE', or 'DELETE'")
    record: dict[str, Any]
    key: Optional[dict[str, Any]] = Field(default=None, description="Primary key values")
    timestamp: datetime
    lsn: Optional[str] = Field(default=None, description="Log sequence number")
    state: SyncState


class WriteResult(BaseModel):
    """Result of a write operation."""

    success_count: int = 0
    failure_count: int = 0
    errors: list[str] = Field(default_factory=list)


class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors.

    All connectors must implement the core abstract methods. Optional capabilities
    (CDC, streaming, writeback) raise NotImplementedError by default.

    Attributes:
        connector_type: Unique identifier (e.g., 'postgresql', 'snowflake')
        category: Connector category (e.g., 'sql', 'warehouse', 'streaming', 'api')

    Example:
        class MyConnector(BaseConnector):
            connector_type = "mydb"
            category = "sql"

            async def test_connection(self) -> ConnectionTestResult:
                # Implementation
                ...
    """

    connector_type: str
    category: str

    @classmethod
    def get_capabilities(cls) -> list[ConnectorCapability]:
        """
        Return the list of capabilities supported by this connector.

        Override in subclasses to declare supported features.
        """
        return [ConnectorCapability.BATCH, ConnectorCapability.SCHEMA_DISCOVERY]

    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        """
        Test the connection to the data source.

        Returns:
            ConnectionTestResult with success status and optional error/latency info.
        """
        ...

    @abstractmethod
    async def discover_schema(self) -> list[SchemaObject]:
        """
        Discover all available objects (tables, views, endpoints) in the data source.

        Returns:
            List of SchemaObject describing each discoverable object.
        """
        ...

    @abstractmethod
    async def get_sample_data(
        self, object_name: str, limit: int = 100
    ) -> pa.Table:
        """
        Retrieve sample data from an object for preview.

        Args:
            object_name: Name of the object to sample.
            limit: Maximum number of rows to return.

        Returns:
            PyArrow Table containing sample data.
        """
        ...

    @abstractmethod
    async def read_batch(
        self, object_name: str, state: Optional[SyncState] = None
    ) -> AsyncIterator[pa.RecordBatch]:
        """
        Read data in batches, optionally resuming from a sync state.

        Args:
            object_name: Name of the object to read.
            state: Optional sync state for incremental reads.

        Yields:
            PyArrow RecordBatch for each chunk of data.
        """
        ...

    @abstractmethod
    async def get_sync_state(self, object_name: str) -> SyncState:
        """
        Get the current sync state (cursor position) for an object.

        Args:
            object_name: Name of the object.

        Returns:
            SyncState representing current position.
        """
        ...

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """
        Perform a health check on the connection.

        Returns:
            HealthStatus indicating connection health.
        """
        ...

    async def close(self) -> None:
        """
        Close the connector and release resources.

        Override to implement cleanup logic (close connection pools, etc.).
        """
        pass

    # Optional capabilities - override in subclasses that support them

    async def profile_data(self, object_name: str) -> DataProfile:
        """
        Run statistical profiling on an object.

        Args:
            object_name: Name of the object to profile.

        Returns:
            DataProfile with statistics.

        Raises:
            NotImplementedError: If connector does not support profiling.
        """
        raise NotImplementedError(f"{self.connector_type} does not support data profiling")

    async def read_cdc(
        self, object_name: str, state: SyncState
    ) -> AsyncIterator[CDCEvent]:
        """
        Read change data capture events.

        Args:
            object_name: Name of the object to track changes on.
            state: Sync state with LSN/cursor for resumption.

        Yields:
            CDCEvent for each change.

        Raises:
            NotImplementedError: If connector does not support CDC.
        """
        raise NotImplementedError(f"{self.connector_type} does not support CDC")
        yield  # Make this a generator

    async def read_stream(self, object_name: str) -> AsyncIterator[dict[str, Any]]:
        """
        Read continuous stream of records.

        Args:
            object_name: Name of the stream/topic to read.

        Yields:
            Record dictionaries.

        Raises:
            NotImplementedError: If connector does not support streaming.
        """
        raise NotImplementedError(f"{self.connector_type} does not support streaming")
        yield  # Make this a generator

    async def write_batch(
        self, object_name: str, records: list[dict[str, Any]]
    ) -> WriteResult:
        """
        Write a batch of records to the destination.

        Args:
            object_name: Target object name.
            records: List of records to write.

        Returns:
            WriteResult with success/failure counts.

        Raises:
            NotImplementedError: If connector does not support batch writes.
        """
        raise NotImplementedError(f"{self.connector_type} does not support batch writes")

    async def write_record(self, object_name: str, record: dict[str, Any]) -> WriteResult:
        """
        Write a single record to the destination.

        Args:
            object_name: Target object name.
            record: Record to write.

        Returns:
            WriteResult with success/failure counts.

        Raises:
            NotImplementedError: If connector does not support single record writes.
        """
        raise NotImplementedError(f"{self.connector_type} does not support single record writes")

    async def __aenter__(self) -> "BaseConnector":
        """Support async context manager."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up on context exit."""
        await self.close()
