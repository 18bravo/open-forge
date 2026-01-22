"""Tests for connector registry."""

import pytest

from forge_connectors.core.base import BaseConnector, ConnectorCapability, ConnectionTestResult
from forge_connectors.core.registry import (
    ConnectorInfo,
    ConnectorNotFoundError,
    ConnectorRegistry,
)


class MockConnector(BaseConnector):
    """Mock connector for testing."""

    connector_type = "mock"
    category = "test"

    async def test_connection(self) -> ConnectionTestResult:
        return ConnectionTestResult(success=True)

    async def discover_schema(self):
        return []

    async def get_sample_data(self, object_name: str, limit: int = 100):
        import pyarrow as pa

        return pa.Table.from_pylist([])

    async def read_batch(self, object_name: str, state=None):
        return
        yield  # Make this a generator

    async def get_sync_state(self, object_name: str):
        from forge_connectors.core.base import SyncState

        return SyncState()

    async def health_check(self):
        from datetime import datetime

        from forge_connectors.core.base import HealthStatus

        return HealthStatus(healthy=True, last_check_at=datetime.utcnow())


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry before and after each test."""
    ConnectorRegistry.clear()
    yield
    ConnectorRegistry.clear()


def test_register_connector():
    """Test registering a connector."""

    @ConnectorRegistry.register("test-db", "sql", "Test database connector")
    class TestConnector(MockConnector):
        pass

    assert ConnectorRegistry.is_registered("test-db")
    assert TestConnector.connector_type == "test-db"
    assert TestConnector.category == "sql"


def test_get_registered_connector():
    """Test getting a registered connector."""

    @ConnectorRegistry.register("test-db", "sql")
    class TestConnector(MockConnector):
        pass

    retrieved = ConnectorRegistry.get("test-db")
    assert retrieved is TestConnector


def test_get_unregistered_connector_raises():
    """Test that getting an unregistered connector raises error."""
    with pytest.raises(ConnectorNotFoundError):
        ConnectorRegistry.get("nonexistent")


def test_list_all_connectors():
    """Test listing all registered connectors."""

    @ConnectorRegistry.register("db1", "sql")
    class Connector1(MockConnector):
        pass

    @ConnectorRegistry.register("db2", "warehouse")
    class Connector2(MockConnector):
        pass

    connectors = ConnectorRegistry.list_all()
    assert len(connectors) == 2

    types = {c.connector_type for c in connectors}
    assert types == {"db1", "db2"}


def test_list_by_category():
    """Test listing connectors by category."""

    @ConnectorRegistry.register("pg", "sql")
    class PGConnector(MockConnector):
        pass

    @ConnectorRegistry.register("mysql", "sql")
    class MySQLConnector(MockConnector):
        pass

    @ConnectorRegistry.register("snowflake", "warehouse")
    class SnowflakeConnector(MockConnector):
        pass

    sql_connectors = ConnectorRegistry.list_by_category("sql")
    assert len(sql_connectors) == 2

    warehouse_connectors = ConnectorRegistry.list_by_category("warehouse")
    assert len(warehouse_connectors) == 1


def test_get_categories():
    """Test getting list of categories."""

    @ConnectorRegistry.register("pg", "sql")
    class PGConnector(MockConnector):
        pass

    @ConnectorRegistry.register("kafka", "streaming")
    class KafkaConnector(MockConnector):
        pass

    categories = ConnectorRegistry.get_categories()
    assert set(categories) == {"sql", "streaming"}


def test_connector_info():
    """Test ConnectorInfo dataclass."""
    info = ConnectorInfo(
        connector_type="test",
        category="sql",
        capabilities=[ConnectorCapability.BATCH, ConnectorCapability.CDC],
        description="Test connector",
    )

    assert info.connector_type == "test"
    assert info.category == "sql"
    assert len(info.capabilities) == 2


def test_capabilities_from_class():
    """Test that capabilities are retrieved from connector class."""

    @ConnectorRegistry.register("custom", "sql")
    class CustomConnector(MockConnector):
        @classmethod
        def get_capabilities(cls):
            return [
                ConnectorCapability.BATCH,
                ConnectorCapability.INCREMENTAL,
                ConnectorCapability.CDC,
            ]

    connectors = ConnectorRegistry.list_all()
    assert len(connectors) == 1

    info = connectors[0]
    assert ConnectorCapability.CDC in info.capabilities
