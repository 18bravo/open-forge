"""
Event-driven sensors for Open Forge.

Monitors Redis event streams to trigger downstream pipelines.
"""
from typing import Dict, List, Optional
from dagster import (
    sensor,
    SensorEvaluationContext,
    RunRequest,
    SkipReason,
    DefaultSensorStatus,
)
import json
from datetime import datetime


@sensor(
    name="data_staged_sensor",
    description="Triggers transformation when data is staged",
    minimum_interval_seconds=30,
    default_status=DefaultSensorStatus.RUNNING,
)
def data_staged_sensor(
    context: SensorEvaluationContext,
) -> None:
    """Sensor that triggers transformation after data staging.

    Listens to the 'data.staged' event stream in Redis and
    triggers transformation jobs for newly staged datasets.

    Uses Redis consumer groups to ensure exactly-once processing.
    """
    import asyncio
    from redis.asyncio import Redis

    from core.config import get_settings

    settings = get_settings()

    # Consumer group configuration
    consumer_group = "dagster_transformation_trigger"
    consumer_name = f"sensor_{context.sensor_name}"
    stream_name = "events:data"

    async def check_events():
        """Async function to check Redis for staged events."""
        redis = Redis.from_url(
            settings.redis.connection_string,
            decode_responses=True
        )

        try:
            # Create consumer group if it doesn't exist
            try:
                await redis.xgroup_create(stream_name, consumer_group, mkstream=True)
            except Exception:
                pass  # Group already exists

            # Read pending messages for this consumer
            messages = await redis.xreadgroup(
                consumer_group,
                consumer_name,
                {stream_name: ">"},
                count=10,
                block=1000,  # 1 second timeout
            )

            events = []
            if messages:
                for stream, stream_messages in messages:
                    for message_id, data in stream_messages:
                        try:
                            event_data = json.loads(data.get("data", "{}"))
                            if event_data.get("event_type") == "data.staged":
                                events.append({
                                    "message_id": message_id,
                                    "payload": event_data.get("payload", {}),
                                })
                                # Acknowledge message
                                await redis.xack(stream_name, consumer_group, message_id)
                        except json.JSONDecodeError:
                            context.log.warning(f"Invalid JSON in message {message_id}")

            return events

        finally:
            await redis.close()

    # Run async check
    try:
        events = asyncio.run(check_events())
    except Exception as e:
        context.log.error(f"Error checking events: {e}")
        yield SkipReason(f"Error: {e}")
        return

    if not events:
        yield SkipReason("No staged data events")
        return

    context.log.info(f"Found {len(events)} staged data events")

    for event in events:
        payload = event["payload"]
        source_id = payload.get("source_id")
        source_name = payload.get("source_name", source_id)

        if not source_id:
            continue

        # Build transformation job config
        run_config = {
            "ops": {
                "load_staged_data": {
                    "config": {
                        "dataset_id": source_id,
                        "dataset_name": source_name,
                        "source_namespace": "staged",
                        "source_tables": [f"staged_{source_id}"],
                    }
                },
                "clean_data": {
                    "config": {
                        "dataset_id": source_id,
                        "dataset_name": source_name,
                    }
                },
                "enrich_data": {
                    "config": {
                        "dataset_id": source_id,
                        "dataset_name": source_name,
                    }
                },
                "aggregate_data": {
                    "config": {
                        "dataset_id": source_id,
                        "dataset_name": source_name,
                    }
                },
                "write_curated_data": {
                    "config": {
                        "dataset_id": source_id,
                        "dataset_name": source_name,
                    }
                },
            }
        }

        yield RunRequest(
            run_key=f"transform_{source_id}_{event['message_id']}",
            run_config=run_config,
            tags={
                "dataset_id": source_id,
                "triggered_by": "data_staged_sensor",
                "event_id": event["message_id"],
            },
        )


@sensor(
    name="pipeline_completion_sensor",
    description="Monitors pipeline completions for chained workflows",
    minimum_interval_seconds=30,
    default_status=DefaultSensorStatus.STOPPED,
)
def pipeline_completion_sensor(
    context: SensorEvaluationContext,
) -> None:
    """Sensor that triggers downstream jobs on pipeline completion.

    Monitors pipeline completion events and triggers subsequent
    stages in multi-phase workflows.

    Workflow chains:
    - ingestion complete -> transformation
    - transformation complete -> ontology refresh
    - ontology complete -> notification
    """
    import asyncio
    from redis.asyncio import Redis

    from core.config import get_settings

    settings = get_settings()

    # Define workflow chains
    workflow_chains = {
        "data.curated": {
            "next_job": "ontology_refresh",
            "trigger_on": ["dataset_id"],
        },
        "ontology.compiled": {
            "next_job": None,  # End of chain, could trigger notification
            "trigger_on": ["ontology_id"],
        },
    }

    consumer_group = "dagster_workflow_chain"
    consumer_name = f"sensor_{context.sensor_name}"

    async def check_completion_events():
        """Check for pipeline completion events."""
        redis = Redis.from_url(
            settings.redis.connection_string,
            decode_responses=True
        )

        try:
            events = []

            for event_type in workflow_chains.keys():
                stream_name = f"events:{event_type.split('.')[0]}"

                try:
                    await redis.xgroup_create(stream_name, consumer_group, mkstream=True)
                except Exception:
                    pass

                messages = await redis.xreadgroup(
                    consumer_group,
                    consumer_name,
                    {stream_name: ">"},
                    count=10,
                    block=500,
                )

                if messages:
                    for stream, stream_messages in messages:
                        for message_id, data in stream_messages:
                            try:
                                event_data = json.loads(data.get("data", "{}"))
                                if event_data.get("event_type") in workflow_chains:
                                    events.append({
                                        "message_id": message_id,
                                        "stream": stream,
                                        "event_type": event_data.get("event_type"),
                                        "payload": event_data.get("payload", {}),
                                    })
                                    await redis.xack(stream_name, consumer_group, message_id)
                            except json.JSONDecodeError:
                                pass

            return events

        finally:
            await redis.close()

    try:
        events = asyncio.run(check_completion_events())
    except Exception as e:
        context.log.error(f"Error checking completion events: {e}")
        yield SkipReason(f"Error: {e}")
        return

    if not events:
        yield SkipReason("No completion events")
        return

    context.log.info(f"Found {len(events)} completion events")

    for event in events:
        chain_config = workflow_chains.get(event["event_type"])
        if not chain_config or not chain_config["next_job"]:
            continue

        payload = event["payload"]
        next_job = chain_config["next_job"]

        # Build trigger key from payload
        trigger_keys = {
            key: payload.get(key)
            for key in chain_config["trigger_on"]
            if key in payload
        }

        if not trigger_keys:
            continue

        # Build appropriate run config based on next job
        run_config = {}

        if next_job == "ontology_refresh":
            # Trigger ontology compilation after data curation
            run_config = {
                "ops": {
                    "ontology_definitions": {
                        "config": {
                            "ontology_id": "default",
                            "ontology_name": "Default Ontology",
                        }
                    },
                    "compiled_ontology": {
                        "config": {
                            "ontology_id": "default",
                            "ontology_name": "Default Ontology",
                        }
                    },
                    "ontology_validation_report": {
                        "config": {
                            "ontology_id": "default",
                            "ontology_name": "Default Ontology",
                        }
                    },
                }
            }

        yield RunRequest(
            run_key=f"{next_job}_{event['message_id']}",
            run_config=run_config,
            tags={
                "triggered_by": "pipeline_completion_sensor",
                "previous_event": event["event_type"],
                **{f"trigger_{k}": v for k, v in trigger_keys.items()},
            },
        )


@sensor(
    name="external_event_sensor",
    description="Handles external webhook events",
    minimum_interval_seconds=10,
    default_status=DefaultSensorStatus.STOPPED,
)
def external_event_sensor(
    context: SensorEvaluationContext,
) -> None:
    """Sensor that processes external webhook events.

    Monitors a Redis queue for webhook payloads posted by the
    API layer. Supports various external triggers:
    - Manual ingestion requests
    - Scheduled refresh triggers
    - Data quality alerts
    """
    import asyncio
    from redis.asyncio import Redis

    from core.config import get_settings

    settings = get_settings()

    queue_name = "dagster:webhooks"

    async def check_webhooks():
        """Check for webhook events in Redis queue."""
        redis = Redis.from_url(
            settings.redis.connection_string,
            decode_responses=True
        )

        try:
            events = []

            # Get up to 10 webhook events from queue
            for _ in range(10):
                result = await redis.lpop(queue_name)
                if not result:
                    break

                try:
                    event = json.loads(result)
                    events.append(event)
                except json.JSONDecodeError:
                    context.log.warning(f"Invalid webhook payload: {result}")

            return events

        finally:
            await redis.close()

    try:
        events = asyncio.run(check_webhooks())
    except Exception as e:
        context.log.error(f"Error checking webhooks: {e}")
        yield SkipReason(f"Error: {e}")
        return

    if not events:
        yield SkipReason("No webhook events")
        return

    context.log.info(f"Processing {len(events)} webhook events")

    for event in events:
        event_type = event.get("type")
        payload = event.get("payload", {})
        event_id = event.get("id", datetime.now().timestamp())

        run_config = None
        job_name = None

        if event_type == "ingest_request":
            # Manual ingestion request
            job_name = "ingestion_job"
            source_config = payload.get("source", {})

            run_config = {
                "ops": {
                    "load_source_data": {
                        "config": {
                            "source_id": source_config.get("source_id", "manual"),
                            "source_type": source_config.get("type", "file"),
                            "source_name": source_config.get("name", "Manual Upload"),
                            "file_path": source_config.get("file_path"),
                            "file_format": source_config.get("file_format"),
                        }
                    },
                    "validate_data": {
                        "config": {
                            "source_id": source_config.get("source_id", "manual"),
                            "source_type": source_config.get("type", "file"),
                            "source_name": source_config.get("name", "Manual Upload"),
                        }
                    },
                    "stage_data": {
                        "config": {
                            "source_id": source_config.get("source_id", "manual"),
                            "source_type": source_config.get("type", "file"),
                            "source_name": source_config.get("name", "Manual Upload"),
                        }
                    },
                }
            }

        elif event_type == "refresh_dataset":
            # Dataset refresh request
            job_name = "transformation_job"
            dataset_id = payload.get("dataset_id")

            if dataset_id:
                run_config = {
                    "ops": {
                        "load_staged_data": {
                            "config": {
                                "dataset_id": dataset_id,
                                "dataset_name": payload.get("dataset_name", dataset_id),
                                "source_namespace": "staged",
                                "source_tables": [f"staged_{dataset_id}"],
                            }
                        },
                        "clean_data": {
                            "config": {
                                "dataset_id": dataset_id,
                                "dataset_name": payload.get("dataset_name", dataset_id),
                            }
                        },
                        "enrich_data": {
                            "config": {
                                "dataset_id": dataset_id,
                                "dataset_name": payload.get("dataset_name", dataset_id),
                            }
                        },
                        "aggregate_data": {
                            "config": {
                                "dataset_id": dataset_id,
                                "dataset_name": payload.get("dataset_name", dataset_id),
                            }
                        },
                        "write_curated_data": {
                            "config": {
                                "dataset_id": dataset_id,
                                "dataset_name": payload.get("dataset_name", dataset_id),
                            }
                        },
                    }
                }

        elif event_type == "refresh_ontology":
            # Ontology refresh request
            job_name = "ontology_job"
            ontology_id = payload.get("ontology_id", "default")

            run_config = {
                "ops": {
                    "ontology_definitions": {
                        "config": {
                            "ontology_id": ontology_id,
                            "ontology_name": payload.get("ontology_name", "Default"),
                        }
                    },
                    "compiled_ontology": {
                        "config": {
                            "ontology_id": ontology_id,
                            "ontology_name": payload.get("ontology_name", "Default"),
                        }
                    },
                    "ontology_validation_report": {
                        "config": {
                            "ontology_id": ontology_id,
                            "ontology_name": payload.get("ontology_name", "Default"),
                        }
                    },
                }
            }

        if run_config and job_name:
            yield RunRequest(
                run_key=f"webhook_{event_type}_{event_id}",
                run_config=run_config,
                tags={
                    "triggered_by": "external_event_sensor",
                    "event_type": event_type,
                    "webhook_id": str(event_id),
                },
            )
