"""
Forge Data - Unified Data Governance Package

This package provides comprehensive data governance capabilities for the
Open Forge platform, consolidating what was previously 5 separate packages:

1. **quality/** - Data health checks (freshness, completeness, schema),
   monitors, and alerting
2. **lineage/** - Lineage graph with bounded traversal limits, automatic
   capture, and impact analysis
3. **branches/** - Git-like dataset branching with merge and conflict
   resolution, Iceberg/Delta storage backends
4. **catalog/** - Data catalog (Navigator) with metadata search and discovery

## Key Features

### Bounded Lineage Queries (P2 Finding Fix)
The lineage module implements bounded query limits to prevent unbounded
graph traversal:
- MAX_DEPTH = 10 (default)
- MAX_NODES = 1000 (default)
- TIMEOUT = 30 seconds (default)

### Extensible Quality Checks
The QualityCheck ABC provides a base for implementing custom checks:

```python
from forge_data.quality import QualityCheck, CheckResult

class MyCustomCheck(QualityCheck):
    @property
    def check_type(self) -> str:
        return "my_custom_check"

    async def execute(self, data_context) -> CheckResult:
        # Implement check logic
        return self._result(passed=True, message="Check passed")
```

### Dataset Versioning
Git-like branching for datasets with Iceberg or Delta Lake backends:

```python
from forge_data.branches import BranchManager, IcebergBackend

manager = BranchManager(backend=IcebergBackend(catalog))
branch = await manager.create_branch(
    dataset_id="my_dataset",
    name="feature/new-schema"
)
```

## Architecture Notes

This package is part of the consolidated Open Forge architecture that
reduced 64 packages to 20. It replaces:
- forge-quality
- forge-lineage
- forge-branches
- forge-navigator
- forge-federation

See docs/plans/2026-01-21-consolidated-architecture.md for details.
"""

__version__ = "0.1.0"

# Quality module exports
from forge_data.quality import (
    QualityCheck,
    CheckResult,
    CheckSeverity,
    FreshnessCheck,
    CompletenessCheck,
    SchemaCheck,
    QualityMonitor,
    MonitorSchedule,
    AlertChannel,
    AlertConfig,
    AlertDispatcher,
)

# Lineage module exports (with bounded limits - P2 fix)
from forge_data.lineage import (
    LineageGraph,
    LineageNode,
    LineageEdge,
    NodeType,
    EdgeType,
    LineageQuery,
    LineageQueryResult,
    LineageTracker,
    ImpactAnalyzer,
    ImpactReport,
)

# Branches module exports
from forge_data.branches import (
    Branch,
    BranchManager,
    BranchStatus,
    Commit,
    MergeStrategy,
    MergeConflict,
    MergeResult,
    ConflictResolution,
    StorageBackend,
    IcebergBackend,
    DeltaBackend,
)

# Catalog module exports
from forge_data.catalog import (
    CatalogNavigator,
    CatalogEntry,
    DataAsset,
    AssetType,
    CatalogSearch,
    SearchResult,
    SearchFilter,
)

__all__ = [
    # Version
    "__version__",
    # Quality
    "QualityCheck",
    "CheckResult",
    "CheckSeverity",
    "FreshnessCheck",
    "CompletenessCheck",
    "SchemaCheck",
    "QualityMonitor",
    "MonitorSchedule",
    "AlertChannel",
    "AlertConfig",
    "AlertDispatcher",
    # Lineage
    "LineageGraph",
    "LineageNode",
    "LineageEdge",
    "NodeType",
    "EdgeType",
    "LineageQuery",
    "LineageQueryResult",
    "LineageTracker",
    "ImpactAnalyzer",
    "ImpactReport",
    # Branches
    "Branch",
    "BranchManager",
    "BranchStatus",
    "Commit",
    "MergeStrategy",
    "MergeConflict",
    "MergeResult",
    "ConflictResolution",
    "StorageBackend",
    "IcebergBackend",
    "DeltaBackend",
    # Catalog
    "CatalogNavigator",
    "CatalogEntry",
    "DataAsset",
    "AssetType",
    "CatalogSearch",
    "SearchResult",
    "SearchFilter",
]
