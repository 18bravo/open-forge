"""
Dagster Definitions for Open Forge Pipelines.

Central definition object that registers all assets, jobs,
sensors, schedules, and resources with Dagster.
"""
from dagster import (
    Definitions,
    EnvVar,
    load_assets_from_modules,
)

# Import resources
from pipelines.resources import (
    DatabaseResource,
    IcebergResource,
    EventBusResource,
)

# Import IO managers
from pipelines.io_managers import (
    IcebergIOManager,
    PolarsIOManager,
    PartitionedIcebergIOManager,
)

# Import assets
from pipelines.assets import ingestion, transformation, ontology

# Import jobs
from pipelines.jobs.ingestion_job import (
    ingestion_job,
    full_ingestion_job,
    hourly_ingestion_schedule,
    daily_full_ingestion_schedule,
)
from pipelines.jobs.transformation_job import (
    transformation_job,
    full_transformation_job,
    hourly_transformation_schedule,
    daily_full_transformation_schedule,
)

# Import sensors
from pipelines.sensors.source_sensor import (
    new_source_sensor,
    file_arrival_sensor,
)
from pipelines.sensors.event_sensor import (
    data_staged_sensor,
    pipeline_completion_sensor,
    external_event_sensor,
)

# Load all assets from modules
ingestion_assets = load_assets_from_modules([ingestion])
transformation_assets = load_assets_from_modules([transformation])
ontology_assets = load_assets_from_modules([ontology])

all_assets = [
    *ingestion_assets,
    *transformation_assets,
    *ontology_assets,
]

# Define all jobs
all_jobs = [
    ingestion_job,
    full_ingestion_job,
    transformation_job,
    full_transformation_job,
]

# Define all schedules
all_schedules = [
    hourly_ingestion_schedule,
    daily_full_ingestion_schedule,
    hourly_transformation_schedule,
    daily_full_transformation_schedule,
]

# Define all sensors
all_sensors = [
    new_source_sensor,
    file_arrival_sensor,
    data_staged_sensor,
    pipeline_completion_sensor,
    external_event_sensor,
]

# Resource configuration with environment variable support
resource_defs = {
    # Database resource
    "database": DatabaseResource(
        host=EnvVar("DB_HOST").get_value() or "localhost",
        port=int(EnvVar("DB_PORT").get_value() or "5432"),
        user=EnvVar("DB_USER").get_value() or "foundry",
        password=EnvVar("DB_PASSWORD").get_value() or "foundry_dev",
        database=EnvVar("DB_NAME").get_value() or "foundry",
    ),
    # Iceberg resource
    "iceberg": IcebergResource(
        catalog_uri=EnvVar("ICEBERG_CATALOG_URI").get_value() or "http://localhost:8181",
        warehouse_path=EnvVar("ICEBERG_WAREHOUSE").get_value() or "s3://foundry-lake/warehouse",
        s3_endpoint=EnvVar("S3_ENDPOINT").get_value() or "http://localhost:9000",
        s3_access_key=EnvVar("S3_ACCESS_KEY").get_value() or "minio",
        s3_secret_key=EnvVar("S3_SECRET_KEY").get_value() or "minio123",
    ),
    # Event bus resource
    "event_bus": EventBusResource(
        host=EnvVar("REDIS_HOST").get_value() or "localhost",
        port=int(EnvVar("REDIS_PORT").get_value() or "6379"),
        password=EnvVar("REDIS_PASSWORD").get_value(),
    ),
    # IO Managers
    "iceberg_io_manager": IcebergIOManager(
        namespace="raw",
        write_mode="append",
    ),
    "polars_io_manager": PolarsIOManager(
        cache_dir="/tmp/dagster_polars_cache",
        cache_threshold_mb=100,
    ),
    "partitioned_iceberg_io_manager": PartitionedIcebergIOManager(
        namespace="raw",
        write_mode="append",
        partition_column="_created_at",
        time_partition_format="day",
    ),
}

# Create the Definitions object
defs = Definitions(
    assets=all_assets,
    jobs=all_jobs,
    schedules=all_schedules,
    sensors=all_sensors,
    resources=resource_defs,
)


# For backwards compatibility and explicit access
def get_definitions() -> Definitions:
    """Get the Dagster Definitions object.

    Returns:
        Definitions object with all assets, jobs, schedules,
        sensors, and resources configured.
    """
    return defs


# Development/testing configuration
def get_dev_definitions() -> Definitions:
    """Get Definitions configured for local development.

    Uses localhost defaults for all services.
    """
    dev_resources = {
        "database": DatabaseResource(
            host="localhost",
            port=5432,
            user="foundry",
            password="foundry_dev",
            database="foundry",
        ),
        "iceberg": IcebergResource(
            catalog_uri="http://localhost:8181",
            warehouse_path="s3://foundry-lake/warehouse",
            s3_endpoint="http://localhost:9000",
            s3_access_key="minio",
            s3_secret_key="minio123",
        ),
        "event_bus": EventBusResource(
            host="localhost",
            port=6379,
        ),
        "iceberg_io_manager": IcebergIOManager(
            namespace="dev",
            write_mode="overwrite",
        ),
        "polars_io_manager": PolarsIOManager(),
        "partitioned_iceberg_io_manager": PartitionedIcebergIOManager(
            namespace="dev",
        ),
    }

    return Definitions(
        assets=all_assets,
        jobs=all_jobs,
        schedules=[],  # No schedules in dev
        sensors=[],    # No sensors in dev by default
        resources=dev_resources,
    )


# Test configuration with mocked resources
def get_test_definitions() -> Definitions:
    """Get Definitions configured for testing.

    Uses mock resources where possible.
    """
    from dagster import mem_io_manager

    test_resources = {
        "database": DatabaseResource(
            host="localhost",
            port=5432,
            user="test",
            password="test",
            database="test",
        ),
        "iceberg": IcebergResource(),
        "event_bus": EventBusResource(),
        "iceberg_io_manager": mem_io_manager,
        "polars_io_manager": mem_io_manager,
        "partitioned_iceberg_io_manager": mem_io_manager,
    }

    return Definitions(
        assets=all_assets,
        jobs=all_jobs,
        schedules=[],
        sensors=[],
        resources=test_resources,
    )
