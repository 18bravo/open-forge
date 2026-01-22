"""
Core module - BaseConnector ABC, registry, schema discovery, data profiling, connection pooling.
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
from forge_connectors.core.pool import ConnectionPool, PoolConfig
from forge_connectors.core.registry import ConnectorInfo, ConnectorRegistry

__all__ = [
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorCapability",
    "ConnectionTestResult",
    "HealthStatus",
    "SchemaObject",
    "ColumnInfo",
    "SyncState",
    "DataProfile",
    "ConnectorRegistry",
    "ConnectorInfo",
    "PoolConfig",
    "ConnectionPool",
]
