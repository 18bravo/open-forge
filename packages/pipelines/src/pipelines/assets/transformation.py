"""
Data transformation assets for Open Forge.

Handles data cleaning, enrichment, and aggregation operations
on staged data to produce curated datasets.
"""
from typing import Any, Dict, List, Optional, Union
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


class TransformationConfig(Config):
    """Configuration for data transformation."""

    dataset_id: str
    dataset_name: str
    source_namespace: str = "staged"
    source_tables: List[str] = []
    target_namespace: str = "curated"


class CleaningConfig(TransformationConfig):
    """Configuration for data cleaning transformation."""

    # Column operations
    drop_columns: Optional[List[str]] = None
    rename_columns: Optional[Dict[str, str]] = None
    # Null handling
    drop_null_columns: Optional[List[str]] = None
    fill_null_values: Optional[Dict[str, Any]] = None
    # String cleaning
    trim_string_columns: bool = True
    lowercase_columns: Optional[List[str]] = None
    uppercase_columns: Optional[List[str]] = None
    # Deduplication
    dedupe_columns: Optional[List[str]] = None


class EnrichmentConfig(TransformationConfig):
    """Configuration for data enrichment."""

    # Lookup joins
    lookup_table: Optional[str] = None
    lookup_namespace: str = "reference"
    lookup_key: Optional[str] = None
    lookup_columns: Optional[List[str]] = None
    # Derived columns
    derived_columns: Optional[Dict[str, str]] = None  # column_name -> polars expression
    # Date/time enrichment
    date_columns: Optional[List[str]] = None
    extract_date_parts: bool = True


class AggregationConfig(TransformationConfig):
    """Configuration for data aggregation."""

    group_by_columns: List[str] = []
    aggregations: Dict[str, str] = {}  # column -> agg_function
    # Time-based aggregation
    time_column: Optional[str] = None
    time_granularity: Optional[str] = None  # "day", "week", "month"


@asset(
    key_prefix=["curated"],
    group_name="transformation",
    description="Cleaned and standardized data",
    compute_kind="polars",
)
def cleaned_data(
    context: AssetExecutionContext,
    config: CleaningConfig,
    iceberg: IcebergResource,
    event_bus: EventBusResource,
) -> Output[pl.DataFrame]:
    """Apply cleaning transformations to staged data.

    Cleaning operations include:
    - Column removal and renaming
    - Null value handling
    - String normalization
    - Deduplication
    - Type standardization

    Each operation is logged for lineage tracking.
    """
    context.log.info(f"Cleaning data for dataset: {config.dataset_name}")

    # Load source data
    dfs = []
    for table in config.source_tables:
        df = iceberg.read_table(config.source_namespace, table)
        dfs.append(df)

    if not dfs:
        context.log.warning("No source tables found")
        return Output(pl.DataFrame())

    # Combine source tables
    df = pl.concat(dfs, how="diagonal") if len(dfs) > 1 else dfs[0]
    original_count = len(df)

    operations_applied = []

    # Drop columns
    if config.drop_columns:
        existing_cols = [c for c in config.drop_columns if c in df.columns]
        if existing_cols:
            df = df.drop(existing_cols)
            operations_applied.append(f"Dropped columns: {existing_cols}")

    # Rename columns
    if config.rename_columns:
        for old_name, new_name in config.rename_columns.items():
            if old_name in df.columns:
                df = df.rename({old_name: new_name})
        operations_applied.append(f"Renamed columns: {list(config.rename_columns.keys())}")

    # Drop rows with nulls in specified columns
    if config.drop_null_columns:
        for col in config.drop_null_columns:
            if col in df.columns:
                df = df.filter(pl.col(col).is_not_null())
        operations_applied.append(f"Dropped nulls in: {config.drop_null_columns}")

    # Fill null values
    if config.fill_null_values:
        for col, value in config.fill_null_values.items():
            if col in df.columns:
                df = df.with_columns(pl.col(col).fill_null(value))
        operations_applied.append(f"Filled nulls in: {list(config.fill_null_values.keys())}")

    # String operations
    if config.trim_string_columns:
        string_cols = [
            col for col in df.columns
            if df[col].dtype in (pl.Utf8, pl.String)
        ]
        for col in string_cols:
            df = df.with_columns(pl.col(col).str.strip_chars())
        operations_applied.append("Trimmed string columns")

    if config.lowercase_columns:
        for col in config.lowercase_columns:
            if col in df.columns:
                df = df.with_columns(pl.col(col).str.to_lowercase())
        operations_applied.append(f"Lowercased: {config.lowercase_columns}")

    if config.uppercase_columns:
        for col in config.uppercase_columns:
            if col in df.columns:
                df = df.with_columns(pl.col(col).str.to_uppercase())
        operations_applied.append(f"Uppercased: {config.uppercase_columns}")

    # Deduplication
    if config.dedupe_columns:
        before = len(df)
        df = df.unique(subset=config.dedupe_columns, keep="last")
        operations_applied.append(f"Deduped on {config.dedupe_columns}: removed {before - len(df)} rows")

    # Add transformation metadata
    df = df.with_columns([
        pl.lit(config.dataset_id).alias("_dataset_id"),
        pl.lit(datetime.now()).alias("_cleaned_at"),
    ])

    rows_removed = original_count - len(df)

    # Publish event
    event_bus.publish_sync(
        "data.cleaned",
        {
            "dataset_id": config.dataset_id,
            "dataset_name": config.dataset_name,
            "original_count": original_count,
            "final_count": len(df),
            "operations": operations_applied,
        }
    )

    context.log.info(f"Cleaning complete: {len(df)} rows ({rows_removed} removed)")

    return Output(
        df,
        metadata={
            "dataset_id": MetadataValue.text(config.dataset_id),
            "original_row_count": MetadataValue.int(original_count),
            "final_row_count": MetadataValue.int(len(df)),
            "rows_removed": MetadataValue.int(rows_removed),
            "operations_applied": MetadataValue.json(operations_applied),
        }
    )


@asset(
    key_prefix=["curated"],
    group_name="transformation",
    description="Data enriched with lookups and derived columns",
    deps=[AssetKey(["curated", "cleaned_data"])],
    compute_kind="polars",
)
def enriched_data(
    context: AssetExecutionContext,
    config: EnrichmentConfig,
    iceberg: IcebergResource,
    database: DatabaseResource,
    event_bus: EventBusResource,
) -> Output[pl.DataFrame]:
    """Enrich cleaned data with additional information.

    Enrichment operations include:
    - Lookup table joins (e.g., reference data)
    - Derived column calculations
    - Date/time component extraction
    - Geographic enrichment (if applicable)

    Preserves original columns while adding enrichment data.
    """
    context.log.info(f"Enriching data for dataset: {config.dataset_name}")

    # Load cleaned data
    df = iceberg.read_table(config.target_namespace, f"cleaned_{config.dataset_id}")
    original_columns = len(df.columns)
    enrichments_applied = []

    # Apply lookup join
    if config.lookup_table and config.lookup_key:
        context.log.info(f"Joining with lookup table: {config.lookup_table}")

        lookup_df = iceberg.read_table(
            config.lookup_namespace,
            config.lookup_table,
            columns=config.lookup_columns
        )

        if not lookup_df.is_empty():
            df = df.join(
                lookup_df,
                on=config.lookup_key,
                how="left"
            )
            enrichments_applied.append(f"Lookup join: {config.lookup_table}")

    # Apply derived columns
    if config.derived_columns:
        for col_name, expression in config.derived_columns.items():
            try:
                # Parse and evaluate polars expression
                # Note: In production, use a safer expression parser
                df = df.with_columns(eval(expression).alias(col_name))
                enrichments_applied.append(f"Derived column: {col_name}")
            except Exception as e:
                context.log.warning(f"Failed to create derived column {col_name}: {e}")

    # Extract date parts
    if config.date_columns and config.extract_date_parts:
        for col in config.date_columns:
            if col in df.columns:
                try:
                    # Ensure column is datetime type
                    if df[col].dtype not in (pl.Date, pl.Datetime):
                        df = df.with_columns(pl.col(col).str.to_datetime())

                    df = df.with_columns([
                        pl.col(col).dt.year().alias(f"{col}_year"),
                        pl.col(col).dt.month().alias(f"{col}_month"),
                        pl.col(col).dt.day().alias(f"{col}_day"),
                        pl.col(col).dt.weekday().alias(f"{col}_weekday"),
                        pl.col(col).dt.quarter().alias(f"{col}_quarter"),
                    ])
                    enrichments_applied.append(f"Date parts: {col}")
                except Exception as e:
                    context.log.warning(f"Failed to extract date parts from {col}: {e}")

    # Add enrichment metadata
    df = df.with_columns([
        pl.lit(datetime.now()).alias("_enriched_at"),
    ])

    columns_added = len(df.columns) - original_columns

    # Publish event
    event_bus.publish_sync(
        "data.enriched",
        {
            "dataset_id": config.dataset_id,
            "dataset_name": config.dataset_name,
            "row_count": len(df),
            "columns_added": columns_added,
            "enrichments": enrichments_applied,
        }
    )

    context.log.info(f"Enrichment complete: added {columns_added} columns")

    return Output(
        df,
        metadata={
            "dataset_id": MetadataValue.text(config.dataset_id),
            "row_count": MetadataValue.int(len(df)),
            "original_columns": MetadataValue.int(original_columns),
            "final_columns": MetadataValue.int(len(df.columns)),
            "columns_added": MetadataValue.int(columns_added),
            "enrichments_applied": MetadataValue.json(enrichments_applied),
        }
    )


@asset(
    key_prefix=["curated"],
    group_name="transformation",
    description="Aggregated metrics and summaries",
    deps=[AssetKey(["curated", "enriched_data"])],
    compute_kind="polars",
)
def aggregated_data(
    context: AssetExecutionContext,
    config: AggregationConfig,
    iceberg: IcebergResource,
    event_bus: EventBusResource,
) -> Output[pl.DataFrame]:
    """Aggregate enriched data into summary tables.

    Supports:
    - Group-by aggregations (sum, count, avg, min, max)
    - Time-based rollups (daily, weekly, monthly)
    - Multiple aggregation levels

    Produces pre-computed metrics for dashboards and analytics.
    """
    context.log.info(f"Aggregating data for dataset: {config.dataset_name}")

    # Load enriched data
    df = iceberg.read_table(config.target_namespace, f"enriched_{config.dataset_id}")

    if df.is_empty():
        context.log.warning("No data to aggregate")
        return Output(pl.DataFrame())

    # Build aggregation expressions
    agg_mapping = {
        "sum": lambda c: pl.col(c).sum(),
        "count": lambda c: pl.col(c).count(),
        "avg": lambda c: pl.col(c).mean(),
        "mean": lambda c: pl.col(c).mean(),
        "min": lambda c: pl.col(c).min(),
        "max": lambda c: pl.col(c).max(),
        "first": lambda c: pl.col(c).first(),
        "last": lambda c: pl.col(c).last(),
        "std": lambda c: pl.col(c).std(),
        "var": lambda c: pl.col(c).var(),
        "median": lambda c: pl.col(c).median(),
        "nunique": lambda c: pl.col(c).n_unique(),
    }

    agg_exprs = []
    for col, agg_func in config.aggregations.items():
        if col in df.columns and agg_func.lower() in agg_mapping:
            agg_exprs.append(
                agg_mapping[agg_func.lower()](col).alias(f"{col}_{agg_func}")
            )

    if not agg_exprs:
        context.log.warning("No valid aggregations specified")
        return Output(df)

    # Apply time-based grouping if configured
    group_cols = list(config.group_by_columns)

    if config.time_column and config.time_granularity:
        if config.time_column in df.columns:
            # Truncate time to specified granularity
            granularity_map = {
                "day": "1d",
                "week": "1w",
                "month": "1mo",
                "quarter": "1q",
                "year": "1y",
                "hour": "1h",
            }

            interval = granularity_map.get(config.time_granularity, "1d")
            time_col = f"{config.time_column}_{config.time_granularity}"

            # Ensure datetime type
            if df[config.time_column].dtype not in (pl.Date, pl.Datetime):
                df = df.with_columns(
                    pl.col(config.time_column).str.to_datetime().alias(config.time_column)
                )

            df = df.with_columns(
                pl.col(config.time_column).dt.truncate(interval).alias(time_col)
            )
            group_cols.append(time_col)

    # Perform aggregation
    if group_cols:
        result_df = df.group_by(group_cols).agg(agg_exprs)
    else:
        # Global aggregation
        result_df = df.select(agg_exprs)

    # Add aggregation metadata
    result_df = result_df.with_columns([
        pl.lit(config.dataset_id).alias("_dataset_id"),
        pl.lit(datetime.now()).alias("_aggregated_at"),
    ])

    # Publish event
    event_bus.publish_sync(
        "data.aggregated",
        {
            "dataset_id": config.dataset_id,
            "dataset_name": config.dataset_name,
            "source_rows": len(df),
            "result_rows": len(result_df),
            "group_columns": group_cols,
            "aggregations": list(config.aggregations.keys()),
        }
    )

    context.log.info(
        f"Aggregation complete: {len(df)} rows -> {len(result_df)} groups"
    )

    return Output(
        result_df,
        metadata={
            "dataset_id": MetadataValue.text(config.dataset_id),
            "source_row_count": MetadataValue.int(len(df)),
            "aggregated_row_count": MetadataValue.int(len(result_df)),
            "group_columns": MetadataValue.json(group_cols),
            "aggregations": MetadataValue.json(list(config.aggregations.keys())),
            "time_granularity": MetadataValue.text(config.time_granularity or "none"),
        }
    )
