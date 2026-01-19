"""
Custom Dagster IO managers for Open Forge pipelines.

Provides Iceberg table I/O and Polars DataFrame handling.
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dagster import (
    ConfigurableIOManager,
    InputContext,
    OutputContext,
    MetadataValue,
)
from pydantic import Field
import polars as pl

from core.storage.iceberg import IcebergCatalog


class IcebergIOManager(ConfigurableIOManager):
    """IO Manager for reading/writing Polars DataFrames to Iceberg tables.

    Automatically handles:
    - Creating tables if they don't exist
    - Adding metadata columns (_created_at, _updated_at, _version)
    - Partitioning strategy
    - Append vs overwrite modes
    """

    namespace: str = Field(
        default="raw",
        description="Default Iceberg namespace for tables"
    )
    write_mode: str = Field(
        default="append",
        description="Write mode: 'append' or 'overwrite'"
    )
    partition_by: Optional[List[str]] = Field(
        default=None,
        description="Columns to partition by"
    )

    _catalog: Optional[IcebergCatalog] = None

    @property
    def catalog(self) -> IcebergCatalog:
        """Lazy-load the Iceberg catalog."""
        if self._catalog is None:
            self._catalog = IcebergCatalog()
        return self._catalog

    def _get_table_name(self, context: Union[InputContext, OutputContext]) -> str:
        """Derive table name from asset key."""
        # Use the last part of the asset key as table name
        if context.has_asset_key:
            return "_".join(context.asset_key.path)
        return context.name

    def _get_namespace(self, context: Union[InputContext, OutputContext]) -> str:
        """Get namespace from context metadata or use default."""
        if context.has_asset_key and len(context.asset_key.path) > 1:
            # Use first part of asset key as namespace
            return context.asset_key.path[0]
        return self.namespace

    def _infer_schema(self, df: pl.DataFrame) -> List[Dict[str, Any]]:
        """Infer Iceberg schema from Polars DataFrame."""
        type_mapping = {
            pl.Utf8: "string",
            pl.String: "string",
            pl.Int8: "integer",
            pl.Int16: "integer",
            pl.Int32: "integer",
            pl.Int64: "long",
            pl.UInt8: "integer",
            pl.UInt16: "integer",
            pl.UInt32: "integer",
            pl.UInt64: "long",
            pl.Float32: "float",
            pl.Float64: "double",
            pl.Boolean: "boolean",
            pl.Date: "timestamp",
            pl.Datetime: "timestamp",
            pl.Time: "timestamp",
            pl.Decimal: "decimal",
        }

        schema_fields = []
        for col_name in df.columns:
            col_type = df[col_name].dtype
            # Get base type for parameterized types
            base_type = type(col_type) if hasattr(col_type, '__class__') else col_type
            iceberg_type = type_mapping.get(base_type, "string")

            schema_fields.append({
                "name": col_name,
                "type": iceberg_type,
                "required": False
            })

        return schema_fields

    def _add_metadata_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        """Add metadata columns to DataFrame if not present."""
        now = datetime.now()

        if "_created_at" not in df.columns:
            df = df.with_columns(pl.lit(now).alias("_created_at"))
        if "_updated_at" not in df.columns:
            df = df.with_columns(pl.lit(now).alias("_updated_at"))
        if "_version" not in df.columns:
            df = df.with_columns(pl.lit(1).alias("_version"))

        return df

    def handle_output(self, context: OutputContext, obj: pl.DataFrame) -> None:
        """Write a Polars DataFrame to an Iceberg table."""
        if obj is None or (isinstance(obj, pl.DataFrame) and obj.is_empty()):
            context.log.info("No data to write, skipping")
            return

        namespace = self._get_namespace(context)
        table_name = self._get_table_name(context)

        # Add metadata columns
        df = self._add_metadata_columns(obj)

        # Ensure namespace exists
        self.catalog.create_namespace(namespace)

        # Create table if it doesn't exist
        if not self.catalog.table_exists(namespace, table_name):
            context.log.info(f"Creating table {namespace}.{table_name}")
            schema_fields = self._infer_schema(df)
            self.catalog.create_table(
                namespace,
                table_name,
                schema_fields,
                self.partition_by
            )

        # Write data
        if self.write_mode == "overwrite":
            self.catalog.overwrite_data(namespace, table_name, df)
            context.log.info(f"Overwrote data in {namespace}.{table_name}")
        else:
            self.catalog.append_data(namespace, table_name, df)
            context.log.info(f"Appended {len(df)} rows to {namespace}.{table_name}")

        # Add output metadata
        context.add_output_metadata({
            "namespace": MetadataValue.text(namespace),
            "table_name": MetadataValue.text(table_name),
            "row_count": MetadataValue.int(len(df)),
            "columns": MetadataValue.json(df.columns),
            "write_mode": MetadataValue.text(self.write_mode),
        })

    def load_input(self, context: InputContext) -> pl.DataFrame:
        """Load a Polars DataFrame from an Iceberg table."""
        namespace = self._get_namespace(context)
        table_name = self._get_table_name(context)

        if not self.catalog.table_exists(namespace, table_name):
            context.log.warning(f"Table {namespace}.{table_name} does not exist")
            return pl.DataFrame()

        # Get columns to load from context if specified
        columns = None
        if context.has_asset_key and context.metadata:
            columns = context.metadata.get("columns")

        df = self.catalog.read_table(namespace, table_name, columns)
        context.log.info(f"Loaded {len(df)} rows from {namespace}.{table_name}")

        return df


class PolarsIOManager(ConfigurableIOManager):
    """IO Manager for handling Polars DataFrames in memory.

    Used for intermediate transformations where persistence to Iceberg
    is not needed. Supports parquet file caching for large DataFrames.
    """

    cache_dir: str = Field(
        default="/tmp/dagster_polars_cache",
        description="Directory for caching large DataFrames"
    )
    cache_threshold_mb: int = Field(
        default=100,
        description="DataFrame size threshold (MB) for disk caching"
    )

    _cache: Dict[str, pl.DataFrame] = {}

    def _get_cache_key(self, context: Union[InputContext, OutputContext]) -> str:
        """Generate a cache key from context."""
        if context.has_asset_key:
            return "_".join(context.asset_key.path)
        return f"{context.step_key}_{context.name}"

    def _estimate_size_mb(self, df: pl.DataFrame) -> float:
        """Estimate DataFrame size in MB."""
        return df.estimated_size() / (1024 * 1024)

    def handle_output(self, context: OutputContext, obj: pl.DataFrame) -> None:
        """Store a Polars DataFrame."""
        if obj is None:
            return

        cache_key = self._get_cache_key(context)
        size_mb = self._estimate_size_mb(obj)

        if size_mb > self.cache_threshold_mb:
            # Cache to disk as parquet
            import os
            os.makedirs(self.cache_dir, exist_ok=True)
            cache_path = f"{self.cache_dir}/{cache_key}.parquet"
            obj.write_parquet(cache_path, compression="zstd")
            self._cache[cache_key] = cache_path  # Store path instead of df
            context.log.info(f"Cached {size_mb:.2f}MB DataFrame to {cache_path}")
        else:
            # Keep in memory
            self._cache[cache_key] = obj
            context.log.info(f"Stored {size_mb:.2f}MB DataFrame in memory")

        context.add_output_metadata({
            "row_count": MetadataValue.int(len(obj)),
            "column_count": MetadataValue.int(len(obj.columns)),
            "size_mb": MetadataValue.float(size_mb),
            "cached_to_disk": MetadataValue.bool(size_mb > self.cache_threshold_mb),
        })

    def load_input(self, context: InputContext) -> pl.DataFrame:
        """Load a Polars DataFrame from cache."""
        cache_key = self._get_cache_key(context)

        if cache_key not in self._cache:
            context.log.warning(f"No cached DataFrame found for {cache_key}")
            return pl.DataFrame()

        cached = self._cache[cache_key]

        if isinstance(cached, str):
            # Load from disk cache
            df = pl.read_parquet(cached)
            context.log.info(f"Loaded DataFrame from {cached}")
            return df
        else:
            # Return from memory
            context.log.info(f"Retrieved DataFrame from memory cache")
            return cached


class PartitionedIcebergIOManager(IcebergIOManager):
    """IO Manager for partitioned Iceberg tables.

    Extends IcebergIOManager with partition-aware read/write operations.
    Supports time-based partitioning for incremental processing.
    """

    partition_column: str = Field(
        default="_created_at",
        description="Column to use for partitioning"
    )
    time_partition_format: str = Field(
        default="day",
        description="Time partition granularity: 'day', 'hour', 'month'"
    )

    def handle_output(self, context: OutputContext, obj: pl.DataFrame) -> None:
        """Write partitioned data to Iceberg."""
        if obj is None or (isinstance(obj, pl.DataFrame) and obj.is_empty()):
            context.log.info("No data to write, skipping")
            return

        # Ensure partition column exists
        if self.partition_column not in obj.columns:
            obj = self._add_metadata_columns(obj)

        # Set partition_by based on configuration
        self.partition_by = [self.partition_column]

        # Call parent implementation
        super().handle_output(context, obj)

        # Add partition metadata
        if self.partition_column in obj.columns:
            try:
                partition_values = obj[self.partition_column].unique().to_list()
                context.add_output_metadata({
                    "partition_column": MetadataValue.text(self.partition_column),
                    "partition_count": MetadataValue.int(len(partition_values)),
                })
            except Exception:
                pass  # Skip if we can't get partition info
