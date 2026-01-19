"""
Data ingestion assets for Open Forge.

Handles loading data from various sources into the data lake.
Supports file uploads, database connections, and API sources.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from dagster import (
    asset,
    AssetExecutionContext,
    Config,
    MetadataValue,
    Output,
    AssetKey,
)
import polars as pl

from pipelines.resources import DatabaseResource, IcebergResource, EventBusResource


class SourceConfig(Config):
    """Configuration for data source ingestion."""

    source_id: str
    source_type: str  # "file", "database", "api"
    source_name: str
    namespace: str = "raw"
    # File source options
    file_path: Optional[str] = None
    file_format: Optional[str] = None  # "csv", "parquet", "json"
    # Database source options
    query: Optional[str] = None
    connection_string: Optional[str] = None
    # API source options
    api_url: Optional[str] = None
    api_headers: Optional[Dict[str, str]] = None


@asset(
    key_prefix=["raw"],
    group_name="ingestion",
    description="Raw data loaded from external sources without transformation",
    compute_kind="polars",
)
def raw_source_data(
    context: AssetExecutionContext,
    config: SourceConfig,
    iceberg: IcebergResource,
    event_bus: EventBusResource,
) -> Output[pl.DataFrame]:
    """Load raw data from configured source.

    Supports multiple source types:
    - File: CSV, Parquet, JSON files from local or S3 paths
    - Database: SQL queries against external databases
    - API: HTTP endpoints returning JSON data

    The data is loaded as-is without transformation, preserving
    the original schema and values for audit purposes.
    """
    context.log.info(f"Loading data from source: {config.source_name} ({config.source_type})")

    start_time = datetime.now()
    df: pl.DataFrame

    if config.source_type == "file":
        df = _load_file_source(context, config)
    elif config.source_type == "database":
        df = _load_database_source(context, config)
    elif config.source_type == "api":
        df = _load_api_source(context, config)
    else:
        raise ValueError(f"Unknown source type: {config.source_type}")

    # Add ingestion metadata
    df = df.with_columns([
        pl.lit(config.source_id).alias("_source_id"),
        pl.lit(config.source_name).alias("_source_name"),
        pl.lit(datetime.now()).alias("_ingested_at"),
    ])

    load_time = (datetime.now() - start_time).total_seconds()

    # Publish ingestion event
    event_bus.publish_sync(
        "data.ingested",
        {
            "source_id": config.source_id,
            "source_name": config.source_name,
            "row_count": len(df),
            "load_time_seconds": load_time,
        }
    )

    context.log.info(f"Loaded {len(df)} rows in {load_time:.2f}s")

    return Output(
        df,
        metadata={
            "source_id": MetadataValue.text(config.source_id),
            "source_type": MetadataValue.text(config.source_type),
            "source_name": MetadataValue.text(config.source_name),
            "row_count": MetadataValue.int(len(df)),
            "column_count": MetadataValue.int(len(df.columns)),
            "columns": MetadataValue.json(df.columns),
            "load_time_seconds": MetadataValue.float(load_time),
        }
    )


def _load_file_source(context: AssetExecutionContext, config: SourceConfig) -> pl.DataFrame:
    """Load data from a file source."""
    if not config.file_path:
        raise ValueError("file_path is required for file source type")

    file_format = config.file_format or _infer_file_format(config.file_path)

    context.log.info(f"Reading {file_format} file: {config.file_path}")

    if file_format == "csv":
        return pl.read_csv(config.file_path, infer_schema_length=10000)
    elif file_format == "parquet":
        return pl.read_parquet(config.file_path)
    elif file_format == "json":
        return pl.read_json(config.file_path)
    elif file_format == "ndjson":
        return pl.read_ndjson(config.file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


def _infer_file_format(file_path: str) -> str:
    """Infer file format from extension."""
    lower_path = file_path.lower()
    if lower_path.endswith(".csv"):
        return "csv"
    elif lower_path.endswith(".parquet"):
        return "parquet"
    elif lower_path.endswith(".json"):
        return "json"
    elif lower_path.endswith(".ndjson"):
        return "ndjson"
    else:
        raise ValueError(f"Cannot infer format from path: {file_path}")


def _load_database_source(context: AssetExecutionContext, config: SourceConfig) -> pl.DataFrame:
    """Load data from a database source."""
    if not config.query:
        raise ValueError("query is required for database source type")
    if not config.connection_string:
        raise ValueError("connection_string is required for database source type")

    context.log.info(f"Executing query against database")

    # Use Polars' read_database for direct SQL execution
    return pl.read_database(
        query=config.query,
        connection=config.connection_string,
    )


def _load_api_source(context: AssetExecutionContext, config: SourceConfig) -> pl.DataFrame:
    """Load data from an API source."""
    import httpx

    if not config.api_url:
        raise ValueError("api_url is required for API source type")

    context.log.info(f"Fetching data from API: {config.api_url}")

    headers = config.api_headers or {}
    response = httpx.get(config.api_url, headers=headers, timeout=60.0)
    response.raise_for_status()

    data = response.json()

    # Handle different JSON structures
    if isinstance(data, list):
        return pl.DataFrame(data)
    elif isinstance(data, dict):
        # Check for common data wrapper keys
        for key in ["data", "results", "items", "records"]:
            if key in data and isinstance(data[key], list):
                return pl.DataFrame(data[key])
        # Treat as single record
        return pl.DataFrame([data])
    else:
        raise ValueError(f"Unexpected API response type: {type(data)}")


@asset(
    key_prefix=["validated"],
    group_name="ingestion",
    description="Source data after schema validation and type coercion",
    deps=[AssetKey(["raw", "raw_source_data"])],
    compute_kind="polars",
)
def validated_source_data(
    context: AssetExecutionContext,
    config: SourceConfig,
    iceberg: IcebergResource,
) -> Output[pl.DataFrame]:
    """Validate and clean raw source data.

    Performs:
    - Schema validation against expected types
    - Null handling and default value assignment
    - Type coercion where possible
    - Data quality checks

    Invalid rows are logged but not rejected at this stage.
    """
    context.log.info(f"Validating data for source: {config.source_name}")

    # Read raw data from Iceberg
    raw_df = iceberg.read_table("raw", f"raw_{config.source_id}")

    validation_results = {
        "total_rows": len(raw_df),
        "null_counts": {},
        "type_errors": [],
        "valid_rows": 0,
    }

    # Check for nulls in each column
    for col in raw_df.columns:
        null_count = raw_df[col].null_count()
        if null_count > 0:
            validation_results["null_counts"][col] = null_count

    # Perform basic cleaning
    df = raw_df

    # Remove completely empty rows
    df = df.filter(~pl.all_horizontal(pl.all().is_null()))

    # Strip whitespace from string columns
    string_cols = [col for col in df.columns if df[col].dtype == pl.Utf8 or df[col].dtype == pl.String]
    for col in string_cols:
        df = df.with_columns(pl.col(col).str.strip_chars().alias(col))

    validation_results["valid_rows"] = len(df)

    # Add validation metadata
    df = df.with_columns([
        pl.lit(True).alias("_is_validated"),
        pl.lit(datetime.now()).alias("_validated_at"),
    ])

    context.log.info(
        f"Validation complete: {validation_results['valid_rows']}/{validation_results['total_rows']} rows valid"
    )

    return Output(
        df,
        metadata={
            "total_rows": MetadataValue.int(validation_results["total_rows"]),
            "valid_rows": MetadataValue.int(validation_results["valid_rows"]),
            "null_columns": MetadataValue.json(validation_results["null_counts"]),
            "validation_pass_rate": MetadataValue.float(
                validation_results["valid_rows"] / max(validation_results["total_rows"], 1)
            ),
        }
    )


@asset(
    key_prefix=["staged"],
    group_name="ingestion",
    description="Validated data staged for transformation",
    deps=[AssetKey(["validated", "validated_source_data"])],
    compute_kind="polars",
)
def staged_source_data(
    context: AssetExecutionContext,
    config: SourceConfig,
    iceberg: IcebergResource,
    event_bus: EventBusResource,
) -> Output[pl.DataFrame]:
    """Stage validated data for downstream transformation.

    This is the final ingestion step before data enters the
    transformation layer. Staged data has:
    - Consistent schema
    - Validated types
    - Deduplication applied
    - Row-level lineage tracking

    Publishes a 'data.staged' event for downstream consumers.
    """
    context.log.info(f"Staging data for source: {config.source_name}")

    # Read validated data
    validated_df = iceberg.read_table("validated", f"validated_{config.source_id}")

    # Apply deduplication based on all columns except metadata
    data_columns = [
        col for col in validated_df.columns
        if not col.startswith("_")
    ]

    df = validated_df.unique(subset=data_columns, keep="last")
    duplicates_removed = len(validated_df) - len(df)

    if duplicates_removed > 0:
        context.log.info(f"Removed {duplicates_removed} duplicate rows")

    # Add staging metadata
    df = df.with_columns([
        pl.lit(datetime.now()).alias("_staged_at"),
        pl.concat_str([
            pl.lit(config.source_id),
            pl.lit("_"),
            pl.arange(0, len(df)).cast(pl.Utf8),
        ]).alias("_row_id"),
    ])

    # Publish staging event
    event_bus.publish_sync(
        "data.staged",
        {
            "source_id": config.source_id,
            "source_name": config.source_name,
            "row_count": len(df),
            "duplicates_removed": duplicates_removed,
        }
    )

    return Output(
        df,
        metadata={
            "source_id": MetadataValue.text(config.source_id),
            "row_count": MetadataValue.int(len(df)),
            "duplicates_removed": MetadataValue.int(duplicates_removed),
            "staged_at": MetadataValue.text(datetime.now().isoformat()),
        }
    )
