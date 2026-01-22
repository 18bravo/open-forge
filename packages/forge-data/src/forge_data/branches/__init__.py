"""
Forge Data Branches Module

Provides Git-like dataset versioning with branching, merging,
and conflict resolution. Supports Iceberg and Delta Lake storage backends.
"""

from forge_data.branches.branch import (
    Branch,
    BranchManager,
    BranchStatus,
    Commit,
)
from forge_data.branches.merge import (
    ConflictResolution,
    MergeConflict,
    MergeResult,
    MergeStrategy,
)
from forge_data.branches.storage import (
    StorageBackend,
    IcebergBackend,
    DeltaBackend,
)

__all__ = [
    # Branching
    "Branch",
    "BranchManager",
    "BranchStatus",
    "Commit",
    # Merging
    "MergeStrategy",
    "MergeConflict",
    "MergeResult",
    "ConflictResolution",
    # Storage backends
    "StorageBackend",
    "IcebergBackend",
    "DeltaBackend",
]
