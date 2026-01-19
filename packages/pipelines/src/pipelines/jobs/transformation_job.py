"""
Transformation pipeline jobs for Open Forge.

Orchestrates data cleaning, enrichment, and aggregation operations.
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
from typing import Any, Dict, List, Optional
import polars as pl

from pipelines.resources import DatabaseResource, IcebergResource, EventBusResource


class TransformationJobConfig(Config):
    """Configuration for transformation job."""

    dataset_id: str
    dataset_name: str
    source_namespace: str = "staged"
    source_tables: List[str] = []
    target_namespace: str = "curated"
    # Cleaning options
    drop_columns: Optional[List[str]] = None
    rename_columns: Optional[Dict[str, str]] = None
    dedupe_columns: Optional[List[str]] = None
    # Enrichment options
    lookup_table: Optional[str] = None
    lookup_key: Optional[str] = None
    # Aggregation options
    group_by_columns: Optional[List[str]] = None
    aggregations: Optional[Dict[str, str]] = None
    time_column: Optional[str] = None
    time_granularity: Optional[str] = None


class MultiDatasetConfig(Config):
    """Configuration for multi-dataset transformation."""

    dataset_ids: List[str] = []
    parallel: bool = True


@op(
    description="Load staged data for transformation",
    out=Out(dagster_type=pl.DataFrame),
)
def load_staged_data(
    context: OpExecutionContext,
    config: TransformationJobConfig,
    iceberg: IcebergResource,
) -> pl.DataFrame:
    """Load data from staging tables.

    Combines multiple source tables if configured.
    """
    context.log.info(f"Loading staged data for: {config.dataset_name}")

    dfs = []
    for table in config.source_tables:
        if iceberg.table_exists(config.source_namespace, table):
            df = iceberg.read_table(config.source_namespace, table)
            context.log.info(f"Loaded {len(df)} rows from {table}")
            dfs.append(df)
        else:
            context.log.warning(f"Table not found: {config.source_namespace}.{table}")

    if not dfs:
        context.log.warning("No data loaded")
        return pl.DataFrame()

    # Combine tables
    combined = pl.concat(dfs, how="diagonal") if len(dfs) > 1 else dfs[0]
    context.log.info(f"Total rows loaded: {len(combined)}")

    return combined


@op(
    description="Clean and standardize data",
    ins={"raw_df": In(dagster_type=pl.DataFrame)},
    out=Out(dagster_type=pl.DataFrame),
)
def clean_data(
    context: OpExecutionContext,
    config: TransformationJobConfig,
    raw_df: pl.DataFrame,
    event_bus: EventBusResource,
) -> pl.DataFrame:
    """Apply cleaning transformations.

    Includes column operations, null handling, and deduplication.
    """
    from datetime import datetime

    context.log.info(f"Cleaning {len(raw_df)} rows")

    if raw_df.is_empty():
        return raw_df

    df = raw_df
    original_count = len(df)
    operations = []

    # Drop columns
    if config.drop_columns:
        existing = [c for c in config.drop_columns if c in df.columns]
        if existing:
            df = df.drop(existing)
            operations.append(f"Dropped: {existing}")

    # Rename columns
    if config.rename_columns:
        for old, new in config.rename_columns.items():
            if old in df.columns:
                df = df.rename({old: new})
        operations.append(f"Renamed columns")

    # Remove null rows
    df = df.filter(~pl.all_horizontal(pl.all().is_null()))

    # Trim strings
    string_cols = [c for c in df.columns if df[c].dtype in (pl.Utf8, pl.String)]
    for col in string_cols:
        df = df.with_columns(pl.col(col).str.strip_chars())

    # Deduplicate
    if config.dedupe_columns:
        before = len(df)
        df = df.unique(subset=config.dedupe_columns, keep="last")
        removed = before - len(df)
        if removed > 0:
            operations.append(f"Deduped: removed {removed} rows")

    # Add metadata
    df = df.with_columns([
        pl.lit(config.dataset_id).alias("_dataset_id"),
        pl.lit(datetime.now()).alias("_cleaned_at"),
    ])

    context.log.info(f"Cleaning complete: {len(df)} rows ({original_count - len(df)} removed)")

    event_bus.publish_sync("data.cleaned", {
        "dataset_id": config.dataset_id,
        "original": original_count,
        "final": len(df),
        "operations": operations,
    })

    return df


@op(
    description="Enrich data with lookups and derived columns",
    ins={"cleaned_df": In(dagster_type=pl.DataFrame)},
    out=Out(dagster_type=pl.DataFrame),
)
def enrich_data(
    context: OpExecutionContext,
    config: TransformationJobConfig,
    cleaned_df: pl.DataFrame,
    iceberg: IcebergResource,
    event_bus: EventBusResource,
) -> pl.DataFrame:
    """Apply enrichment transformations.

    Joins with lookup tables and extracts date components.
    """
    from datetime import datetime

    context.log.info(f"Enriching {len(cleaned_df)} rows")

    if cleaned_df.is_empty():
        return cleaned_df

    df = cleaned_df
    original_cols = len(df.columns)

    # Join with lookup table
    if config.lookup_table and config.lookup_key:
        if iceberg.table_exists("reference", config.lookup_table):
            lookup_df = iceberg.read_table("reference", config.lookup_table)
            if not lookup_df.is_empty() and config.lookup_key in df.columns:
                df = df.join(lookup_df, on=config.lookup_key, how="left")
                context.log.info(f"Joined with {config.lookup_table}")

    # Extract date parts from time column
    if config.time_column and config.time_column in df.columns:
        try:
            if df[config.time_column].dtype not in (pl.Date, pl.Datetime):
                df = df.with_columns(
                    pl.col(config.time_column).str.to_datetime().alias(config.time_column)
                )

            df = df.with_columns([
                pl.col(config.time_column).dt.year().alias(f"{config.time_column}_year"),
                pl.col(config.time_column).dt.month().alias(f"{config.time_column}_month"),
                pl.col(config.time_column).dt.day().alias(f"{config.time_column}_day"),
                pl.col(config.time_column).dt.weekday().alias(f"{config.time_column}_weekday"),
            ])
            context.log.info(f"Extracted date parts from {config.time_column}")
        except Exception as e:
            context.log.warning(f"Could not extract date parts: {e}")

    # Add metadata
    df = df.with_columns([
        pl.lit(datetime.now()).alias("_enriched_at"),
    ])

    added = len(df.columns) - original_cols
    context.log.info(f"Enrichment complete: added {added} columns")

    event_bus.publish_sync("data.enriched", {
        "dataset_id": config.dataset_id,
        "row_count": len(df),
        "columns_added": added,
    })

    return df


@op(
    description="Aggregate data into summaries",
    ins={"enriched_df": In(dagster_type=pl.DataFrame)},
    out=Out(dagster_type=pl.DataFrame),
)
def aggregate_data(
    context: OpExecutionContext,
    config: TransformationJobConfig,
    enriched_df: pl.DataFrame,
    event_bus: EventBusResource,
) -> pl.DataFrame:
    """Apply aggregation transformations.

    Produces summary metrics grouped by specified dimensions.
    """
    from datetime import datetime

    context.log.info(f"Aggregating {len(enriched_df)} rows")

    if enriched_df.is_empty():
        return enriched_df

    # Skip aggregation if not configured
    if not config.aggregations or not config.group_by_columns:
        context.log.info("No aggregations configured, returning enriched data")
        return enriched_df

    df = enriched_df

    # Build aggregation expressions
    agg_funcs = {
        "sum": lambda c: pl.col(c).sum(),
        "count": lambda c: pl.col(c).count(),
        "avg": lambda c: pl.col(c).mean(),
        "min": lambda c: pl.col(c).min(),
        "max": lambda c: pl.col(c).max(),
        "first": lambda c: pl.col(c).first(),
        "last": lambda c: pl.col(c).last(),
        "nunique": lambda c: pl.col(c).n_unique(),
    }

    agg_exprs = []
    for col, func in config.aggregations.items():
        if col in df.columns and func.lower() in agg_funcs:
            agg_exprs.append(
                agg_funcs[func.lower()](col).alias(f"{col}_{func}")
            )

    if not agg_exprs:
        context.log.warning("No valid aggregations")
        return enriched_df

    # Apply time-based grouping
    group_cols = list(config.group_by_columns)

    if config.time_column and config.time_granularity:
        if config.time_column in df.columns:
            granularity_map = {
                "day": "1d",
                "week": "1w",
                "month": "1mo",
                "hour": "1h",
            }
            interval = granularity_map.get(config.time_granularity, "1d")
            time_col = f"{config.time_column}_{config.time_granularity}"

            if df[config.time_column].dtype not in (pl.Date, pl.Datetime):
                df = df.with_columns(
                    pl.col(config.time_column).str.to_datetime().alias(config.time_column)
                )

            df = df.with_columns(
                pl.col(config.time_column).dt.truncate(interval).alias(time_col)
            )
            group_cols.append(time_col)

    # Perform aggregation
    result = df.group_by(group_cols).agg(agg_exprs)

    # Add metadata
    result = result.with_columns([
        pl.lit(config.dataset_id).alias("_dataset_id"),
        pl.lit(datetime.now()).alias("_aggregated_at"),
    ])

    context.log.info(f"Aggregation complete: {len(df)} -> {len(result)} groups")

    event_bus.publish_sync("data.aggregated", {
        "dataset_id": config.dataset_id,
        "source_rows": len(df),
        "result_rows": len(result),
        "groups": group_cols,
    })

    return result


@op(
    description="Write transformed data to curated layer",
    ins={"df": In(dagster_type=pl.DataFrame)},
)
def write_curated_data(
    context: OpExecutionContext,
    config: TransformationJobConfig,
    df: pl.DataFrame,
    iceberg: IcebergResource,
    event_bus: EventBusResource,
) -> None:
    """Write final transformed data to Iceberg.

    Stores in the curated namespace for consumption.
    """
    if df.is_empty():
        context.log.info("No data to write")
        return

    table_name = f"curated_{config.dataset_id}"

    # Ensure namespace exists
    iceberg.create_namespace(config.target_namespace)

    # Create or append to table
    if iceberg.table_exists(config.target_namespace, table_name):
        iceberg.overwrite_data(config.target_namespace, table_name, df)
        context.log.info(f"Overwrote {len(df)} rows in {table_name}")
    else:
        # Create table
        from pipelines.io_managers import IcebergIOManager
        io_manager = IcebergIOManager()
        schema_fields = io_manager._infer_schema(df)
        iceberg.create_table(config.target_namespace, table_name, schema_fields)
        iceberg.append_data(config.target_namespace, table_name, df)
        context.log.info(f"Created {table_name} with {len(df)} rows")

    event_bus.publish_sync("data.curated", {
        "dataset_id": config.dataset_id,
        "table": f"{config.target_namespace}.{table_name}",
        "row_count": len(df),
    })


@op(
    description="Discover datasets for batch transformation",
    out=DynamicOut(dagster_type=str),
)
def discover_datasets(
    context: OpExecutionContext,
    config: MultiDatasetConfig,
    database: DatabaseResource,
) -> None:
    """Discover datasets ready for transformation."""
    if config.dataset_ids:
        datasets = config.dataset_ids
    else:
        with database.get_session() as session:
            try:
                result = session.execute(
                    """
                    SELECT dataset_id FROM datasets
                    WHERE status = 'staged' AND is_active = true
                    """
                )
                datasets = [row[0] for row in result]
            except Exception as e:
                context.log.warning(f"Could not query datasets: {e}")
                datasets = []

    context.log.info(f"Discovered {len(datasets)} datasets")

    for dataset_id in datasets:
        yield DynamicOutput(dataset_id, mapping_key=dataset_id.replace("-", "_"))


@graph
def transformation_pipeline():
    """Graph for single dataset transformation."""
    staged = load_staged_data()
    cleaned = clean_data(staged)
    enriched = enrich_data(cleaned)
    aggregated = aggregate_data(enriched)
    write_curated_data(aggregated)


@job(
    description="Transform data for a single dataset",
    tags={"type": "transformation", "scope": "single"},
)
def transformation_job():
    """Job to transform a single dataset.

    Runs: load -> clean -> enrich -> aggregate -> write.
    """
    transformation_pipeline()


@graph
def multi_dataset_transformation_pipeline():
    """Graph for multi-dataset batch transformation."""
    datasets = discover_datasets()
    datasets.map(lambda ds_id: transformation_pipeline())


@job(
    description="Transform multiple datasets",
    tags={"type": "transformation", "scope": "batch"},
)
def full_transformation_job():
    """Job to transform multiple datasets.

    Discovers staged datasets and runs transformation for each.
    """
    multi_dataset_transformation_pipeline()


# Schedules
hourly_transformation_schedule = ScheduleDefinition(
    job=transformation_job,
    cron_schedule="30 * * * *",  # 30 minutes past each hour
    name="hourly_transformation",
    description="Run transformation job every hour",
)

daily_full_transformation_schedule = ScheduleDefinition(
    job=full_transformation_job,
    cron_schedule="0 4 * * *",  # 4 AM daily
    name="daily_full_transformation",
    description="Run full transformation across all datasets daily",
)
