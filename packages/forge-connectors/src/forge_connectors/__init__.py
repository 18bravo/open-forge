"""
Forge Connectors - Unified connector framework for Open Forge.

This package provides:
- BaseConnector ABC for implementing data source connectors
- Connector registry for plugin-based discovery
- Sync engine supporting batch, CDC, incremental, and streaming modes
- Auth module for OAuth, service accounts, and secrets management
- Connection pooling and health monitoring

Example usage:
    from forge_connectors import ConnectorRegistry, BaseConnector
    from forge_connectors.connectors.sql import PostgreSQLConnector

    # Discover available connectors
    connectors = ConnectorRegistry.list_all()

    # Create a connector instance
    config = PostgreSQLConnector.Config(
        host="localhost",
        database="mydb",
        secrets_ref="vault/path/to/creds"
    )
    connector = PostgreSQLConnector(config, secrets_provider)

    # Test connection
    result = await connector.test_connection()
"""

from forge_connectors.core.base import (
    BaseConnector,
    ColumnInfo,
    ConnectorCapability,
    ConnectorConfig,
    ConnectionTestResult,
    DataProfile,
    HealthStatus,
    SchemaObject,
    SyncState,
)
from forge_connectors.core.pool import PoolConfig, ConnectionPool
from forge_connectors.core.registry import ConnectorRegistry, ConnectorInfo

__version__ = "0.1.0"

__all__ = [
    # Core
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorCapability",
    "ConnectionTestResult",
    "HealthStatus",
    "SchemaObject",
    "ColumnInfo",
    "SyncState",
    "DataProfile",
    # Registry
    "ConnectorRegistry",
    "ConnectorInfo",
    # Pool
    "PoolConfig",
    "ConnectionPool",
]
