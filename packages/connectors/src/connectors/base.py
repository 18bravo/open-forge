"""
Base connector classes and registry for Open Forge.
Provides abstract base classes for all data source connectors.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ConnectionStatus(str, Enum):
    """Status of a connector connection."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class ConnectorConfig(BaseSettings):
    """Base configuration for all connectors."""
    name: str = Field(..., description="Unique name for this connector instance")
    connector_type: str = Field(..., description="Type identifier for the connector")
    enabled: bool = Field(default=True, description="Whether this connector is enabled")
    timeout_seconds: int = Field(default=30, description="Connection timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts on failure")
    retry_delay_seconds: float = Field(default=1.0, description="Delay between retries")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {"extra": "allow"}


class SchemaField(BaseModel):
    """Represents a field in a data schema."""
    name: str
    data_type: str
    nullable: bool = True
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DataSchema(BaseModel):
    """Schema representation for a data source."""
    name: str
    fields: List[SchemaField]
    primary_key: Optional[List[str]] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SampleData(BaseModel):
    """Sample data from a data source."""
    schema_: DataSchema = Field(..., alias="schema")
    rows: List[Dict[str, Any]]
    total_count: Optional[int] = None
    sample_size: int

    model_config = {"populate_by_name": True}


class ConnectionTestResult(BaseModel):
    """Result of a connection test."""
    success: bool
    message: str
    latency_ms: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)


T = TypeVar("T", bound="BaseConnector")


class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors.

    All connectors must implement async connect/disconnect and
    provide methods for testing connections and fetching schemas.
    """

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._status = ConnectionStatus.DISCONNECTED
        self._connection: Any = None

    @property
    def name(self) -> str:
        """Return the connector instance name."""
        return self.config.name

    @property
    def connector_type(self) -> str:
        """Return the connector type identifier."""
        return self.config.connector_type

    @property
    def status(self) -> ConnectionStatus:
        """Return the current connection status."""
        return self._status

    @property
    def is_connected(self) -> bool:
        """Check if the connector is currently connected."""
        return self._status == ConnectionStatus.CONNECTED

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the data source.
        Should set _status to CONNECTED on success.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close connection to the data source.
        Should set _status to DISCONNECTED.
        """
        pass

    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        """
        Test the connection to the data source.
        Returns a result indicating success/failure with details.
        """
        pass

    @abstractmethod
    async def fetch_schema(self, source: Optional[str] = None) -> List[DataSchema]:
        """
        Fetch schema information from the data source.

        Args:
            source: Optional source identifier (table name, endpoint, etc.)
                   If None, returns all available schemas.

        Returns:
            List of DataSchema objects describing the data structure.
        """
        pass

    @abstractmethod
    async def fetch_sample(
        self,
        source: str,
        limit: int = 100
    ) -> SampleData:
        """
        Fetch sample data from a specific source.

        Args:
            source: Source identifier (table name, endpoint, etc.)
            limit: Maximum number of rows to fetch.

        Returns:
            SampleData containing schema and sample rows.
        """
        pass

    async def __aenter__(self) -> "BaseConnector":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()


class ConnectorRegistry:
    """
    Registry for connector types.
    Allows dynamic registration and lookup of connector classes.
    """

    _connectors: Dict[str, Type[BaseConnector]] = {}

    @classmethod
    def register(cls, connector_type: str):
        """
        Decorator to register a connector class.

        Usage:
            @ConnectorRegistry.register("postgres")
            class PostgresConnector(BaseConnector):
                ...
        """
        def decorator(connector_class: Type[T]) -> Type[T]:
            cls._connectors[connector_type] = connector_class
            return connector_class
        return decorator

    @classmethod
    def get(cls, connector_type: str) -> Optional[Type[BaseConnector]]:
        """Get a connector class by type identifier."""
        return cls._connectors.get(connector_type)

    @classmethod
    def create(
        cls,
        connector_type: str,
        config: ConnectorConfig
    ) -> BaseConnector:
        """
        Create a connector instance by type.

        Args:
            connector_type: Type identifier for the connector.
            config: Configuration for the connector.

        Returns:
            Instantiated connector.

        Raises:
            ValueError: If the connector type is not registered.
        """
        connector_class = cls.get(connector_type)
        if connector_class is None:
            available = ", ".join(cls._connectors.keys())
            raise ValueError(
                f"Unknown connector type: {connector_type}. "
                f"Available types: {available}"
            )
        return connector_class(config)

    @classmethod
    def list_types(cls) -> List[str]:
        """List all registered connector types."""
        return list(cls._connectors.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered connectors (for testing)."""
        cls._connectors.clear()
