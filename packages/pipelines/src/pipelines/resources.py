"""
Dagster resources for Open Forge pipelines.

Provides database, Iceberg catalog, and event bus resources
for use in Dagster assets and jobs.
"""
from typing import Optional
from contextlib import contextmanager
from dagster import ConfigurableResource, InitResourceContext
from pydantic import Field
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import get_settings
from core.storage.iceberg import IcebergCatalog
from core.messaging.events import EventBus


class DatabaseResource(ConfigurableResource):
    """PostgreSQL database resource for Dagster.

    Provides synchronous database connections via SQLAlchemy.
    Configuration is loaded from environment via core.config.
    """

    host: str = Field(default="")
    port: int = Field(default=5432)
    user: str = Field(default="")
    password: str = Field(default="")
    database: str = Field(default="")
    pool_size: int = Field(default=10)

    _engine: Optional[object] = None
    _session_factory: Optional[object] = None

    def setup_for_execution(self, context: InitResourceContext) -> None:
        """Initialize database connection on resource setup."""
        settings = get_settings()

        # Use provided config or fall back to settings
        host = self.host or settings.database.host
        port = self.port or settings.database.port
        user = self.user or settings.database.user
        password = self.password or settings.database.password
        database = self.database or settings.database.database
        pool_size = self.pool_size or settings.database.pool_size

        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        self._engine = create_engine(
            connection_string,
            pool_size=pool_size,
            pool_pre_ping=True,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False
        )

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        """Clean up database connections."""
        if self._engine:
            self._engine.dispose()

    @contextmanager
    def get_session(self):
        """Get a database session as a context manager."""
        if self._session_factory is None:
            # Lazy initialization if not set up through Dagster
            self.setup_for_execution(None)

        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def execute_query(self, query: str, params: Optional[dict] = None) -> list:
        """Execute a raw SQL query and return results."""
        with self.get_session() as session:
            result = session.execute(query, params or {})
            return result.fetchall()


class IcebergResource(ConfigurableResource):
    """Apache Iceberg catalog resource for Dagster.

    Wraps the core IcebergCatalog class for use in Dagster pipelines.
    Provides table operations for the data lake.
    """

    catalog_uri: str = Field(default="")
    warehouse_path: str = Field(default="")
    s3_endpoint: str = Field(default="")
    s3_access_key: str = Field(default="")
    s3_secret_key: str = Field(default="")

    _catalog: Optional[IcebergCatalog] = None

    def setup_for_execution(self, context: InitResourceContext) -> None:
        """Initialize Iceberg catalog on resource setup."""
        # IcebergCatalog uses settings internally, so we just instantiate it
        self._catalog = IcebergCatalog()

    @property
    def catalog(self) -> IcebergCatalog:
        """Get the Iceberg catalog instance."""
        if self._catalog is None:
            self._catalog = IcebergCatalog()
        return self._catalog

    def create_namespace(self, namespace: str) -> None:
        """Create a namespace in the Iceberg catalog."""
        self.catalog.create_namespace(namespace)

    def create_table(
        self,
        namespace: str,
        table_name: str,
        schema_fields: list,
        partition_by: Optional[list] = None
    ) -> None:
        """Create an Iceberg table."""
        self.catalog.create_table(namespace, table_name, schema_fields, partition_by)

    def table_exists(self, namespace: str, table_name: str) -> bool:
        """Check if a table exists."""
        return self.catalog.table_exists(namespace, table_name)

    def append_data(self, namespace: str, table_name: str, df) -> None:
        """Append data to an Iceberg table."""
        self.catalog.append_data(namespace, table_name, df)

    def overwrite_data(self, namespace: str, table_name: str, df) -> None:
        """Overwrite data in an Iceberg table."""
        self.catalog.overwrite_data(namespace, table_name, df)

    def read_table(
        self,
        namespace: str,
        table_name: str,
        columns: Optional[list] = None,
        filter_expr: Optional[str] = None
    ):
        """Read data from an Iceberg table."""
        return self.catalog.read_table(namespace, table_name, columns, filter_expr)

    def get_table_schema(self, namespace: str, table_name: str) -> dict:
        """Get schema information for a table."""
        return self.catalog.get_table_schema(namespace, table_name)

    def list_tables(self, namespace: str) -> list:
        """List all tables in a namespace."""
        return self.catalog.list_tables(namespace)


class EventBusResource(ConfigurableResource):
    """Redis event bus resource for Dagster.

    Provides event publishing capabilities for pipeline events.
    Uses Redis Streams for durable message delivery.
    """

    host: str = Field(default="")
    port: int = Field(default=6379)
    password: Optional[str] = Field(default=None)

    _event_bus: Optional[EventBus] = None
    _connected: bool = False

    def setup_for_execution(self, context: InitResourceContext) -> None:
        """Initialize event bus - note: actual connection is async."""
        self._event_bus = EventBus()

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus instance."""
        if self._event_bus is None:
            self._event_bus = EventBus()
        return self._event_bus

    async def connect(self) -> None:
        """Connect to Redis asynchronously."""
        await self.event_bus.connect()
        self._connected = True

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._connected:
            await self.event_bus.disconnect()
            self._connected = False

    async def publish(self, event_type: str, payload: dict) -> str:
        """Publish an event to the event bus.

        Args:
            event_type: Type of event (e.g., "pipeline.started", "data.ingested")
            payload: Event data as a dictionary

        Returns:
            Message ID from Redis
        """
        if not self._connected:
            await self.connect()
        return await self.event_bus.publish(event_type, payload)

    def publish_sync(self, event_type: str, payload: dict) -> None:
        """Synchronous event publishing for non-async contexts.

        Note: This creates a new event loop for the publish operation.
        Prefer async publish when possible.
        """
        import asyncio

        async def _publish():
            await self.connect()
            try:
                await self.event_bus.publish(event_type, payload)
            finally:
                await self.disconnect()

        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            asyncio.create_task(_publish())
        except RuntimeError:
            # No running loop, run synchronously
            asyncio.run(_publish())
