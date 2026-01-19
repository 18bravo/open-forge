"""
CSV file connector for Open Forge.
Provides async CSV file reading and schema inference.
"""
import csv
import time
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
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


class CSVConfig(ConnectorConfig):
    """Configuration for CSV file connector."""
    connector_type: str = Field(default="csv", frozen=True)
    file_path: str = Field(..., description="Path to the CSV file or directory")
    delimiter: str = Field(default=",", description="Field delimiter")
    quote_char: str = Field(default='"', description="Quote character")
    encoding: str = Field(default="utf-8", description="File encoding")
    has_header: bool = Field(default=True, description="Whether the file has a header row")
    skip_rows: int = Field(default=0, description="Number of rows to skip at the beginning")
    null_values: List[str] = Field(
        default_factory=lambda: ["", "NULL", "null", "None", "NA", "N/A"],
        description="Values to treat as null"
    )
    # Type inference settings
    infer_types: bool = Field(default=True, description="Attempt to infer column types")
    sample_rows_for_inference: int = Field(
        default=1000,
        description="Number of rows to sample for type inference"
    )


@ConnectorRegistry.register("csv")
class CSVConnector(BaseConnector):
    """
    CSV file connector.

    Provides async file reading with schema inference and
    type detection support.

    Example:
        config = CSVConfig(
            name="my-csv",
            file_path="/data/users.csv"
        )
        async with CSVConnector(config) as conn:
            schema = await conn.fetch_schema()
            sample = await conn.fetch_sample("users.csv", limit=100)
    """

    def __init__(self, config: CSVConfig):
        super().__init__(config)
        self.config: CSVConfig = config
        self._path: Optional[Path] = None
        self._files: List[Path] = []

    @property
    def path(self) -> Path:
        """Get the configured path."""
        if self._path is None:
            raise RuntimeError("Connector not connected. Call connect() first.")
        return self._path

    async def connect(self) -> None:
        """Verify the CSV file or directory exists."""
        self._status = ConnectionStatus.CONNECTING
        try:
            self._path = Path(self.config.file_path)

            if self._path.is_file():
                if not self._path.suffix.lower() == ".csv":
                    raise ValueError(f"File is not a CSV: {self._path}")
                self._files = [self._path]
            elif self._path.is_dir():
                self._files = list(self._path.glob("*.csv"))
                if not self._files:
                    raise ValueError(f"No CSV files found in directory: {self._path}")
            else:
                raise FileNotFoundError(f"Path does not exist: {self._path}")

            self._status = ConnectionStatus.CONNECTED
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            raise RuntimeError(f"Failed to connect to CSV: {e}") from e

    async def disconnect(self) -> None:
        """Clean up resources."""
        self._path = None
        self._files = []
        self._status = ConnectionStatus.DISCONNECTED

    async def test_connection(self) -> ConnectionTestResult:
        """Test that the CSV file is accessible and readable."""
        start_time = time.time()
        try:
            path = Path(self.config.file_path)

            if not path.exists():
                return ConnectionTestResult(
                    success=False,
                    message=f"Path does not exist: {path}",
                    latency_ms=(time.time() - start_time) * 1000,
                )

            if path.is_file():
                # Try to read the first line
                async with aiofiles.open(
                    path, mode="r", encoding=self.config.encoding
                ) as f:
                    await f.readline()

                latency_ms = (time.time() - start_time) * 1000
                return ConnectionTestResult(
                    success=True,
                    message="File is readable",
                    latency_ms=latency_ms,
                    details={"file_path": str(path), "size_bytes": path.stat().st_size}
                )
            elif path.is_dir():
                csv_files = list(path.glob("*.csv"))
                latency_ms = (time.time() - start_time) * 1000
                return ConnectionTestResult(
                    success=len(csv_files) > 0,
                    message=f"Found {len(csv_files)} CSV files",
                    latency_ms=latency_ms,
                    details={"directory": str(path), "file_count": len(csv_files)}
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

    async def _read_csv_content(
        self,
        file_path: Path,
        limit: Optional[int] = None
    ) -> tuple[List[str], List[List[str]]]:
        """Read CSV content and return headers and rows."""
        async with aiofiles.open(
            file_path, mode="r", encoding=self.config.encoding
        ) as f:
            content = await f.read()

        reader = csv.reader(
            StringIO(content),
            delimiter=self.config.delimiter,
            quotechar=self.config.quote_char,
        )

        rows = list(reader)

        # Skip rows if configured
        rows = rows[self.config.skip_rows:]

        if not rows:
            return [], []

        if self.config.has_header:
            headers = rows[0]
            data_rows = rows[1:]
        else:
            headers = [f"column_{i}" for i in range(len(rows[0]))]
            data_rows = rows

        if limit is not None:
            data_rows = data_rows[:limit]

        return headers, data_rows

    def _infer_column_type(self, values: List[str]) -> str:
        """Infer the type of a column from sample values."""
        non_null_values = [
            v for v in values
            if v not in self.config.null_values
        ]

        if not non_null_values:
            return "string"

        # Check for boolean
        bool_values = {"true", "false", "1", "0", "yes", "no"}
        if all(v.lower() in bool_values for v in non_null_values):
            return "boolean"

        # Check for integer
        try:
            for v in non_null_values:
                int(v)
            return "integer"
        except ValueError:
            pass

        # Check for float
        try:
            for v in non_null_values:
                float(v)
            return "float"
        except ValueError:
            pass

        # Check for date patterns
        date_patterns = [
            r"^\d{4}-\d{2}-\d{2}$",  # YYYY-MM-DD
            r"^\d{2}/\d{2}/\d{4}$",  # MM/DD/YYYY
            r"^\d{2}-\d{2}-\d{4}$",  # DD-MM-YYYY
        ]
        import re
        for pattern in date_patterns:
            if all(re.match(pattern, v) for v in non_null_values[:10]):
                return "date"

        # Check for timestamp patterns
        if any("T" in v or ":" in v for v in non_null_values[:10]):
            return "timestamp"

        return "string"

    async def fetch_schema(self, source: Optional[str] = None) -> List[DataSchema]:
        """
        Fetch schema from CSV files.

        Args:
            source: Optional filename. If None, returns schemas for all files.

        Returns:
            List of DataSchema objects.
        """
        schemas = []

        if source:
            # Find the specific file
            target_files = [f for f in self._files if f.name == source]
            if not target_files:
                raise ValueError(f"File not found: {source}")
        else:
            target_files = self._files

        for file_path in target_files:
            headers, data_rows = await self._read_csv_content(
                file_path,
                limit=self.config.sample_rows_for_inference if self.config.infer_types else 1
            )

            fields = []
            for i, header in enumerate(headers):
                if self.config.infer_types and data_rows:
                    column_values = [row[i] if i < len(row) else "" for row in data_rows]
                    data_type = self._infer_column_type(column_values)
                else:
                    data_type = "string"

                fields.append(SchemaField(
                    name=header,
                    data_type=data_type,
                    nullable=True,
                    metadata={"position": i}
                ))

            schemas.append(DataSchema(
                name=file_path.stem,
                fields=fields,
                metadata={
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "delimiter": self.config.delimiter,
                    "has_header": self.config.has_header,
                }
            ))

        return schemas

    async def fetch_sample(
        self,
        source: str,
        limit: int = 100
    ) -> SampleData:
        """
        Fetch sample data from a CSV file.

        Args:
            source: CSV filename.
            limit: Maximum number of rows.

        Returns:
            SampleData with schema and rows.
        """
        # Find the file
        target_files = [f for f in self._files if f.name == source or f.stem == source]
        if not target_files:
            raise ValueError(f"File not found: {source}")

        file_path = target_files[0]
        headers, data_rows = await self._read_csv_content(file_path, limit=None)

        # Get schema
        schemas = await self.fetch_schema(file_path.name)
        schema = schemas[0] if schemas else DataSchema(name=source, fields=[])

        # Convert rows to dictionaries
        rows = []
        for row_data in data_rows[:limit]:
            row_dict = {}
            for i, header in enumerate(headers):
                value = row_data[i] if i < len(row_data) else None
                # Convert null values
                if value in self.config.null_values:
                    value = None
                row_dict[header] = value
            rows.append(row_dict)

        return SampleData(
            schema=schema,
            rows=rows,
            total_count=len(data_rows),
            sample_size=len(rows)
        )

    async def list_files(self) -> List[Dict[str, Any]]:
        """List all CSV files in the configured path."""
        files = []
        for file_path in self._files:
            stat = file_path.stat()
            files.append({
                "name": file_path.name,
                "path": str(file_path),
                "size_bytes": stat.st_size,
                "modified_time": stat.st_mtime,
            })
        return files

    async def read_all(
        self,
        source: str,
        batch_size: int = 1000
    ):
        """
        Async generator to read all rows from a CSV file in batches.

        Args:
            source: CSV filename.
            batch_size: Number of rows per batch.

        Yields:
            List of row dictionaries for each batch.
        """
        target_files = [f for f in self._files if f.name == source or f.stem == source]
        if not target_files:
            raise ValueError(f"File not found: {source}")

        file_path = target_files[0]
        headers, data_rows = await self._read_csv_content(file_path)

        for i in range(0, len(data_rows), batch_size):
            batch = data_rows[i:i + batch_size]
            rows = []
            for row_data in batch:
                row_dict = {}
                for j, header in enumerate(headers):
                    value = row_data[j] if j < len(row_data) else None
                    if value in self.config.null_values:
                        value = None
                    row_dict[header] = value
                rows.append(row_dict)
            yield rows
