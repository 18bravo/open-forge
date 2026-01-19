"""
Ingestion pipeline jobs for Open Forge.

Orchestrates the full data ingestion process from source to staging.
"""
from dagster import (
    job,
    op,
    OpExecutionContext,
    Config,
    In,
    Out,
    DynamicOut,
    DynamicOutput,
    graph,
    schedule,
    ScheduleDefinition,
)
from typing import List, Optional
import polars as pl

from pipelines.resources import DatabaseResource, IcebergResource, EventBusResource
from pipelines.assets.ingestion import (
    raw_source_data,
    validated_source_data,
    staged_source_data,
    SourceConfig,
)


class IngestionJobConfig(Config):
    """Configuration for ingestion job."""

    source_id: str
    source_type: str
    source_name: str
    namespace: str = "raw"
    # File options
    file_path: Optional[str] = None
    file_format: Optional[str] = None
    # Database options
    query: Optional[str] = None
    connection_string: Optional[str] = None
    # API options
    api_url: Optional[str] = None
    # Processing options
    batch_size: int = 10000
    validate_schema: bool = True
    skip_staging: bool = False


class MultiSourceIngestionConfig(Config):
    """Configuration for multi-source ingestion."""

    source_ids: List[str] = []
    parallel: bool = True


@op(
    description="Load raw data from a configured source",
    out=Out(dagster_type=pl.DataFrame),
)
def load_source_data(
    context: OpExecutionContext,
    config: IngestionJobConfig,
    iceberg: IcebergResource,
    event_bus: EventBusResource,
) -> pl.DataFrame:
    """Load data from the configured source.

    Handles different source types (file, database, API) and
    applies initial data type inference.
    """
    from datetime import datetime
    import httpx

    context.log.info(f"Loading data from source: {config.source_name}")
    start_time = datetime.now()

    df: pl.DataFrame

    if config.source_type == "file":
        if not config.file_path:
            raise ValueError("file_path required for file source")

        file_format = config.file_format or _infer_format(config.file_path)
        context.log.info(f"Reading {file_format} file: {config.file_path}")

        if file_format == "csv":
            df = pl.read_csv(config.file_path, infer_schema_length=10000)
        elif file_format == "parquet":
            df = pl.read_parquet(config.file_path)
        elif file_format == "json":
            df = pl.read_json(config.file_path)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

    elif config.source_type == "database":
        if not config.query or not config.connection_string:
            raise ValueError("query and connection_string required for database source")

        context.log.info("Executing database query")
        df = pl.read_database(query=config.query, connection=config.connection_string)

    elif config.source_type == "api":
        if not config.api_url:
            raise ValueError("api_url required for API source")

        context.log.info(f"Fetching from API: {config.api_url}")
        response = httpx.get(config.api_url, timeout=60.0)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            df = pl.DataFrame(data)
        elif isinstance(data, dict):
            for key in ["data", "results", "items"]:
                if key in data and isinstance(data[key], list):
                    df = pl.DataFrame(data[key])
                    break
            else:
                df = pl.DataFrame([data])
        else:
            raise ValueError(f"Unexpected API response: {type(data)}")
    else:
        raise ValueError(f"Unknown source type: {config.source_type}")

    # Add metadata columns
    df = df.with_columns([
        pl.lit(config.source_id).alias("_source_id"),
        pl.lit(config.source_name).alias("_source_name"),
        pl.lit(datetime.now()).alias("_ingested_at"),
    ])

    load_time = (datetime.now() - start_time).total_seconds()
    context.log.info(f"Loaded {len(df)} rows in {load_time:.2f}s")

    # Publish event
    event_bus.publish_sync("data.loaded", {
        "source_id": config.source_id,
        "row_count": len(df),
        "load_time": load_time,
    })

    return df


def _infer_format(path: str) -> str:
    """Infer file format from path."""
    lower = path.lower()
    if lower.endswith(".csv"):
        return "csv"
    elif lower.endswith(".parquet"):
        return "parquet"
    elif lower.endswith(".json"):
        return "json"
    raise ValueError(f"Cannot infer format: {path}")


@op(
    description="Validate loaded data schema and quality",
    ins={"raw_df": In(dagster_type=pl.DataFrame)},
    out=Out(dagster_type=pl.DataFrame),
)
def validate_data(
    context: OpExecutionContext,
    config: IngestionJobConfig,
    raw_df: pl.DataFrame,
) -> pl.DataFrame:
    """Validate raw data before staging.

    Performs schema validation, null checks, and basic
    data quality assessments.
    """
    from datetime import datetime

    context.log.info(f"Validating {len(raw_df)} rows")

    if not config.validate_schema:
        context.log.info("Schema validation disabled, passing through")
        return raw_df

    validation_issues = []

    # Check for completely null rows
    null_rows = raw_df.filter(pl.all_horizontal(pl.all().is_null()))
    if len(null_rows) > 0:
        validation_issues.append(f"Found {len(null_rows)} completely null rows")
        raw_df = raw_df.filter(~pl.all_horizontal(pl.all().is_null()))

    # Check for high null percentage in columns
    for col in raw_df.columns:
        if col.startswith("_"):
            continue
        null_pct = raw_df[col].null_count() / len(raw_df) * 100
        if null_pct > 50:
            validation_issues.append(f"Column {col} has {null_pct:.1f}% null values")

    # Strip whitespace from strings
    string_cols = [
        c for c in raw_df.columns
        if raw_df[c].dtype in (pl.Utf8, pl.String)
    ]
    for col in string_cols:
        raw_df = raw_df.with_columns(pl.col(col).str.strip_chars())

    if validation_issues:
        context.log.warning(f"Validation issues: {validation_issues}")

    # Add validation metadata
    df = raw_df.with_columns([
        pl.lit(True).alias("_is_validated"),
        pl.lit(datetime.now()).alias("_validated_at"),
    ])

    context.log.info(f"Validation complete: {len(df)} valid rows")
    return df


@op(
    description="Stage validated data for transformation",
    ins={"validated_df": In(dagster_type=pl.DataFrame)},
    out=Out(dagster_type=pl.DataFrame),
)
def stage_data(
    context: OpExecutionContext,
    config: IngestionJobConfig,
    validated_df: pl.DataFrame,
    iceberg: IcebergResource,
    event_bus: EventBusResource,
) -> pl.DataFrame:
    """Stage validated data to Iceberg.

    Applies deduplication and writes to the staging layer.
    """
    from datetime import datetime

    context.log.info(f"Staging {len(validated_df)} rows")

    if config.skip_staging:
        context.log.info("Staging disabled, returning validated data")
        return validated_df

    # Deduplicate
    data_cols = [c for c in validated_df.columns if not c.startswith("_")]
    df = validated_df.unique(subset=data_cols, keep="last")
    dupes = len(validated_df) - len(df)

    if dupes > 0:
        context.log.info(f"Removed {dupes} duplicates")

    # Add staging metadata
    df = df.with_columns([
        pl.lit(datetime.now()).alias("_staged_at"),
        pl.concat_str([
            pl.lit(config.source_id),
            pl.lit("_"),
            pl.arange(0, len(df)).cast(pl.Utf8),
        ]).alias("_row_id"),
    ])

    # Write to Iceberg
    table_name = f"staged_{config.source_id}"
    iceberg.create_namespace(config.namespace)

    if iceberg.table_exists(config.namespace, table_name):
        iceberg.append_data(config.namespace, table_name, df)
    else:
        # Create table first
        from pipelines.io_managers import IcebergIOManager
        io_manager = IcebergIOManager()
        schema_fields = io_manager._infer_schema(df)
        iceberg.create_table(config.namespace, table_name, schema_fields)
        iceberg.append_data(config.namespace, table_name, df)

    context.log.info(f"Staged {len(df)} rows to {config.namespace}.{table_name}")

    # Publish event
    event_bus.publish_sync("data.staged", {
        "source_id": config.source_id,
        "table": f"{config.namespace}.{table_name}",
        "row_count": len(df),
    })

    return df


@op(
    description="Discover sources for batch ingestion",
    out=DynamicOut(dagster_type=str),
)
def discover_sources(
    context: OpExecutionContext,
    config: MultiSourceIngestionConfig,
    database: DatabaseResource,
) -> None:
    """Discover active data sources for batch processing.

    Queries the database for configured sources or uses
    the provided source IDs.
    """
    if config.source_ids:
        sources = config.source_ids
    else:
        # Query database for active sources
        with database.get_session() as session:
            try:
                result = session.execute(
                    "SELECT source_id FROM data_sources WHERE is_active = true"
                )
                sources = [row[0] for row in result]
            except Exception as e:
                context.log.warning(f"Could not query sources: {e}")
                sources = []

    context.log.info(f"Discovered {len(sources)} sources")

    for source_id in sources:
        yield DynamicOutput(source_id, mapping_key=source_id.replace("-", "_"))


@graph
def ingestion_pipeline():
    """Graph for single source ingestion."""
    raw = load_source_data()
    validated = validate_data(raw)
    stage_data(validated)


@job(
    description="Ingest data from a single source",
    tags={"type": "ingestion", "scope": "single"},
)
def ingestion_job():
    """Job to ingest data from a single configured source.

    Runs the full ingestion pipeline: load -> validate -> stage.
    """
    ingestion_pipeline()


@graph
def multi_source_ingestion_pipeline():
    """Graph for multi-source batch ingestion."""
    sources = discover_sources()
    # Each source runs through the pipeline
    sources.map(lambda source_id: ingestion_pipeline())


@job(
    description="Ingest data from multiple sources",
    tags={"type": "ingestion", "scope": "batch"},
)
def full_ingestion_job():
    """Job to ingest data from multiple sources.

    Discovers active sources and runs ingestion for each.
    Can process sources in parallel for efficiency.
    """
    multi_source_ingestion_pipeline()


# Schedule for hourly ingestion
hourly_ingestion_schedule = ScheduleDefinition(
    job=ingestion_job,
    cron_schedule="0 * * * *",  # Every hour
    name="hourly_ingestion",
    description="Run ingestion job every hour",
)

# Schedule for daily full ingestion
daily_full_ingestion_schedule = ScheduleDefinition(
    job=full_ingestion_job,
    cron_schedule="0 2 * * *",  # 2 AM daily
    name="daily_full_ingestion",
    description="Run full ingestion across all sources daily",
)
