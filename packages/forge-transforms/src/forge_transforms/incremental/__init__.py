"""
Forge Transforms Incremental Module

Provides incremental processing capabilities with state checkpointing
for efficient processing of streaming or append-only data.
"""

from forge_transforms.incremental.engine import (
    IncrementalProcessor,
    IncrementalConfig,
    ProcessingMode,
    WatermarkStrategy,
)
from forge_transforms.incremental.checkpoints import (
    Checkpoint,
    CheckpointStore,
    FileCheckpointStore,
    MemoryCheckpointStore,
    CheckpointMetadata,
)

__all__ = [
    # Engine
    "IncrementalProcessor",
    "IncrementalConfig",
    "ProcessingMode",
    "WatermarkStrategy",
    # Checkpoints
    "Checkpoint",
    "CheckpointStore",
    "FileCheckpointStore",
    "MemoryCheckpointStore",
    "CheckpointMetadata",
]
