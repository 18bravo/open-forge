"""
SQL database connectors.

Provides connectors for:
- PostgreSQL (with CDC via logical replication)
- MySQL / MariaDB
- SQL Server
- Oracle Database

All SQL connectors inherit from SQLConnector base class which provides
common functionality for SQL databases.
"""

from forge_connectors.connectors.sql.base import SQLConnector, SQLConnectorConfig
from forge_connectors.connectors.sql.postgresql import PostgreSQLConnector, PostgreSQLConfig

__all__ = [
    "SQLConnector",
    "SQLConnectorConfig",
    "PostgreSQLConnector",
    "PostgreSQLConfig",
]
