"""
Session Context Management

Manages DataFusion session contexts with configuration and lifecycle management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import pyarrow as pa


@dataclass
class SessionConfig:
    """Configuration for a DataFusion session context.

    Attributes:
        max_memory_mb: Maximum memory for the session in megabytes.
        target_partitions: Target number of partitions for parallel execution.
        batch_size: Default batch size for operations.
        enable_object_store: Whether to enable object store integration.
        temp_dir: Directory for temporary files.
        runtime_config: Additional runtime configuration options.
    """

    max_memory_mb: int = 4096
    target_partitions: int = 4
    batch_size: int = 8192
    enable_object_store: bool = False
    temp_dir: str | None = None
    runtime_config: dict[str, Any] = field(default_factory=dict)


class SessionContext:
    """Manages a DataFusion session context.

    Provides lifecycle management and configuration for DataFusion sessions.
    Each session maintains its own registered tables and UDFs.

    Example:
        ```python
        config = SessionConfig(max_memory_mb=8192, target_partitions=8)
        session = SessionContext(config)
        await session.start()

        session.register_table("users", users_table)
        result = await session.execute("SELECT * FROM users WHERE active = true")

        await session.stop()
        ```
    """

    def __init__(self, config: SessionConfig | None = None):
        """Initialize session context with configuration.

        Args:
            config: Optional session configuration. Uses defaults if not provided.
        """
        self.config = config or SessionConfig()
        self._ctx: Any | None = None
        self._started: bool = False
        self._registered_tables: set[str] = set()

    @property
    def is_started(self) -> bool:
        """Check if the session is started."""
        return self._started

    async def start(self) -> None:
        """Start the session context.

        Creates and configures the DataFusion SessionContext.
        """
        if self._started:
            return

        try:
            import datafusion

            # Create session config
            runtime_config = datafusion.RuntimeConfig()

            # Apply memory limit
            runtime_config = runtime_config.with_memory_limit(
                self.config.max_memory_mb * 1024 * 1024,
                1.0,  # memory fraction
            )

            # Apply temp directory if specified
            if self.config.temp_dir:
                runtime_config = runtime_config.with_temp_file_path(
                    self.config.temp_dir
                )

            # Create session config
            session_config = datafusion.SessionConfig()
            session_config = session_config.with_target_partitions(
                self.config.target_partitions
            )
            session_config = session_config.with_batch_size(self.config.batch_size)

            # Create context
            self._ctx = datafusion.SessionContext(session_config, runtime_config)
            self._started = True

        except ImportError as e:
            raise RuntimeError(
                "DataFusion is not installed. Install with: pip install datafusion"
            ) from e

    async def stop(self) -> None:
        """Stop the session and release resources."""
        self._ctx = None
        self._started = False
        self._registered_tables.clear()

    def _ensure_started(self) -> None:
        """Ensure the session is started."""
        if not self._started or self._ctx is None:
            raise RuntimeError("Session not started. Call start() first.")

    def register_table(self, name: str, data: pa.Table) -> None:
        """Register a table in this session.

        Args:
            name: The table name.
            data: The Arrow table data.
        """
        self._ensure_started()
        self._ctx.register_record_batches(name, [data.to_batches()])
        self._registered_tables.add(name)

    def deregister_table(self, name: str) -> None:
        """Deregister a table from this session.

        Args:
            name: The table name to deregister.
        """
        self._ensure_started()
        if name in self._registered_tables:
            self._ctx.deregister_table(name)
            self._registered_tables.discard(name)

    async def execute(self, sql: str) -> pa.Table:
        """Execute a SQL query in this session.

        Args:
            sql: The SQL query to execute.

        Returns:
            Arrow table with the query results.

        Raises:
            RuntimeError: If session is not started or query fails.
        """
        self._ensure_started()

        try:
            df = self._ctx.sql(sql)
            batches = df.collect()

            if batches:
                return pa.Table.from_batches(batches)
            return pa.table({})

        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}") from e

    def get_tables(self) -> list[str]:
        """Get list of registered tables."""
        return list(self._registered_tables)

    @property
    def native_context(self) -> Any:
        """Get the underlying DataFusion context.

        Returns:
            The native datafusion.SessionContext object.

        Raises:
            RuntimeError: If session is not started.
        """
        self._ensure_started()
        return self._ctx

    async def __aenter__(self) -> "SessionContext":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop()
