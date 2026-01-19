"""
Open Forge Pipelines Package

Dagster-based data processing pipelines for Open Forge.
Provides data ingestion, transformation, and ontology compilation
capabilities using Apache Iceberg for storage and Polars for processing.

Usage:
    # In dagster.yaml or workspace.yaml
    load_from:
      - python_module: pipelines.definitions

    # Or programmatically
    from pipelines.definitions import defs
"""

__version__ = "0.1.0"

# Resources
from pipelines.resources import (
    DatabaseResource,
    IcebergResource,
    EventBusResource,
)

# IO Managers
from pipelines.io_managers import (
    IcebergIOManager,
    PolarsIOManager,
    PartitionedIcebergIOManager,
)

# Definitions
from pipelines.definitions import (
    defs,
    get_definitions,
    get_dev_definitions,
    get_test_definitions,
)

__all__ = [
    # Version
    "__version__",
    # Resources
    "DatabaseResource",
    "IcebergResource",
    "EventBusResource",
    # IO Managers
    "IcebergIOManager",
    "PolarsIOManager",
    "PartitionedIcebergIOManager",
    # Definitions
    "defs",
    "get_definitions",
    "get_dev_definitions",
    "get_test_definitions",
]
