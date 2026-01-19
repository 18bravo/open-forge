# Pipeline Creation Guide

This guide explains how to create and manage data pipelines in Open Forge using Dagster.

## Table of Contents

- [Pipeline Overview](#pipeline-overview)
- [Dagster Concepts](#dagster-concepts)
- [Creating Pipelines](#creating-pipelines)
- [Pipeline Configuration](#pipeline-configuration)
- [Scheduling and Sensors](#scheduling-and-sensors)
- [Monitoring and Debugging](#monitoring-and-debugging)
- [Best Practices](#best-practices)

---

## Pipeline Overview

Open Forge uses **Dagster** for data pipeline orchestration. Pipelines handle:

- **Data Ingestion**: Loading data from various sources
- **Transformation**: Cleaning, enriching, and reshaping data
- **Loading**: Writing data to target systems (Iceberg, databases)
- **Orchestration**: Scheduling and dependency management

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Sources   │────▶│  Transform  │────▶│   Targets   │
│             │     │             │     │             │
│ - PostgreSQL│     │ - Clean     │     │ - Iceberg   │
│ - S3/CSV    │     │ - Enrich    │     │ - PostgreSQL│
│ - APIs      │     │ - Aggregate │     │ - MinIO     │
└─────────────┘     └─────────────┘     └─────────────┘
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                    ┌───────▼───────┐
                    │    Dagster    │
                    │  Orchestrator │
                    └───────────────┘
```

---

## Dagster Concepts

### Assets

**Assets** are the core building blocks - they represent data artifacts:

```python
from dagster import asset
import polars as pl

@asset(
    description="Raw customer data from source database",
    group_name="ingestion"
)
def raw_customers(database: DatabaseResource) -> pl.DataFrame:
    """Load raw customer data from source database."""
    return pl.read_database(
        "SELECT * FROM customers",
        database.connection_string
    )

@asset(
    description="Cleaned and validated customer data",
    group_name="transformation"
)
def clean_customers(raw_customers: pl.DataFrame) -> pl.DataFrame:
    """Clean and validate customer data."""
    return (
        raw_customers
        .drop_nulls(subset=["email"])
        .unique(subset=["customer_id"])
        .with_columns([
            pl.col("email").str.to_lowercase(),
            pl.col("created_at").cast(pl.Datetime)
        ])
    )
```

### Resources

**Resources** provide connections to external systems:

```python
from dagster import ConfigurableResource
from sqlalchemy import create_engine

class DatabaseResource(ConfigurableResource):
    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_connection(self):
        return create_engine(self.connection_string)
```

### Jobs

**Jobs** define which assets to materialize together:

```python
from dagster import define_asset_job, AssetSelection

# Job for all ingestion assets
ingestion_job = define_asset_job(
    name="ingestion_job",
    selection=AssetSelection.groups("ingestion"),
    description="Ingest data from all sources"
)

# Job for specific assets
customer_pipeline = define_asset_job(
    name="customer_pipeline",
    selection=AssetSelection.assets("raw_customers", "clean_customers", "customer_metrics")
)
```

### Sensors

**Sensors** trigger jobs based on external events:

```python
from dagster import sensor, RunRequest

@sensor(job=ingestion_job)
def new_file_sensor(context, s3: S3Resource):
    """Trigger ingestion when new files arrive in S3."""
    new_files = s3.list_new_files("raw-data/")

    if new_files:
        yield RunRequest(
            run_key=f"files_{datetime.now().isoformat()}",
            run_config={
                "ops": {
                    "ingest_files": {"config": {"files": new_files}}
                }
            }
        )
```

---

## Creating Pipelines

### Step 1: Define Source Assets

```python
# packages/pipelines/src/pipelines/assets/ingestion.py

from dagster import asset, AssetExecutionContext
import polars as pl

from pipelines.resources import DatabaseResource, IcebergResource

@asset(
    description="Raw customer data from source PostgreSQL",
    group_name="ingestion",
    compute_kind="sql",
    metadata={
        "source_table": "public.customers",
        "update_frequency": "hourly"
    }
)
def raw_customers(
    context: AssetExecutionContext,
    database: DatabaseResource
) -> pl.DataFrame:
    """Ingest customer data from source database."""
    query = """
        SELECT
            customer_id,
            email,
            first_name,
            last_name,
            created_at,
            updated_at
        FROM public.customers
        WHERE updated_at > :last_run
    """

    last_run = context.instance.get_latest_materialization_timestamp(
        context.asset_key
    )

    df = pl.read_database(query, database.get_connection(), params={
        "last_run": last_run or "1970-01-01"
    })

    context.log.info(f"Loaded {len(df)} customer records")
    context.add_output_metadata({
        "row_count": len(df),
        "columns": list(df.columns)
    })

    return df


@asset(
    description="Raw order data from source PostgreSQL",
    group_name="ingestion",
    compute_kind="sql"
)
def raw_orders(
    context: AssetExecutionContext,
    database: DatabaseResource
) -> pl.DataFrame:
    """Ingest order data from source database."""
    query = """
        SELECT
            order_id,
            customer_id,
            order_date,
            status,
            total_amount
        FROM public.orders
        WHERE order_date >= CURRENT_DATE - INTERVAL '7 days'
    """

    df = pl.read_database(query, database.get_connection())
    context.log.info(f"Loaded {len(df)} order records")

    return df
```

### Step 2: Define Transformation Assets

```python
# packages/pipelines/src/pipelines/assets/transformation.py

from dagster import asset, AssetExecutionContext, AssetIn
import polars as pl

@asset(
    description="Cleaned and validated customer data",
    group_name="transformation",
    compute_kind="polars",
    ins={
        "raw_customers": AssetIn(key="raw_customers")
    }
)
def clean_customers(
    context: AssetExecutionContext,
    raw_customers: pl.DataFrame
) -> pl.DataFrame:
    """Clean and validate customer data."""
    initial_count = len(raw_customers)

    clean_df = (
        raw_customers
        # Remove invalid emails
        .filter(pl.col("email").str.contains("@"))
        # Normalize email to lowercase
        .with_columns([
            pl.col("email").str.to_lowercase().alias("email"),
            pl.col("first_name").str.strip_chars().alias("first_name"),
            pl.col("last_name").str.strip_chars().alias("last_name"),
        ])
        # Remove duplicates
        .unique(subset=["customer_id"], keep="last")
        # Add processing metadata
        .with_columns([
            pl.lit(context.run_id).alias("_processing_run_id"),
            pl.lit(datetime.now()).alias("_processed_at")
        ])
    )

    removed = initial_count - len(clean_df)
    context.log.info(f"Cleaned {len(clean_df)} records, removed {removed}")

    context.add_output_metadata({
        "input_rows": initial_count,
        "output_rows": len(clean_df),
        "rows_removed": removed,
        "removal_rate": f"{removed/initial_count*100:.1f}%"
    })

    return clean_df


@asset(
    description="Customer metrics aggregated from orders",
    group_name="transformation",
    compute_kind="polars"
)
def customer_metrics(
    context: AssetExecutionContext,
    clean_customers: pl.DataFrame,
    raw_orders: pl.DataFrame
) -> pl.DataFrame:
    """Calculate customer metrics from order data."""
    order_metrics = (
        raw_orders
        .group_by("customer_id")
        .agg([
            pl.count().alias("total_orders"),
            pl.sum("total_amount").alias("total_spent"),
            pl.mean("total_amount").alias("avg_order_value"),
            pl.min("order_date").alias("first_order_date"),
            pl.max("order_date").alias("last_order_date")
        ])
    )

    metrics_df = (
        clean_customers
        .join(order_metrics, on="customer_id", how="left")
        .with_columns([
            pl.col("total_orders").fill_null(0),
            pl.col("total_spent").fill_null(0),
            # Calculate customer lifetime (days)
            (pl.col("last_order_date") - pl.col("first_order_date"))
                .dt.total_days()
                .alias("customer_lifetime_days")
        ])
    )

    context.log.info(f"Generated metrics for {len(metrics_df)} customers")

    return metrics_df
```

### Step 3: Define Output Assets

```python
# packages/pipelines/src/pipelines/assets/output.py

from dagster import asset, AssetExecutionContext
import polars as pl

@asset(
    description="Customer metrics stored in Iceberg",
    group_name="output",
    compute_kind="iceberg",
    io_manager_key="iceberg_io_manager"
)
def iceberg_customer_metrics(
    context: AssetExecutionContext,
    customer_metrics: pl.DataFrame,
    iceberg: IcebergResource
) -> pl.DataFrame:
    """Write customer metrics to Iceberg table."""
    # The IO manager handles the actual write
    context.log.info(f"Writing {len(customer_metrics)} records to Iceberg")

    return customer_metrics
```

### Step 4: Create Jobs

```python
# packages/pipelines/src/pipelines/jobs/customer_job.py

from dagster import define_asset_job, AssetSelection, ScheduleDefinition

# Define the job
customer_pipeline = define_asset_job(
    name="customer_pipeline",
    selection=AssetSelection.assets(
        "raw_customers",
        "raw_orders",
        "clean_customers",
        "customer_metrics",
        "iceberg_customer_metrics"
    ),
    description="Complete customer data pipeline"
)

# Daily schedule
daily_customer_schedule = ScheduleDefinition(
    job=customer_pipeline,
    cron_schedule="0 2 * * *",  # 2 AM daily
    description="Run customer pipeline daily at 2 AM"
)
```

---

## Pipeline Configuration

### Resource Configuration

Configure resources in `definitions.py`:

```python
# packages/pipelines/src/pipelines/definitions.py

from dagster import Definitions, EnvVar

from pipelines.resources import DatabaseResource, IcebergResource
from pipelines.io_managers import IcebergIOManager
from pipelines.assets import ingestion, transformation, output
from pipelines.jobs import customer_job

resource_defs = {
    "database": DatabaseResource(
        host=EnvVar("DB_HOST"),
        port=EnvVar.int("DB_PORT"),
        user=EnvVar("DB_USER"),
        password=EnvVar("DB_PASSWORD"),
        database=EnvVar("DB_NAME"),
    ),
    "iceberg": IcebergResource(
        catalog_uri=EnvVar("ICEBERG_CATALOG_URI"),
        warehouse_path=EnvVar("ICEBERG_WAREHOUSE"),
    ),
    "iceberg_io_manager": IcebergIOManager(
        namespace="analytics",
        write_mode="append",
    ),
}

defs = Definitions(
    assets=[
        *ingestion.assets,
        *transformation.assets,
        *output.assets,
    ],
    jobs=[customer_job.customer_pipeline],
    schedules=[customer_job.daily_customer_schedule],
    resources=resource_defs,
)
```

### Environment-Specific Configuration

```python
# Development configuration
def get_dev_definitions():
    dev_resources = {
        "database": DatabaseResource(
            host="localhost",
            port=5432,
            user="dev",
            password="dev",
            database="dev_db",
        ),
        "iceberg_io_manager": IcebergIOManager(
            namespace="dev",
            write_mode="overwrite",  # Overwrite in dev
        ),
    }

    return Definitions(
        assets=all_assets,
        jobs=all_jobs,
        schedules=[],  # No schedules in dev
        resources=dev_resources,
    )
```

### Partitioned Assets

Handle time-partitioned data:

```python
from dagster import (
    asset,
    DailyPartitionsDefinition,
    AssetExecutionContext
)

daily_partitions = DailyPartitionsDefinition(start_date="2024-01-01")

@asset(
    partitions_def=daily_partitions,
    description="Daily order summary",
    group_name="daily_metrics"
)
def daily_order_summary(
    context: AssetExecutionContext,
    raw_orders: pl.DataFrame
) -> pl.DataFrame:
    """Calculate daily order summary for partition."""
    partition_date = context.partition_key

    daily_orders = (
        raw_orders
        .filter(pl.col("order_date") == partition_date)
        .group_by(pl.lit(True))
        .agg([
            pl.count().alias("order_count"),
            pl.sum("total_amount").alias("total_revenue"),
            pl.n_unique("customer_id").alias("unique_customers")
        ])
        .with_columns([
            pl.lit(partition_date).alias("date")
        ])
    )

    return daily_orders
```

---

## Scheduling and Sensors

### Schedule Definitions

```python
from dagster import ScheduleDefinition, schedule

# Simple cron schedule
hourly_schedule = ScheduleDefinition(
    job=ingestion_job,
    cron_schedule="0 * * * *",  # Every hour
    description="Hourly data ingestion"
)

# Schedule with timezone
daily_schedule = ScheduleDefinition(
    job=transformation_job,
    cron_schedule="0 6 * * *",  # 6 AM
    execution_timezone="America/New_York",
    description="Daily transformation at 6 AM ET"
)

# Custom schedule with dynamic config
@schedule(cron_schedule="0 */4 * * *", job=customer_pipeline)
def adaptive_schedule(context):
    """Schedule with dynamic configuration based on time."""
    hour = datetime.now().hour

    # Run full pipeline during off-peak hours
    if 0 <= hour < 6:
        run_mode = "full"
    else:
        run_mode = "incremental"

    return RunRequest(
        run_config={
            "ops": {"config": {"mode": run_mode}}
        }
    )
```

### Sensor Definitions

```python
from dagster import sensor, RunRequest, SensorEvaluationContext

@sensor(job=ingestion_job, minimum_interval_seconds=60)
def new_data_sensor(
    context: SensorEvaluationContext,
    database: DatabaseResource
):
    """Trigger when new data is available in source."""
    # Check for new data
    last_processed = context.cursor or "1970-01-01"

    new_records = database.query(f"""
        SELECT COUNT(*) as count, MAX(updated_at) as max_updated
        FROM customers
        WHERE updated_at > '{last_processed}'
    """)

    if new_records["count"] > 0:
        context.update_cursor(str(new_records["max_updated"]))

        yield RunRequest(
            run_key=f"new_data_{new_records['max_updated']}",
            run_config={
                "ops": {
                    "raw_customers": {
                        "config": {"since": last_processed}
                    }
                }
            }
        )


@sensor(job=customer_pipeline, minimum_interval_seconds=300)
def s3_file_sensor(
    context: SensorEvaluationContext,
    s3: S3Resource
):
    """Trigger when new files arrive in S3."""
    bucket = "raw-data"
    prefix = "customers/"

    # List files modified since last run
    last_modified = context.cursor or "1970-01-01T00:00:00Z"
    new_files = s3.list_objects(
        bucket,
        prefix,
        modified_after=last_modified
    )

    if new_files:
        latest_modified = max(f["LastModified"] for f in new_files)
        context.update_cursor(latest_modified.isoformat())

        yield RunRequest(
            run_key=f"s3_files_{latest_modified.isoformat()}",
            run_config={
                "resources": {
                    "s3_files": {"config": {"files": [f["Key"] for f in new_files]}}
                }
            }
        )
```

---

## Monitoring and Debugging

### Dagster UI

Access the Dagster UI at `http://localhost:3000`:

- **Assets**: View asset lineage and materialization history
- **Runs**: Monitor running and completed pipeline runs
- **Schedules**: Manage scheduled jobs
- **Sensors**: Monitor sensor activity

### Logging

Add structured logging to assets:

```python
@asset
def my_asset(context: AssetExecutionContext):
    context.log.info("Starting processing")
    context.log.debug(f"Config: {context.op_config}")

    try:
        result = process_data()
        context.log.info(f"Processed {len(result)} records")
    except Exception as e:
        context.log.error(f"Processing failed: {e}")
        raise

    return result
```

### Output Metadata

Add rich metadata to asset outputs:

```python
@asset
def enriched_data(context: AssetExecutionContext, raw_data: pl.DataFrame):
    result = enrich(raw_data)

    # Add metadata visible in UI
    context.add_output_metadata({
        "row_count": len(result),
        "columns": result.columns,
        "null_counts": {col: result[col].null_count() for col in result.columns},
        "sample_data": MetadataValue.md(result.head(5).to_pandas().to_markdown()),
        "schema": MetadataValue.json(result.schema),
    })

    return result
```

### Data Quality Checks

Add asset checks:

```python
from dagster import asset_check, AssetCheckResult

@asset_check(asset=clean_customers)
def check_no_null_emails(clean_customers: pl.DataFrame) -> AssetCheckResult:
    """Ensure no null emails in cleaned data."""
    null_count = clean_customers.filter(pl.col("email").is_null()).height

    return AssetCheckResult(
        passed=null_count == 0,
        metadata={"null_email_count": null_count}
    )

@asset_check(asset=customer_metrics)
def check_positive_totals(customer_metrics: pl.DataFrame) -> AssetCheckResult:
    """Ensure all total_spent values are non-negative."""
    negative_count = customer_metrics.filter(pl.col("total_spent") < 0).height

    return AssetCheckResult(
        passed=negative_count == 0,
        metadata={"negative_total_count": negative_count}
    )
```

---

## Best Practices

### 1. Use Meaningful Asset Names

```python
# Good: Descriptive, follows naming convention
@asset(name="sales_daily_summary")
def sales_daily_summary(...): ...

# Bad: Vague, hard to understand
@asset(name="data1")
def data1(...): ...
```

### 2. Group Related Assets

```python
@asset(group_name="ingestion")
def raw_customers(...): ...

@asset(group_name="ingestion")
def raw_orders(...): ...

@asset(group_name="transformation")
def clean_customers(...): ...
```

### 3. Add Documentation

```python
@asset(
    description="""
    Customer lifetime value (CLV) calculation.

    Methodology:
    - Uses historical order data from past 12 months
    - Applies cohort-based retention rates
    - Discounts future value at 10% annually

    Output columns:
    - customer_id: Unique customer identifier
    - historical_clv: Sum of past purchases
    - predicted_clv: Expected future value
    - total_clv: historical + predicted
    """,
    metadata={
        "owner": "data-team@company.com",
        "documentation_url": "https://wiki/clv-methodology"
    }
)
def customer_clv(...): ...
```

### 4. Handle Failures Gracefully

```python
from dagster import RetryPolicy, Backoff

@asset(
    retry_policy=RetryPolicy(
        max_retries=3,
        delay=30,
        backoff=Backoff.EXPONENTIAL
    )
)
def api_data(context: AssetExecutionContext):
    """Fetch data from external API with retries."""
    try:
        return fetch_from_api()
    except RateLimitError:
        context.log.warning("Rate limited, will retry")
        raise
```

### 5. Use Incremental Processing

```python
@asset
def incremental_orders(
    context: AssetExecutionContext,
    database: DatabaseResource
) -> pl.DataFrame:
    """Incrementally load new orders."""
    # Get last processed timestamp
    last_run = context.instance.get_latest_materialization_timestamp(
        context.asset_key
    )

    if last_run:
        query = f"SELECT * FROM orders WHERE updated_at > '{last_run}'"
    else:
        query = "SELECT * FROM orders"

    return pl.read_database(query, database.connection_string)
```

---

## Related Documentation

- [Getting Started](./getting-started.md)
- [Engagement Workflow](./engagement-workflow.md)
- [Ontology Design](./ontology-design.md)
- [Agent Canvas](./agent-canvas.md)
- [Scaling Guide](../runbooks/scaling.md)
