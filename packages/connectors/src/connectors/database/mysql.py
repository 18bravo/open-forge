"""
MySQL connector for Open Forge.
Provides async connection and data access for MySQL databases.
"""
from typing import Optional

from pydantic import Field

from connectors.base import ConnectorRegistry
from connectors.database.base_sql import BaseSQLConnector, SQLConnectorConfig


class MySQLConfig(SQLConnectorConfig):
    """Configuration for MySQL connector."""
    connector_type: str = Field(default="mysql", frozen=True)
    port: int = Field(default=3306, description="MySQL port")
    charset: str = Field(default="utf8mb4", description="Character set")
    ssl_mode: Optional[str] = Field(
        default=None,
        description="SSL mode: DISABLED, PREFERRED, REQUIRED, VERIFY_CA, VERIFY_IDENTITY"
    )

    @property
    def connection_string(self) -> str:
        """Generate async connection string for MySQL."""
        params = [f"charset={self.charset}"]
        if self.ssl_mode:
            params.append(f"ssl_mode={self.ssl_mode}")
        params_str = "&".join(params)
        return (
            f"mysql+aiomysql://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}?{params_str}"
        )


@ConnectorRegistry.register("mysql")
class MySQLConnector(BaseSQLConnector):
    """
    MySQL database connector.

    Uses aiomysql for async operations through SQLAlchemy.

    Example:
        config = MySQLConfig(
            name="my-mysql",
            host="localhost",
            port=3306,
            username="user",
            password="pass",
            database="mydb"
        )
        async with MySQLConnector(config) as conn:
            schemas = await conn.fetch_schema()
            sample = await conn.fetch_sample("users", limit=10)
    """

    def __init__(self, config: MySQLConfig):
        super().__init__(config)
        self.config: MySQLConfig = config

    def _get_tables_query(self) -> str:
        """Return query to list tables in MySQL."""
        return f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{self.config.database}'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """

    def _get_columns_query(self, table_name: str) -> str:
        """Return query to get column info for a MySQL table."""
        return f"""
            SELECT
                column_name,
                data_type,
                CASE WHEN is_nullable = 'YES' THEN 1 ELSE 0 END as is_nullable,
                CASE WHEN column_key = 'PRI' THEN 1 ELSE 0 END as is_primary
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            AND table_schema = '{self.config.database}'
            ORDER BY ordinal_position
        """

    def _map_db_type(self, db_type: str) -> str:
        """Map MySQL types to common type names."""
        type_map = {
            "int": "int",
            "integer": "int",
            "bigint": "long",
            "smallint": "short",
            "tinyint": "byte",
            "mediumint": "int",
            "decimal": "decimal",
            "numeric": "decimal",
            "float": "float",
            "double": "double",
            "real": "double",
            "varchar": "string",
            "char": "string",
            "text": "string",
            "tinytext": "string",
            "mediumtext": "string",
            "longtext": "string",
            "enum": "string",
            "set": "string",
            "bit": "boolean",
            "boolean": "boolean",
            "bool": "boolean",
            "date": "date",
            "datetime": "timestamp",
            "timestamp": "timestamp",
            "time": "time",
            "year": "int",
            "binary": "binary",
            "varbinary": "binary",
            "blob": "binary",
            "tinyblob": "binary",
            "mediumblob": "binary",
            "longblob": "binary",
            "json": "json",
        }
        return type_map.get(db_type.lower(), db_type)

    async def list_databases(self) -> list[str]:
        """List all databases on the server."""
        query = "SHOW DATABASES"
        results = await self.execute_query(query)
        return [r["Database"] for r in results]

    async def get_table_size(self, table_name: str) -> dict:
        """Get size information for a table."""
        query = f"""
            SELECT
                table_name,
                ROUND(data_length / 1024 / 1024, 2) as data_size_mb,
                ROUND(index_length / 1024 / 1024, 2) as index_size_mb,
                ROUND((data_length + index_length) / 1024 / 1024, 2) as total_size_mb,
                table_rows as estimated_rows
            FROM information_schema.tables
            WHERE table_schema = '{self.config.database}'
            AND table_name = '{table_name}'
        """
        results = await self.execute_query(query)
        return results[0] if results else {}

    async def get_indexes(self, table_name: str) -> list[dict]:
        """Get index information for a table."""
        query = f"""
            SELECT
                index_name as name,
                GROUP_CONCAT(column_name ORDER BY seq_in_index) as columns,
                CASE WHEN non_unique = 0 THEN 'unique' ELSE 'non-unique' END as type
            FROM information_schema.statistics
            WHERE table_schema = '{self.config.database}'
            AND table_name = '{table_name}'
            GROUP BY index_name, non_unique
        """
        return await self.execute_query(query)

    async def get_engine_status(self) -> list[dict]:
        """Get MySQL engine status."""
        query = "SHOW ENGINE INNODB STATUS"
        return await self.execute_query(query)
