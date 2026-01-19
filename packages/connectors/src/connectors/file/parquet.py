"""
Parquet file connector for Open Forge.
Provides async Parquet file reading with schema extraction.
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field

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


class ParquetConfig(ConnectorConfig):
    """Configuration for Parquet file connector."""
    connector_type: str = Field(default="parquet", frozen=True)
    file_path: str = Field(..., description="Path to the Parquet file or directory")
    # Reading options
    columns: Optional[List[str]] = Field(
        default=None,
        description="Specific columns to read (None for all)"
    )
    row_groups: Optional[List[int]] = Field(
        default=None,
        description="Specific row groups to read (None for all)"
    )
    # Thread pool settings
    max_workers: int = Field(default=4, description="Max worker threads for I/O")


@ConnectorRegistry.register("parquet")
class ParquetConnector(BaseConnector):
    """
    Parquet file connector.

    Provides async file reading with native schema extraction
    from Parquet metadata.

    Requires pyarrow to be installed.

    Example:
        config = ParquetConfig(
            name="my-parquet",
            file_path="/data/users.parquet"
        )
        async with ParquetConnector(config) as conn:
            schema = await conn.fetch_schema()
            sample = await conn.fetch_sample("users.parquet", limit=100)
    """

    def __init__(self, config: ParquetConfig):
        super().__init__(config)
        self.config: ParquetConfig = config
        self._path: Optional[Path] = None
        self._files: List[Path] = []
        self._executor: Optional[ThreadPoolExecutor] = None

    @property
    def path(self) -> Path:
        """Get the configured path."""
        if self._path is None:
            raise RuntimeError("Connector not connected. Call connect() first.")
        return self._path

    def _import_pyarrow(self):
        """Import pyarrow with helpful error message."""
        try:
            import pyarrow.parquet as pq
            return pq
        except ImportError:
            raise ImportError(
                "pyarrow is required for Parquet support. "
                "Install it with: pip install pyarrow"
            )

    async def connect(self) -> None:
        """Verify the Parquet file or directory exists."""
        self._status = ConnectionStatus.CONNECTING
        try:
            # Verify pyarrow is available
            self._import_pyarrow()

            self._path = Path(self.config.file_path)
            self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)

            if self._path.is_file():
                if not self._path.suffix.lower() == ".parquet":
                    raise ValueError(f"File is not a Parquet file: {self._path}")
                self._files = [self._path]
            elif self._path.is_dir():
                self._files = list(self._path.glob("*.parquet"))
                # Also check for partitioned dataset
                self._files.extend(self._path.glob("**/*.parquet"))
                self._files = list(set(self._files))  # Remove duplicates
                if not self._files:
                    raise ValueError(f"No Parquet files found in directory: {self._path}")
            else:
                raise FileNotFoundError(f"Path does not exist: {self._path}")

            self._status = ConnectionStatus.CONNECTED
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            raise RuntimeError(f"Failed to connect to Parquet: {e}") from e

    async def disconnect(self) -> None:
        """Clean up resources."""
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
        self._path = None
        self._files = []
        self._status = ConnectionStatus.DISCONNECTED

    async def test_connection(self) -> ConnectionTestResult:
        """Test that the Parquet file is accessible and valid."""
        start_time = time.time()
        try:
            pq = self._import_pyarrow()
            path = Path(self.config.file_path)

            if not path.exists():
                return ConnectionTestResult(
                    success=False,
                    message=f"Path does not exist: {path}",
                    latency_ms=(time.time() - start_time) * 1000,
                )

            if path.is_file():
                # Try to read metadata
                loop = asyncio.get_event_loop()
                metadata = await loop.run_in_executor(
                    self._executor,
                    lambda: pq.read_metadata(path)
                )

                latency_ms = (time.time() - start_time) * 1000
                return ConnectionTestResult(
                    success=True,
                    message="Parquet file is valid",
                    latency_ms=latency_ms,
                    details={
                        "file_path": str(path),
                        "num_rows": metadata.num_rows,
                        "num_columns": metadata.num_columns,
                        "num_row_groups": metadata.num_row_groups,
                    }
                )
            elif path.is_dir():
                parquet_files = list(path.glob("*.parquet"))
                parquet_files.extend(path.glob("**/*.parquet"))
                parquet_files = list(set(parquet_files))

                latency_ms = (time.time() - start_time) * 1000
                return ConnectionTestResult(
                    success=len(parquet_files) > 0,
                    message=f"Found {len(parquet_files)} Parquet files",
                    latency_ms=latency_ms,
                    details={"directory": str(path), "file_count": len(parquet_files)}
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message="Path is neither a file nor directory",
                    latency_ms=(time.time() - start_time) * 1000,
                )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Error: {str(e)}",
                latency_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )

    def _arrow_type_to_string(self, arrow_type) -> str:
        """Convert Arrow type to a string representation."""
        import pyarrow as pa

        type_mapping = {
            pa.int8(): "byte",
            pa.int16(): "short",
            pa.int32(): "int",
            pa.int64(): "long",
            pa.uint8(): "ubyte",
            pa.uint16(): "ushort",
            pa.uint32(): "uint",
            pa.uint64(): "ulong",
            pa.float16(): "float16",
            pa.float32(): "float",
            pa.float64(): "double",
            pa.bool_(): "boolean",
            pa.string(): "string",
            pa.large_string(): "string",
            pa.binary(): "binary",
            pa.large_binary(): "binary",
            pa.date32(): "date",
            pa.date64(): "date",
        }

        # Check exact type match
        if arrow_type in type_mapping:
            return type_mapping[arrow_type]

        # Check type categories
        if pa.types.is_timestamp(arrow_type):
            return "timestamp"
        if pa.types.is_time(arrow_type):
            return "time"
        if pa.types.is_duration(arrow_type):
            return "duration"
        if pa.types.is_decimal(arrow_type):
            return "decimal"
        if pa.types.is_list(arrow_type):
            return "array"
        if pa.types.is_struct(arrow_type):
            return "struct"
        if pa.types.is_map(arrow_type):
            return "map"
        if pa.types.is_dictionary(arrow_type):
            return "dictionary"

        return str(arrow_type)

    async def fetch_schema(self, source: Optional[str] = None) -> List[DataSchema]:
        """
        Fetch schema from Parquet files.

        Args:
            source: Optional filename. If None, returns schemas for all files.

        Returns:
            List of DataSchema objects.
        """
        pq = self._import_pyarrow()
        schemas = []
        loop = asyncio.get_event_loop()

        if source:
            target_files = [f for f in self._files if f.name == source]
            if not target_files:
                raise ValueError(f"File not found: {source}")
        else:
            target_files = self._files

        for file_path in target_files:
            # Read schema from file
            parquet_schema = await loop.run_in_executor(
                self._executor,
                lambda fp=file_path: pq.read_schema(fp)
            )

            fields = []
            for i, field in enumerate(parquet_schema):
                fields.append(SchemaField(
                    name=field.name,
                    data_type=self._arrow_type_to_string(field.type),
                    nullable=field.nullable,
                    metadata={
                        "arrow_type": str(field.type),
                        "position": i,
                    }
                ))

            # Get file metadata
            metadata = await loop.run_in_executor(
                self._executor,
                lambda fp=file_path: pq.read_metadata(fp)
            )

            schemas.append(DataSchema(
                name=file_path.stem,
                fields=fields,
                metadata={
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "num_rows": metadata.num_rows,
                    "num_row_groups": metadata.num_row_groups,
                    "created_by": metadata.created_by,
                    "format_version": str(metadata.format_version),
                }
            ))

        return schemas

    async def fetch_sample(
        self,
        source: str,
        limit: int = 100
    ) -> SampleData:
        """
        Fetch sample data from a Parquet file.

        Args:
            source: Parquet filename.
            limit: Maximum number of rows.

        Returns:
            SampleData with schema and rows.
        """
        pq = self._import_pyarrow()
        loop = asyncio.get_event_loop()

        # Find the file
        target_files = [f for f in self._files if f.name == source or f.stem == source]
        if not target_files:
            raise ValueError(f"File not found: {source}")

        file_path = target_files[0]

        # Get schema
        schemas = await self.fetch_schema(file_path.name)
        schema = schemas[0] if schemas else DataSchema(name=source, fields=[])

        # Read sample data
        def read_sample():
            table = pq.read_table(
                file_path,
                columns=self.config.columns,
            )
            # Convert to pandas for easier row iteration
            df = table.slice(0, limit).to_pandas()
            return df.to_dict(orient="records"), len(table)

        rows, total_count = await loop.run_in_executor(self._executor, read_sample)

        return SampleData(
            schema=schema,
            rows=rows,
            total_count=total_count,
            sample_size=len(rows)
        )

    async def list_files(self) -> List[Dict[str, Any]]:
        """List all Parquet files in the configured path."""
        pq = self._import_pyarrow()
        loop = asyncio.get_event_loop()
        files = []

        for file_path in self._files:
            stat = file_path.stat()

            # Get Parquet metadata
            try:
                metadata = await loop.run_in_executor(
                    self._executor,
                    lambda fp=file_path: pq.read_metadata(fp)
                )
                num_rows = metadata.num_rows
                num_columns = metadata.num_columns
            except Exception:
                num_rows = None
                num_columns = None

            files.append({
                "name": file_path.name,
                "path": str(file_path),
                "size_bytes": stat.st_size,
                "modified_time": stat.st_mtime,
                "num_rows": num_rows,
                "num_columns": num_columns,
            })

        return files

    async def read_table(
        self,
        source: str,
        columns: Optional[List[str]] = None,
        row_groups: Optional[List[int]] = None
    ):
        """
        Read a Parquet file as a PyArrow Table.

        Args:
            source: Parquet filename.
            columns: Specific columns to read.
            row_groups: Specific row groups to read.

        Returns:
            PyArrow Table.
        """
        pq = self._import_pyarrow()
        loop = asyncio.get_event_loop()

        target_files = [f for f in self._files if f.name == source or f.stem == source]
        if not target_files:
            raise ValueError(f"File not found: {source}")

        file_path = target_files[0]

        def read():
            if row_groups is not None:
                parquet_file = pq.ParquetFile(file_path)
                return parquet_file.read_row_groups(row_groups, columns=columns)
            return pq.read_table(file_path, columns=columns)

        return await loop.run_in_executor(self._executor, read)

    async def read_batches(
        self,
        source: str,
        batch_size: int = 10000,
        columns: Optional[List[str]] = None
    ):
        """
        Async generator to read Parquet file in batches.

        Args:
            source: Parquet filename.
            batch_size: Number of rows per batch.
            columns: Specific columns to read.

        Yields:
            List of row dictionaries for each batch.
        """
        pq = self._import_pyarrow()
        loop = asyncio.get_event_loop()

        target_files = [f for f in self._files if f.name == source or f.stem == source]
        if not target_files:
            raise ValueError(f"File not found: {source}")

        file_path = target_files[0]

        def get_batches():
            parquet_file = pq.ParquetFile(file_path)
            batches = []
            for batch in parquet_file.iter_batches(batch_size=batch_size, columns=columns):
                batches.append(batch.to_pydict())
            return batches

        batches = await loop.run_in_executor(self._executor, get_batches)

        for batch_dict in batches:
            # Convert columnar to row-oriented
            if batch_dict:
                keys = list(batch_dict.keys())
                num_rows = len(batch_dict[keys[0]])
                rows = [
                    {k: batch_dict[k][i] for k in keys}
                    for i in range(num_rows)
                ]
                yield rows
