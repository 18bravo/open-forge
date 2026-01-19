"""
Open Forge Connectors Package

Data source connectors for various systems including databases,
APIs, and file storage.
"""

from connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorRegistry,
    ConnectionStatus,
    ConnectionTestResult,
    DataSchema,
    SchemaField,
    SampleData,
)

from connectors.discovery import (
    DataDiscovery,
    DataProfile,
    DiscoveryResult,
    FieldStatistics,
    DataSourceScanner,
    SchemaComparator,
    DataQualityChecker,
    DataType,
)

# Database connectors
from connectors.database.base_sql import BaseSQLConnector, SQLConnectorConfig
from connectors.database.postgres import PostgresConnector, PostgresConfig
from connectors.database.mysql import MySQLConnector, MySQLConfig

# API connectors
from connectors.api.rest import RESTConnector, RESTConfig
from connectors.api.graphql import GraphQLConnector, GraphQLConfig

# File connectors
from connectors.file.csv import CSVConnector, CSVConfig
from connectors.file.parquet import ParquetConnector, ParquetConfig
from connectors.file.s3 import S3Connector, S3Config

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Base classes
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorRegistry",
    "ConnectionStatus",
    "ConnectionTestResult",
    "DataSchema",
    "SchemaField",
    "SampleData",
    # Discovery and profiling
    "DataDiscovery",
    "DataProfile",
    "DiscoveryResult",
    "FieldStatistics",
    "DataSourceScanner",
    "SchemaComparator",
    "DataQualityChecker",
    "DataType",
    # Database connectors
    "BaseSQLConnector",
    "SQLConnectorConfig",
    "PostgresConnector",
    "PostgresConfig",
    "MySQLConnector",
    "MySQLConfig",
    # API connectors
    "RESTConnector",
    "RESTConfig",
    "GraphQLConnector",
    "GraphQLConfig",
    # File connectors
    "CSVConnector",
    "CSVConfig",
    "ParquetConnector",
    "ParquetConfig",
    "S3Connector",
    "S3Config",
]
