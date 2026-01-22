"""Tests for base connector classes and models."""

from datetime import datetime, timedelta

import pytest

from forge_connectors.core.base import (
    CDCEvent,
    ColumnInfo,
    ConnectionTestResult,
    ConnectorCapability,
    ConnectorConfig,
    DataProfile,
    HealthStatus,
    SchemaObject,
    SyncState,
    WriteResult,
)


class TestConnectorConfig:
    """Tests for ConnectorConfig."""

    def test_basic_config(self):
        """Test basic configuration."""
        config = ConnectorConfig(
            connector_type="postgresql",
            name="My DB",
            secrets_ref="vault/path",
        )
        assert config.connector_type == "postgresql"
        assert config.name == "My DB"
        assert config.secrets_ref == "vault/path"

    def test_config_without_secrets(self):
        """Test configuration without secrets reference."""
        config = ConnectorConfig(
            connector_type="test",
            name="Test",
        )
        assert config.secrets_ref is None


class TestSyncState:
    """Tests for SyncState."""

    def test_empty_state(self):
        """Test empty sync state."""
        state = SyncState()
        assert state.cursor is None
        assert state.last_sync_at is None
        assert state.lsn is None
        assert state.metadata == {}

    def test_state_with_cursor(self):
        """Test sync state with cursor."""
        state = SyncState(
            cursor="2024-01-01T00:00:00",
            last_sync_at=datetime.utcnow(),
            metadata={"records_processed": 1000},
        )
        assert state.cursor == "2024-01-01T00:00:00"
        assert state.metadata["records_processed"] == 1000


class TestColumnInfo:
    """Tests for ColumnInfo."""

    def test_column_info(self):
        """Test column information."""
        col = ColumnInfo(
            name="created_at",
            data_type="timestamp",
            arrow_type="timestamp[us]",
            nullable=False,
            is_primary_key=False,
            is_cursor_field=True,
        )
        assert col.name == "created_at"
        assert col.data_type == "timestamp"
        assert col.is_cursor_field is True


class TestSchemaObject:
    """Tests for SchemaObject."""

    def test_schema_object(self):
        """Test schema object creation."""
        obj = SchemaObject(
            name="orders",
            schema_name="public",
            object_type="table",
            columns=[
                ColumnInfo(name="id", data_type="integer"),
                ColumnInfo(name="total", data_type="numeric"),
            ],
            primary_key=["id"],
            supports_cdc=True,
            supports_incremental=True,
        )
        assert obj.name == "orders"
        assert obj.full_name == "public.orders"
        assert len(obj.columns) == 2
        assert obj.supports_cdc is True

    def test_full_name_without_schema(self):
        """Test full name when schema is not set."""
        obj = SchemaObject(
            name="collection",
            object_type="collection",
        )
        assert obj.full_name == "collection"


class TestConnectionTestResult:
    """Tests for ConnectionTestResult."""

    def test_successful_result(self):
        """Test successful connection result."""
        result = ConnectionTestResult(
            success=True,
            latency_ms=15.5,
            server_version="PostgreSQL 15.2",
        )
        assert result.success is True
        assert result.latency_ms == 15.5
        assert result.error is None

    def test_failed_result(self):
        """Test failed connection result."""
        result = ConnectionTestResult(
            success=False,
            error="Connection refused",
        )
        assert result.success is False
        assert result.error == "Connection refused"


class TestHealthStatus:
    """Tests for HealthStatus."""

    def test_healthy_status(self):
        """Test healthy status."""
        status = HealthStatus(
            healthy=True,
            last_check_at=datetime.utcnow(),
            details={"connections": 5},
        )
        assert status.healthy is True
        assert "connections" in status.details

    def test_unhealthy_status(self):
        """Test unhealthy status."""
        status = HealthStatus(
            healthy=False,
            last_check_at=datetime.utcnow(),
            error="Database unavailable",
        )
        assert status.healthy is False
        assert status.error is not None


class TestDataProfile:
    """Tests for DataProfile."""

    def test_data_profile(self):
        """Test data profile creation."""
        profile = DataProfile(
            object_name="orders",
            row_count=10000,
            column_count=5,
            null_counts={"notes": 500},
            distinct_counts={"status": 3},
            min_values={"total": 0.01},
            max_values={"total": 9999.99},
        )
        assert profile.row_count == 10000
        assert profile.null_counts["notes"] == 500


class TestCDCEvent:
    """Tests for CDCEvent."""

    def test_insert_event(self):
        """Test CDC insert event."""
        event = CDCEvent(
            operation="INSERT",
            record={"id": 1, "name": "test"},
            key={"id": 1},
            timestamp=datetime.utcnow(),
            lsn="0/1234567",
            state=SyncState(lsn="0/1234567"),
        )
        assert event.operation == "INSERT"
        assert event.record["id"] == 1


class TestWriteResult:
    """Tests for WriteResult."""

    def test_successful_write(self):
        """Test successful write result."""
        result = WriteResult(
            success_count=100,
            failure_count=0,
        )
        assert result.success_count == 100
        assert result.failure_count == 0

    def test_partial_write(self):
        """Test partial write with errors."""
        result = WriteResult(
            success_count=95,
            failure_count=5,
            errors=["Duplicate key", "Null value", "Constraint violation"],
        )
        assert result.success_count == 95
        assert result.failure_count == 5
        assert len(result.errors) == 3


class TestConnectorCapability:
    """Tests for ConnectorCapability enum."""

    def test_capabilities(self):
        """Test capability enum values."""
        assert ConnectorCapability.BATCH.value == "batch"
        assert ConnectorCapability.CDC.value == "cdc"
        assert ConnectorCapability.STREAMING.value == "streaming"
        assert ConnectorCapability.WRITE_BATCH.value == "write_batch"
