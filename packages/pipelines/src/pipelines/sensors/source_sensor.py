"""
Source detection sensors for Open Forge.

Monitors for new data sources and triggers ingestion pipelines.
"""
from typing import Optional
from dagster import (
    sensor,
    SensorEvaluationContext,
    RunRequest,
    SkipReason,
    SensorDefinition,
    DefaultSensorStatus,
    RunConfig,
)
import json
import os
from datetime import datetime

from pipelines.resources import DatabaseResource


@sensor(
    name="new_source_sensor",
    description="Detects newly configured data sources and triggers ingestion",
    minimum_interval_seconds=60,
    default_status=DefaultSensorStatus.RUNNING,
)
def new_source_sensor(
    context: SensorEvaluationContext,
) -> None:
    """Sensor that monitors for new data source configurations.

    Checks the database for newly added sources that have not
    been processed yet. When found, triggers the ingestion job.

    The cursor tracks the last processed source timestamp to
    avoid reprocessing.
    """
    from sqlalchemy import create_engine, text

    from core.config import get_settings

    settings = get_settings()

    # Get cursor (last processed timestamp)
    cursor = context.cursor
    last_processed = cursor if cursor else "1970-01-01T00:00:00"

    try:
        engine = create_engine(settings.database.connection_string)

        with engine.connect() as conn:
            # Query for new sources since last check
            result = conn.execute(
                text("""
                    SELECT
                        source_id,
                        source_type,
                        source_name,
                        config_json,
                        created_at
                    FROM data_sources
                    WHERE is_active = true
                        AND created_at > :last_processed
                    ORDER BY created_at ASC
                    LIMIT 10
                """),
                {"last_processed": last_processed}
            )

            rows = result.fetchall()

            if not rows:
                yield SkipReason(f"No new sources since {last_processed}")
                return

            context.log.info(f"Found {len(rows)} new sources")

            # Track latest timestamp for cursor update
            latest_timestamp = last_processed

            for row in rows:
                source_id = row.source_id
                source_type = row.source_type
                source_name = row.source_name
                config_json = row.config_json
                created_at = row.created_at

                # Parse source configuration
                try:
                    source_config = json.loads(config_json) if config_json else {}
                except json.JSONDecodeError:
                    source_config = {}

                # Build run config based on source type
                run_config = {
                    "ops": {
                        "load_source_data": {
                            "config": {
                                "source_id": source_id,
                                "source_type": source_type,
                                "source_name": source_name,
                                "namespace": source_config.get("namespace", "raw"),
                            }
                        },
                        "validate_data": {
                            "config": {
                                "source_id": source_id,
                                "source_type": source_type,
                                "source_name": source_name,
                            }
                        },
                        "stage_data": {
                            "config": {
                                "source_id": source_id,
                                "source_type": source_type,
                                "source_name": source_name,
                            }
                        },
                    }
                }

                # Add source-specific config
                if source_type == "file":
                    run_config["ops"]["load_source_data"]["config"].update({
                        "file_path": source_config.get("file_path"),
                        "file_format": source_config.get("file_format"),
                    })
                elif source_type == "database":
                    run_config["ops"]["load_source_data"]["config"].update({
                        "query": source_config.get("query"),
                        "connection_string": source_config.get("connection_string"),
                    })
                elif source_type == "api":
                    run_config["ops"]["load_source_data"]["config"].update({
                        "api_url": source_config.get("api_url"),
                    })

                yield RunRequest(
                    run_key=f"source_{source_id}_{created_at.isoformat()}",
                    run_config=run_config,
                    tags={
                        "source_id": source_id,
                        "source_type": source_type,
                        "triggered_by": "new_source_sensor",
                    },
                )

                # Update latest timestamp
                if isinstance(created_at, datetime):
                    latest_timestamp = created_at.isoformat()
                else:
                    latest_timestamp = str(created_at)

            # Update cursor
            context.update_cursor(latest_timestamp)

    except Exception as e:
        context.log.error(f"Error checking for new sources: {e}")
        yield SkipReason(f"Error: {e}")


@sensor(
    name="file_arrival_sensor",
    description="Detects new files in monitored directories",
    minimum_interval_seconds=30,
    default_status=DefaultSensorStatus.STOPPED,
)
def file_arrival_sensor(
    context: SensorEvaluationContext,
) -> None:
    """Sensor that monitors directories for new files.

    Watches configured directories for new CSV, Parquet, or JSON
    files and triggers ingestion when files arrive.

    Uses file modification time to detect new files.
    """
    # Configure watched directories (in production, this would come from config)
    watched_dirs = [
        "/data/incoming",
        "/data/uploads",
    ]

    supported_extensions = {".csv", ".parquet", ".json", ".ndjson"}

    # Get cursor (dict of file -> mtime)
    cursor = context.cursor
    try:
        processed_files = json.loads(cursor) if cursor else {}
    except json.JSONDecodeError:
        processed_files = {}

    new_files = []

    for watched_dir in watched_dirs:
        if not os.path.isdir(watched_dir):
            continue

        try:
            for filename in os.listdir(watched_dir):
                file_path = os.path.join(watched_dir, filename)

                # Skip directories
                if os.path.isdir(file_path):
                    continue

                # Check extension
                _, ext = os.path.splitext(filename)
                if ext.lower() not in supported_extensions:
                    continue

                # Get modification time
                mtime = os.path.getmtime(file_path)

                # Check if new or modified
                if file_path not in processed_files or processed_files[file_path] < mtime:
                    new_files.append({
                        "path": file_path,
                        "filename": filename,
                        "extension": ext.lower(),
                        "mtime": mtime,
                        "directory": watched_dir,
                    })
                    processed_files[file_path] = mtime

        except Exception as e:
            context.log.warning(f"Error scanning {watched_dir}: {e}")

    if not new_files:
        yield SkipReason("No new files detected")
        return

    context.log.info(f"Found {len(new_files)} new files")

    # Infer file format from extension
    format_map = {
        ".csv": "csv",
        ".parquet": "parquet",
        ".json": "json",
        ".ndjson": "ndjson",
    }

    for file_info in new_files:
        # Generate source ID from filename
        source_id = os.path.splitext(file_info["filename"])[0]
        source_id = source_id.replace(" ", "_").replace("-", "_").lower()

        file_format = format_map.get(file_info["extension"], "csv")

        run_config = {
            "ops": {
                "load_source_data": {
                    "config": {
                        "source_id": source_id,
                        "source_type": "file",
                        "source_name": file_info["filename"],
                        "file_path": file_info["path"],
                        "file_format": file_format,
                    }
                },
                "validate_data": {
                    "config": {
                        "source_id": source_id,
                        "source_type": "file",
                        "source_name": file_info["filename"],
                    }
                },
                "stage_data": {
                    "config": {
                        "source_id": source_id,
                        "source_type": "file",
                        "source_name": file_info["filename"],
                    }
                },
            }
        }

        yield RunRequest(
            run_key=f"file_{source_id}_{file_info['mtime']}",
            run_config=run_config,
            tags={
                "source_id": source_id,
                "source_type": "file",
                "file_path": file_info["path"],
                "triggered_by": "file_arrival_sensor",
            },
        )

    # Update cursor
    context.update_cursor(json.dumps(processed_files))


@sensor(
    name="source_health_sensor",
    description="Monitors data source health and connectivity",
    minimum_interval_seconds=300,  # 5 minutes
    default_status=DefaultSensorStatus.STOPPED,
)
def source_health_sensor(
    context: SensorEvaluationContext,
) -> None:
    """Sensor that monitors data source health.

    Periodically checks connectivity to configured data sources
    and logs warnings for unhealthy sources. Does not trigger
    jobs but maintains health status in metadata.
    """
    from sqlalchemy import create_engine, text

    from core.config import get_settings

    settings = get_settings()

    health_status = {}

    try:
        engine = create_engine(settings.database.connection_string)

        with engine.connect() as conn:
            # Get all active sources
            result = conn.execute(
                text("""
                    SELECT source_id, source_type, source_name, config_json
                    FROM data_sources
                    WHERE is_active = true
                """)
            )

            for row in result:
                source_id = row.source_id
                source_type = row.source_type
                config_json = row.config_json

                try:
                    config = json.loads(config_json) if config_json else {}
                except json.JSONDecodeError:
                    config = {}

                # Check health based on source type
                is_healthy = True
                error_message = None

                if source_type == "file":
                    file_path = config.get("file_path")
                    if file_path and not os.path.exists(file_path):
                        is_healthy = False
                        error_message = f"File not found: {file_path}"

                elif source_type == "database":
                    conn_string = config.get("connection_string")
                    if conn_string:
                        try:
                            test_engine = create_engine(conn_string)
                            with test_engine.connect() as test_conn:
                                test_conn.execute(text("SELECT 1"))
                        except Exception as e:
                            is_healthy = False
                            error_message = f"Database connection failed: {e}"

                elif source_type == "api":
                    api_url = config.get("api_url")
                    if api_url:
                        import httpx
                        try:
                            response = httpx.head(api_url, timeout=10.0)
                            if response.status_code >= 400:
                                is_healthy = False
                                error_message = f"API returned {response.status_code}"
                        except Exception as e:
                            is_healthy = False
                            error_message = f"API unreachable: {e}"

                health_status[source_id] = {
                    "healthy": is_healthy,
                    "error": error_message,
                    "checked_at": datetime.now().isoformat(),
                }

                if not is_healthy:
                    context.log.warning(f"Source {source_id} unhealthy: {error_message}")

    except Exception as e:
        context.log.error(f"Error checking source health: {e}")

    # Store health status in cursor for reference
    context.update_cursor(json.dumps(health_status))

    # This sensor doesn't trigger jobs, just monitors
    healthy_count = sum(1 for s in health_status.values() if s["healthy"])
    total_count = len(health_status)

    yield SkipReason(f"Health check complete: {healthy_count}/{total_count} sources healthy")
