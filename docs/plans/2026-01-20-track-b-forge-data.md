# Track B: Forge Data Platform Design

**Date:** 2026-01-20
**Status:** Draft
**Track:** B - Data Platform
**Dependencies:** api, pipelines, ontology

---

## Executive Summary

Track B implements the data platform layer for Open Forge, providing data quality monitoring, lineage tracking, data versioning (branches), a unified data catalog (Navigator), and federated query capabilities. This track addresses ~40+ data management features for enterprise data governance.

### Key Packages

| Package | Purpose |
|---------|---------|
| `forge-quality` | Data health monitoring & checks |
| `forge-lineage` | End-to-end data lineage |
| `forge-branches` | Git-like data versioning |
| `forge-navigator` | Data catalog & discovery |
| `forge-federation` | Cross-source virtual tables |
| `transforms-core` | Transform framework |
| `transforms-spark` | Apache Spark transforms |
| `transforms-flink` | Streaming transforms |
| `transforms-datafusion` | Fast Rust-based transforms |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FORGE DATA PLATFORM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         FORGE NAVIGATOR                              │    │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────┐    │    │
│  │  │  Catalog  │  │  Search   │  │  Discover │  │  Ownership    │    │    │
│  │  │  Browser  │  │  Engine   │  │  Engine   │  │  & Stewards   │    │    │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  FORGE QUALITY  │  │  FORGE LINEAGE  │  │     FORGE BRANCHES          │  │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────────────────┤  │
│  │  Health Checks  │  │  Column-Level   │  │  Git-like Versioning        │  │
│  │  SLA Monitors   │  │  Impact Analysis│  │  Merge/Conflict Resolution  │  │
│  │  Anomaly Detect │  │  Dependency Map │  │  Time Travel Queries        │  │
│  │  Auto-Remediate │  │  Propagation    │  │  Branch Comparison          │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       TRANSFORMS ENGINE                                │  │
│  │  ┌──────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │  │
│  │  │ Core Engine  │  │   Spark    │  │   Flink    │  │  DataFusion  │  │  │
│  │  │ (Orchestrate)│  │  (Batch)   │  │ (Stream)   │  │  (Fast SQL)  │  │  │
│  │  └──────────────┘  └────────────┘  └────────────┘  └──────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       FORGE FEDERATION                                 │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │  Virtual    │  │   Query     │  │   Schema    │  │   Cache     │  │  │
│  │  │  Tables     │  │   Pushdown  │  │   Mapping   │  │   Layer     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Package 1: Forge Quality

### Purpose

Automated data quality monitoring with configurable health checks, SLA enforcement, anomaly detection, and automated remediation workflows.

### Module Structure

```
packages/forge-quality/
├── src/
│   └── forge_quality/
│       ├── __init__.py
│       ├── checks/
│       │   ├── __init__.py
│       │   ├── base.py            # BaseCheck abstract class
│       │   ├── freshness.py       # Data freshness checks
│       │   ├── completeness.py    # Null/missing value checks
│       │   ├── schema.py          # Schema validation
│       │   ├── volume.py          # Row count thresholds
│       │   ├── uniqueness.py      # Duplicate detection
│       │   ├── referential.py     # Foreign key validation
│       │   ├── statistical.py     # Distribution checks
│       │   └── custom.py          # User-defined checks
│       ├── monitors/
│       │   ├── __init__.py
│       │   ├── monitor.py         # Monitor definitions
│       │   ├── schedule.py        # Cron-based scheduling
│       │   ├── runner.py          # Check execution engine
│       │   └── alerting.py        # Alert dispatch
│       ├── anomaly/
│       │   ├── __init__.py
│       │   ├── detector.py        # Anomaly detection
│       │   ├── statistical.py     # Statistical methods
│       │   └── ml.py              # ML-based detection
│       ├── remediation/
│       │   ├── __init__.py
│       │   ├── actions.py         # Remediation actions
│       │   ├── workflows.py       # Auto-fix workflows
│       │   └── issue_tracker.py   # Issue management
│       ├── models/
│       │   ├── __init__.py
│       │   ├── check.py           # Check result models
│       │   ├── monitor.py         # Monitor models
│       │   └── alert.py           # Alert models
│       └── api/
│           ├── __init__.py
│           └── routes.py          # FastAPI routes
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# checks/base.py
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from typing import Any
from pydantic import BaseModel

class CheckSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class CheckResult(BaseModel):
    check_id: str
    check_type: str
    dataset_id: str
    passed: bool
    severity: CheckSeverity
    message: str
    details: dict[str, Any] | None = None
    executed_at: datetime
    execution_ms: int

class BaseCheck(ABC):
    """Abstract base class for all quality checks."""

    def __init__(
        self,
        check_id: str,
        dataset_id: str,
        severity: CheckSeverity = CheckSeverity.ERROR,
        config: dict[str, Any] | None = None
    ):
        self.check_id = check_id
        self.dataset_id = dataset_id
        self.severity = severity
        self.config = config or {}

    @property
    @abstractmethod
    def check_type(self) -> str:
        """Return the check type identifier."""
        pass

    @abstractmethod
    async def execute(self, data_context: "DataContext") -> CheckResult:
        """Execute the check and return results."""
        pass

    def _result(self, passed: bool, message: str, details: dict | None = None) -> CheckResult:
        return CheckResult(
            check_id=self.check_id,
            check_type=self.check_type,
            dataset_id=self.dataset_id,
            passed=passed,
            severity=self.severity,
            message=message,
            details=details,
            executed_at=datetime.utcnow(),
            execution_ms=0  # Set by runner
        )
```

```python
# checks/freshness.py
from datetime import datetime, timedelta
from .base import BaseCheck, CheckResult, CheckSeverity

class FreshnessCheck(BaseCheck):
    """Check that data has been updated within expected timeframe."""

    @property
    def check_type(self) -> str:
        return "freshness"

    async def execute(self, data_context: "DataContext") -> CheckResult:
        max_age_hours = self.config.get("max_age_hours", 24)
        timestamp_column = self.config.get("timestamp_column", "updated_at")

        # Get latest timestamp from dataset
        latest = await data_context.get_max_timestamp(
            self.dataset_id,
            timestamp_column
        )

        if latest is None:
            return self._result(
                passed=False,
                message=f"No timestamps found in column '{timestamp_column}'",
                details={"timestamp_column": timestamp_column}
            )

        age = datetime.utcnow() - latest
        max_age = timedelta(hours=max_age_hours)
        passed = age <= max_age

        return self._result(
            passed=passed,
            message=f"Data age: {age}. Max allowed: {max_age}",
            details={
                "latest_timestamp": latest.isoformat(),
                "age_hours": age.total_seconds() / 3600,
                "max_age_hours": max_age_hours
            }
        )
```

```python
# checks/completeness.py
class CompletenessCheck(BaseCheck):
    """Check for null/missing values in specified columns."""

    @property
    def check_type(self) -> str:
        return "completeness"

    async def execute(self, data_context: "DataContext") -> CheckResult:
        columns = self.config.get("columns", [])
        max_null_pct = self.config.get("max_null_percentage", 0.0)

        stats = await data_context.get_null_stats(self.dataset_id, columns)

        failed_columns = []
        for col, null_pct in stats.items():
            if null_pct > max_null_pct:
                failed_columns.append({
                    "column": col,
                    "null_percentage": null_pct,
                    "threshold": max_null_pct
                })

        passed = len(failed_columns) == 0

        return self._result(
            passed=passed,
            message=f"Completeness check: {len(failed_columns)} columns exceed null threshold",
            details={
                "column_stats": stats,
                "failed_columns": failed_columns,
                "threshold": max_null_pct
            }
        )
```

```python
# checks/statistical.py
import numpy as np
from scipy import stats as scipy_stats

class StatisticalCheck(BaseCheck):
    """Statistical distribution and anomaly checks."""

    @property
    def check_type(self) -> str:
        return "statistical"

    async def execute(self, data_context: "DataContext") -> CheckResult:
        column = self.config["column"]
        check_type = self.config.get("statistical_check", "zscore")
        threshold = self.config.get("threshold", 3.0)

        values = await data_context.get_column_values(self.dataset_id, column)

        if check_type == "zscore":
            return await self._zscore_check(values, threshold, column)
        elif check_type == "iqr":
            return await self._iqr_check(values, threshold, column)
        elif check_type == "ks_test":
            return await self._ks_test(values, column)
        else:
            raise ValueError(f"Unknown statistical check type: {check_type}")

    async def _zscore_check(self, values, threshold, column) -> CheckResult:
        zscores = np.abs(scipy_stats.zscore(values))
        outliers = np.sum(zscores > threshold)
        outlier_pct = outliers / len(values) * 100

        max_outlier_pct = self.config.get("max_outlier_percentage", 1.0)
        passed = outlier_pct <= max_outlier_pct

        return self._result(
            passed=passed,
            message=f"Z-score check: {outlier_pct:.2f}% outliers (threshold: {max_outlier_pct}%)",
            details={
                "column": column,
                "outlier_count": int(outliers),
                "outlier_percentage": outlier_pct,
                "threshold": threshold,
                "mean": float(np.mean(values)),
                "std": float(np.std(values))
            }
        )
```

```python
# monitors/monitor.py
from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class MonitorSchedule(BaseModel):
    type: Literal["cron", "interval", "on_change"]
    cron: str | None = None  # For cron type
    interval_minutes: int | None = None  # For interval type

class AlertConfig(BaseModel):
    channels: list[str]  # ["slack", "email", "pagerduty"]
    severity_threshold: CheckSeverity = CheckSeverity.WARNING
    notify_on_recovery: bool = True

class QualityMonitor(BaseModel):
    id: str
    name: str
    description: str | None = None
    dataset_id: str
    checks: list[dict]  # Check configurations
    schedule: MonitorSchedule
    alerting: AlertConfig | None = None
    enabled: bool = True
    created_at: datetime
    updated_at: datetime

    # SLA configuration
    sla_target_percentage: float | None = None  # e.g., 99.5
    sla_window_days: int = 30
```

```python
# monitors/runner.py
import asyncio
from datetime import datetime

class CheckRunner:
    """Executes quality checks and handles results."""

    def __init__(
        self,
        check_registry: "CheckRegistry",
        alert_dispatcher: "AlertDispatcher",
        result_store: "ResultStore"
    ):
        self.check_registry = check_registry
        self.alert_dispatcher = alert_dispatcher
        self.result_store = result_store

    async def run_monitor(
        self,
        monitor: QualityMonitor,
        data_context: "DataContext"
    ) -> list[CheckResult]:
        """Execute all checks in a monitor."""
        results = []

        # Instantiate checks from config
        checks = [
            self.check_registry.create_check(cfg)
            for cfg in monitor.checks
        ]

        # Execute checks concurrently
        start_time = datetime.utcnow()
        check_tasks = [
            self._execute_check(check, data_context)
            for check in checks
        ]
        results = await asyncio.gather(*check_tasks)

        # Store results
        await self.result_store.save_results(monitor.id, results)

        # Check for failures and alert
        failures = [r for r in results if not r.passed]
        if failures and monitor.alerting:
            await self.alert_dispatcher.dispatch(
                monitor=monitor,
                failures=failures
            )

        return results

    async def _execute_check(
        self,
        check: BaseCheck,
        data_context: "DataContext"
    ) -> CheckResult:
        start = datetime.utcnow()
        result = await check.execute(data_context)
        result.execution_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        return result
```

```python
# anomaly/detector.py
from enum import Enum
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class AnomalyMethod(str, Enum):
    ISOLATION_FOREST = "isolation_forest"
    ZSCORE = "zscore"
    IQR = "iqr"
    PROPHET = "prophet"  # For time series

class AnomalyDetector:
    """Detect anomalies in data using various methods."""

    def __init__(self, method: AnomalyMethod = AnomalyMethod.ISOLATION_FOREST):
        self.method = method
        self._model = None

    async def fit(self, historical_data: np.ndarray):
        """Train anomaly detection model on historical data."""
        if self.method == AnomalyMethod.ISOLATION_FOREST:
            self._model = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            self._scaler = StandardScaler()
            scaled = self._scaler.fit_transform(historical_data.reshape(-1, 1))
            self._model.fit(scaled)

    async def detect(
        self,
        current_data: np.ndarray,
        threshold: float = 0.5
    ) -> list[dict]:
        """Detect anomalies in current data."""
        if self.method == AnomalyMethod.ISOLATION_FOREST:
            return await self._detect_isolation_forest(current_data)
        elif self.method == AnomalyMethod.ZSCORE:
            return await self._detect_zscore(current_data, threshold)
        elif self.method == AnomalyMethod.IQR:
            return await self._detect_iqr(current_data, threshold)

    async def _detect_isolation_forest(self, data: np.ndarray) -> list[dict]:
        scaled = self._scaler.transform(data.reshape(-1, 1))
        predictions = self._model.predict(scaled)
        scores = self._model.decision_function(scaled)

        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # Anomaly
                anomalies.append({
                    "index": i,
                    "value": float(data[i]),
                    "anomaly_score": float(-score),
                    "is_anomaly": True
                })
        return anomalies
```

```python
# remediation/actions.py
from enum import Enum
from abc import ABC, abstractmethod

class RemediationAction(str, Enum):
    NOTIFY = "notify"
    QUARANTINE = "quarantine"
    ROLLBACK = "rollback"
    IMPUTE = "impute"
    DEDUPLICATE = "deduplicate"
    CUSTOM = "custom"

class BaseRemediation(ABC):
    """Base class for remediation actions."""

    @abstractmethod
    async def execute(
        self,
        check_result: CheckResult,
        data_context: "DataContext"
    ) -> "RemediationResult":
        pass

class QuarantineRemediation(BaseRemediation):
    """Move affected records to quarantine table."""

    async def execute(
        self,
        check_result: CheckResult,
        data_context: "DataContext"
    ) -> "RemediationResult":
        affected_records = check_result.details.get("affected_record_ids", [])

        if not affected_records:
            return RemediationResult(
                action=RemediationAction.QUARANTINE,
                success=False,
                message="No affected records identified"
            )

        quarantine_table = f"{check_result.dataset_id}_quarantine"
        moved_count = await data_context.move_to_quarantine(
            source_dataset=check_result.dataset_id,
            quarantine_table=quarantine_table,
            record_ids=affected_records
        )

        return RemediationResult(
            action=RemediationAction.QUARANTINE,
            success=True,
            message=f"Quarantined {moved_count} records",
            details={"quarantine_table": quarantine_table}
        )

class RollbackRemediation(BaseRemediation):
    """Rollback dataset to previous known-good version."""

    def __init__(self, branches_client: "BranchesClient"):
        self.branches = branches_client

    async def execute(
        self,
        check_result: CheckResult,
        data_context: "DataContext"
    ) -> "RemediationResult":
        # Find last passing commit
        last_good = await self._find_last_passing_commit(
            check_result.dataset_id,
            check_result.check_id
        )

        if not last_good:
            return RemediationResult(
                action=RemediationAction.ROLLBACK,
                success=False,
                message="No previous passing version found"
            )

        # Perform rollback via branches
        await self.branches.rollback(
            dataset_id=check_result.dataset_id,
            commit_id=last_good
        )

        return RemediationResult(
            action=RemediationAction.ROLLBACK,
            success=True,
            message=f"Rolled back to commit {last_good[:8]}"
        )
```

### API Routes

```python
# api/routes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/v1/quality", tags=["quality"])

@router.post("/monitors")
async def create_monitor(
    monitor: QualityMonitorCreate,
    db: AsyncSession = Depends(get_db)
) -> QualityMonitor:
    """Create a new quality monitor."""
    pass

@router.get("/monitors")
async def list_monitors(
    dataset_id: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
) -> list[QualityMonitor]:
    """List all quality monitors."""
    pass

@router.get("/monitors/{monitor_id}")
async def get_monitor(
    monitor_id: str,
    db: AsyncSession = Depends(get_db)
) -> QualityMonitor:
    """Get a specific monitor."""
    pass

@router.post("/monitors/{monitor_id}/run")
async def run_monitor(
    monitor_id: str,
    runner: CheckRunner = Depends(get_runner),
    db: AsyncSession = Depends(get_db)
) -> list[CheckResult]:
    """Manually trigger a monitor run."""
    pass

@router.get("/monitors/{monitor_id}/results")
async def get_monitor_results(
    monitor_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[CheckResult]:
    """Get historical results for a monitor."""
    pass

@router.get("/monitors/{monitor_id}/sla")
async def get_monitor_sla(
    monitor_id: str,
    window_days: int = 30,
    db: AsyncSession = Depends(get_db)
) -> SLAStatus:
    """Get SLA compliance status."""
    pass

@router.get("/datasets/{dataset_id}/health")
async def get_dataset_health(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
) -> DatasetHealth:
    """Get overall health status for a dataset."""
    pass

@router.post("/checks/validate")
async def validate_check_config(
    config: dict
) -> ValidationResult:
    """Validate a check configuration without running it."""
    pass
```

---

## Package 2: Forge Lineage

### Purpose

Track end-to-end data lineage at column level, enable impact analysis, visualize dependency graphs, and track data propagation across the platform.

### Module Structure

```
packages/forge-lineage/
├── src/
│   └── forge_lineage/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── node.py            # Lineage node types
│       │   ├── edge.py            # Lineage relationships
│       │   └── graph.py           # Full lineage graph
│       ├── collectors/
│       │   ├── __init__.py
│       │   ├── base.py            # Base collector
│       │   ├── sql.py             # SQL parser
│       │   ├── spark.py           # Spark lineage
│       │   ├── dagster.py         # Pipeline lineage
│       │   └── manual.py          # Manual annotations
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── graph_store.py     # Graph storage
│       │   └── neo4j.py           # Neo4j backend
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── impact.py          # Impact analysis
│       │   ├── dependency.py      # Dependency tracking
│       │   └── propagation.py     # Change propagation
│       ├── visualization/
│       │   ├── __init__.py
│       │   └── graph_layout.py    # Graph visualization
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/node.py
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Any

class NodeType(str, Enum):
    DATASET = "dataset"
    TABLE = "table"
    COLUMN = "column"
    TRANSFORM = "transform"
    PIPELINE = "pipeline"
    EXTERNAL = "external"
    MODEL = "model"

class LineageNode(BaseModel):
    id: str
    type: NodeType
    name: str
    qualified_name: str  # Full path: database.schema.table.column
    metadata: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    # For columns
    data_type: str | None = None
    nullable: bool | None = None

    # For transforms
    transform_type: str | None = None
    code: str | None = None

    def __hash__(self):
        return hash(self.id)
```

```python
# models/edge.py
from enum import Enum

class EdgeType(str, Enum):
    DERIVES_FROM = "derives_from"  # A is computed from B
    CONTAINS = "contains"          # Table contains column
    EXECUTES = "executes"          # Pipeline executes transform
    PRODUCES = "produces"          # Transform produces output
    CONSUMES = "consumes"          # Transform consumes input

class TransformationType(str, Enum):
    DIRECT = "direct"              # 1:1 mapping
    AGGREGATION = "aggregation"    # Many:1
    FILTER = "filter"              # Subset
    JOIN = "join"                  # Multiple sources
    UNION = "union"                # Combine
    EXPRESSION = "expression"      # Calculated
    UNKNOWN = "unknown"

class LineageEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    transformation: TransformationType = TransformationType.UNKNOWN
    expression: str | None = None  # SQL/code that defines the transform
    confidence: float = 1.0        # For inferred lineage
    metadata: dict[str, Any] = {}
    created_at: datetime
```

```python
# models/graph.py
from typing import Iterator

class LineageGraph:
    """In-memory lineage graph with traversal operations."""

    def __init__(self):
        self._nodes: dict[str, LineageNode] = {}
        self._edges: dict[str, LineageEdge] = {}
        self._outgoing: dict[str, set[str]] = {}  # node_id -> edge_ids
        self._incoming: dict[str, set[str]] = {}  # node_id -> edge_ids

    def add_node(self, node: LineageNode):
        self._nodes[node.id] = node
        self._outgoing.setdefault(node.id, set())
        self._incoming.setdefault(node.id, set())

    def add_edge(self, edge: LineageEdge):
        self._edges[edge.id] = edge
        self._outgoing[edge.source_id].add(edge.id)
        self._incoming[edge.target_id].add(edge.id)

    def get_upstream(
        self,
        node_id: str,
        depth: int = -1,
        edge_types: list[EdgeType] | None = None
    ) -> "LineageGraph":
        """Get all upstream dependencies."""
        result = LineageGraph()
        visited = set()
        self._traverse_upstream(node_id, depth, edge_types, result, visited)
        return result

    def get_downstream(
        self,
        node_id: str,
        depth: int = -1,
        edge_types: list[EdgeType] | None = None
    ) -> "LineageGraph":
        """Get all downstream dependents."""
        result = LineageGraph()
        visited = set()
        self._traverse_downstream(node_id, depth, edge_types, result, visited)
        return result

    def _traverse_upstream(
        self,
        node_id: str,
        depth: int,
        edge_types: list[EdgeType] | None,
        result: "LineageGraph",
        visited: set[str]
    ):
        if node_id in visited or depth == 0:
            return
        visited.add(node_id)

        node = self._nodes.get(node_id)
        if node:
            result.add_node(node)

        for edge_id in self._incoming.get(node_id, []):
            edge = self._edges[edge_id]
            if edge_types is None or edge.edge_type in edge_types:
                result.add_edge(edge)
                self._traverse_upstream(
                    edge.source_id,
                    depth - 1 if depth > 0 else -1,
                    edge_types,
                    result,
                    visited
                )

    def get_column_lineage(self, column_id: str) -> "ColumnLineage":
        """Get detailed column-level lineage."""
        upstream = self.get_upstream(column_id, edge_types=[EdgeType.DERIVES_FROM])
        downstream = self.get_downstream(column_id, edge_types=[EdgeType.DERIVES_FROM])

        return ColumnLineage(
            column_id=column_id,
            upstream_columns=[
                n for n in upstream._nodes.values()
                if n.type == NodeType.COLUMN
            ],
            downstream_columns=[
                n for n in downstream._nodes.values()
                if n.type == NodeType.COLUMN
            ],
            transformations=[
                e for e in upstream._edges.values()
            ]
        )
```

```python
# collectors/sql.py
from sqlglot import parse, exp
from sqlglot.lineage import lineage

class SQLLineageCollector:
    """Extract column-level lineage from SQL queries."""

    async def collect(
        self,
        sql: str,
        dialect: str = "postgres",
        source_catalog: dict[str, list[str]] | None = None
    ) -> list[LineageEdge]:
        """Parse SQL and extract lineage relationships."""
        edges = []

        try:
            # Use sqlglot's lineage analysis
            for output_col, deps in lineage(sql, dialect=dialect).items():
                target_id = self._column_to_id(output_col)

                for source_col in deps:
                    source_id = self._column_to_id(source_col)

                    edges.append(LineageEdge(
                        id=f"{source_id}->{target_id}",
                        source_id=source_id,
                        target_id=target_id,
                        edge_type=EdgeType.DERIVES_FROM,
                        transformation=self._infer_transformation(sql, source_col, output_col),
                        expression=self._extract_expression(sql, output_col)
                    ))
        except Exception as e:
            # Fall back to table-level lineage
            edges = await self._collect_table_level(sql, dialect)

        return edges

    def _infer_transformation(
        self,
        sql: str,
        source_col: str,
        target_col: str
    ) -> TransformationType:
        """Infer the type of transformation applied."""
        ast = parse(sql)[0]

        # Check for aggregations
        for node in ast.walk():
            if isinstance(node, (exp.Sum, exp.Count, exp.Avg, exp.Min, exp.Max)):
                return TransformationType.AGGREGATION
            if isinstance(node, exp.Case):
                return TransformationType.EXPRESSION

        # Check if direct mapping
        if source_col.lower() == target_col.lower():
            return TransformationType.DIRECT

        return TransformationType.EXPRESSION
```

```python
# collectors/dagster.py
from dagster import AssetKey

class DagsterLineageCollector:
    """Collect lineage from Dagster asset definitions."""

    async def collect_from_job(
        self,
        job_name: str,
        run_id: str
    ) -> list[LineageEdge]:
        """Extract lineage from a Dagster job run."""
        # Get asset materialization events
        events = await self._get_materialization_events(job_name, run_id)

        edges = []
        for event in events:
            asset_key = event.asset_key
            input_assets = event.upstream_lineage

            for input_asset in input_assets:
                edges.append(LineageEdge(
                    id=f"{input_asset.to_string()}->{asset_key.to_string()}",
                    source_id=input_asset.to_string(),
                    target_id=asset_key.to_string(),
                    edge_type=EdgeType.DERIVES_FROM,
                    metadata={
                        "run_id": run_id,
                        "job_name": job_name,
                        "timestamp": event.timestamp
                    }
                ))

        return edges
```

```python
# analysis/impact.py
class ImpactAnalyzer:
    """Analyze impact of changes to data assets."""

    def __init__(self, graph: LineageGraph):
        self.graph = graph

    async def analyze_column_change(
        self,
        column_id: str
    ) -> "ImpactReport":
        """Analyze impact if a column changes."""
        downstream = self.graph.get_downstream(column_id)

        # Categorize impacted assets
        impacted_columns = []
        impacted_transforms = []
        impacted_dashboards = []
        impacted_models = []

        for node in downstream._nodes.values():
            if node.type == NodeType.COLUMN:
                impacted_columns.append(node)
            elif node.type == NodeType.TRANSFORM:
                impacted_transforms.append(node)
            elif node.type == NodeType.MODEL:
                impacted_models.append(node)

        # Calculate risk score
        risk_score = self._calculate_risk(
            impacted_columns,
            impacted_transforms,
            impacted_models
        )

        return ImpactReport(
            source_id=column_id,
            impacted_columns=impacted_columns,
            impacted_transforms=impacted_transforms,
            impacted_dashboards=impacted_dashboards,
            impacted_models=impacted_models,
            total_impacted=len(downstream._nodes),
            risk_score=risk_score,
            recommendations=self._generate_recommendations(downstream)
        )

    async def analyze_schema_change(
        self,
        table_id: str,
        change_type: str,  # "add_column", "remove_column", "rename_column", "type_change"
        column_name: str,
        new_value: str | None = None
    ) -> "SchemaChangeImpact":
        """Analyze impact of a schema change."""
        if change_type == "remove_column":
            # High impact - need to find all downstream uses
            column_id = f"{table_id}.{column_name}"
            downstream = self.graph.get_downstream(column_id)

            breaking_changes = []
            for node in downstream._nodes.values():
                if node.type == NodeType.TRANSFORM:
                    breaking_changes.append({
                        "asset": node.qualified_name,
                        "type": "transform_failure",
                        "reason": f"Missing input column: {column_name}"
                    })

            return SchemaChangeImpact(
                change_type=change_type,
                is_breaking=len(breaking_changes) > 0,
                breaking_changes=breaking_changes,
                affected_assets=list(downstream._nodes.values()),
                migration_steps=self._generate_migration_steps(change_type, column_name)
            )
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/lineage", tags=["lineage"])

@router.get("/graph")
async def get_lineage_graph(
    root_id: str,
    direction: Literal["upstream", "downstream", "both"] = "both",
    depth: int = 5,
    node_types: list[NodeType] | None = None
) -> LineageGraphResponse:
    """Get lineage graph for visualization."""
    pass

@router.get("/columns/{column_id}/lineage")
async def get_column_lineage(
    column_id: str,
    include_transformations: bool = True
) -> ColumnLineage:
    """Get detailed column-level lineage."""
    pass

@router.get("/tables/{table_id}/lineage")
async def get_table_lineage(
    table_id: str,
    column_level: bool = False
) -> TableLineage:
    """Get table-level lineage."""
    pass

@router.post("/impact/column")
async def analyze_column_impact(
    column_id: str,
    change_type: str | None = None
) -> ImpactReport:
    """Analyze downstream impact of column change."""
    pass

@router.post("/impact/schema")
async def analyze_schema_impact(
    table_id: str,
    changes: list[SchemaChange]
) -> SchemaChangeImpact:
    """Analyze impact of schema changes."""
    pass

@router.get("/search")
async def search_lineage(
    query: str,
    node_types: list[NodeType] | None = None,
    limit: int = 50
) -> list[LineageNode]:
    """Search for nodes in the lineage graph."""
    pass
```

---

## Package 3: Forge Branches

### Purpose

Git-like versioning for datasets enabling branch-based development, merge workflows, conflict resolution, time travel queries, and branch comparison.

### Module Structure

```
packages/forge-branches/
├── src/
│   └── forge_branches/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── branch.py          # Branch model
│       │   ├── commit.py          # Commit model
│       │   ├── diff.py            # Diff representation
│       │   └── conflict.py        # Merge conflicts
│       ├── operations/
│       │   ├── __init__.py
│       │   ├── branch.py          # Branch operations
│       │   ├── commit.py          # Commit operations
│       │   ├── merge.py           # Merge strategies
│       │   ├── revert.py          # Revert operations
│       │   └── cherry_pick.py     # Cherry-pick
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── iceberg.py         # Apache Iceberg backend
│       │   ├── delta.py           # Delta Lake backend
│       │   └── base.py            # Storage interface
│       ├── query/
│       │   ├── __init__.py
│       │   ├── time_travel.py     # Time travel queries
│       │   └── diff_query.py      # Diff queries
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/branch.py
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class BranchStatus(str, Enum):
    ACTIVE = "active"
    MERGED = "merged"
    ARCHIVED = "archived"

class Branch(BaseModel):
    id: str
    name: str
    dataset_id: str
    parent_branch_id: str | None = None  # None for main
    parent_commit_id: str | None = None  # Fork point
    head_commit_id: str
    status: BranchStatus = BranchStatus.ACTIVE
    created_by: str
    created_at: datetime
    description: str | None = None

    # Protection rules
    protected: bool = False
    require_approval: bool = False
    allowed_mergers: list[str] | None = None

class BranchComparison(BaseModel):
    base_branch: Branch
    compare_branch: Branch
    common_ancestor_commit: str
    commits_ahead: int
    commits_behind: int
    can_fast_forward: bool
    has_conflicts: bool
    changed_files: list[str]
```

```python
# models/commit.py
from pydantic import BaseModel
from datetime import datetime
from typing import Any

class CommitStats(BaseModel):
    rows_added: int
    rows_deleted: int
    rows_modified: int
    bytes_added: int
    bytes_deleted: int

class DataCommit(BaseModel):
    id: str  # SHA-256 hash
    dataset_id: str
    branch_id: str
    parent_ids: list[str]  # Can have multiple parents for merges
    message: str
    author: str
    timestamp: datetime
    stats: CommitStats
    metadata: dict[str, Any] = {}

    # Storage reference
    snapshot_id: str  # Iceberg snapshot ID or Delta version

    def is_merge_commit(self) -> bool:
        return len(self.parent_ids) > 1

class CommitHistory(BaseModel):
    commits: list[DataCommit]
    total_count: int
    has_more: bool
```

```python
# models/diff.py
from enum import Enum
from pydantic import BaseModel

class ChangeType(str, Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"

class RowChange(BaseModel):
    change_type: ChangeType
    primary_key: dict[str, Any]
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    changed_columns: list[str] | None = None

class SchemaDiff(BaseModel):
    added_columns: list[dict]
    removed_columns: list[str]
    modified_columns: list[dict]  # Type changes

class DatasetDiff(BaseModel):
    base_commit_id: str
    compare_commit_id: str
    schema_diff: SchemaDiff | None = None
    row_changes: list[RowChange]
    summary: dict[str, int]  # {"inserts": N, "updates": N, "deletes": N}

    def has_schema_changes(self) -> bool:
        if not self.schema_diff:
            return False
        return bool(
            self.schema_diff.added_columns or
            self.schema_diff.removed_columns or
            self.schema_diff.modified_columns
        )
```

```python
# models/conflict.py
from enum import Enum

class ConflictType(str, Enum):
    ROW_UPDATE = "row_update"      # Same row modified in both branches
    SCHEMA_CHANGE = "schema_change" # Incompatible schema changes
    CONSTRAINT = "constraint"       # Constraint violation after merge

class MergeConflict(BaseModel):
    id: str
    conflict_type: ConflictType
    location: str  # Row key or column name
    base_value: Any
    ours_value: Any
    theirs_value: Any
    resolution: str | None = None  # "ours", "theirs", "manual"
    resolved_value: Any | None = None

class MergeConflictSet(BaseModel):
    merge_id: str
    source_branch: str
    target_branch: str
    conflicts: list[MergeConflict]
    resolved_count: int
    total_count: int

    @property
    def is_fully_resolved(self) -> bool:
        return self.resolved_count == self.total_count
```

```python
# operations/merge.py
from enum import Enum
from abc import ABC, abstractmethod

class MergeStrategy(str, Enum):
    FAST_FORWARD = "fast_forward"
    THREE_WAY = "three_way"
    SQUASH = "squash"
    REBASE = "rebase"

class MergeResult(BaseModel):
    success: bool
    strategy_used: MergeStrategy
    merge_commit_id: str | None = None
    conflicts: MergeConflictSet | None = None
    stats: CommitStats | None = None

class MergeEngine:
    """Handle branch merge operations."""

    def __init__(self, storage: "BranchStorage"):
        self.storage = storage

    async def merge(
        self,
        source_branch_id: str,
        target_branch_id: str,
        strategy: MergeStrategy = MergeStrategy.THREE_WAY,
        message: str | None = None,
        author: str = None
    ) -> MergeResult:
        """Merge source branch into target branch."""
        source = await self.storage.get_branch(source_branch_id)
        target = await self.storage.get_branch(target_branch_id)

        # Check if fast-forward is possible
        comparison = await self._compare_branches(source, target)

        if strategy == MergeStrategy.FAST_FORWARD:
            if not comparison.can_fast_forward:
                return MergeResult(
                    success=False,
                    strategy_used=strategy,
                    conflicts=None
                )
            return await self._fast_forward_merge(source, target, author)

        elif strategy == MergeStrategy.THREE_WAY:
            # Find common ancestor
            ancestor_commit = await self._find_common_ancestor(source, target)

            # Compute three-way diff
            conflicts = await self._detect_conflicts(
                ancestor_commit,
                source.head_commit_id,
                target.head_commit_id
            )

            if conflicts.total_count > 0:
                return MergeResult(
                    success=False,
                    strategy_used=strategy,
                    conflicts=conflicts
                )

            # Create merge commit
            return await self._create_merge_commit(
                source, target, ancestor_commit, message, author
            )

        elif strategy == MergeStrategy.SQUASH:
            # Combine all commits into single commit
            return await self._squash_merge(source, target, message, author)

    async def _detect_conflicts(
        self,
        ancestor_commit: str,
        source_commit: str,
        target_commit: str
    ) -> MergeConflictSet:
        """Detect merge conflicts using three-way comparison."""
        # Get changes from ancestor to source
        source_changes = await self.storage.get_changes(ancestor_commit, source_commit)

        # Get changes from ancestor to target
        target_changes = await self.storage.get_changes(ancestor_commit, target_commit)

        conflicts = []

        # Find overlapping row modifications
        source_keys = {c.primary_key_tuple for c in source_changes if c.change_type == ChangeType.UPDATE}
        target_keys = {c.primary_key_tuple for c in target_changes if c.change_type == ChangeType.UPDATE}

        overlapping = source_keys & target_keys

        for key in overlapping:
            source_change = next(c for c in source_changes if c.primary_key_tuple == key)
            target_change = next(c for c in target_changes if c.primary_key_tuple == key)

            # Check if same columns modified differently
            source_cols = set(source_change.changed_columns or [])
            target_cols = set(target_change.changed_columns or [])
            conflicting_cols = source_cols & target_cols

            for col in conflicting_cols:
                if source_change.new_values[col] != target_change.new_values[col]:
                    conflicts.append(MergeConflict(
                        id=f"{key}:{col}",
                        conflict_type=ConflictType.ROW_UPDATE,
                        location=f"{key}.{col}",
                        base_value=source_change.old_values.get(col),
                        ours_value=target_change.new_values[col],
                        theirs_value=source_change.new_values[col]
                    ))

        return MergeConflictSet(
            merge_id=f"{source_commit[:8]}_{target_commit[:8]}",
            source_branch=source_commit,
            target_branch=target_commit,
            conflicts=conflicts,
            resolved_count=0,
            total_count=len(conflicts)
        )

    async def resolve_conflict(
        self,
        merge_id: str,
        conflict_id: str,
        resolution: str,
        manual_value: Any | None = None
    ) -> MergeConflict:
        """Resolve a specific merge conflict."""
        conflict_set = await self.storage.get_conflicts(merge_id)
        conflict = next(c for c in conflict_set.conflicts if c.id == conflict_id)

        if resolution == "ours":
            conflict.resolved_value = conflict.ours_value
        elif resolution == "theirs":
            conflict.resolved_value = conflict.theirs_value
        elif resolution == "manual":
            conflict.resolved_value = manual_value

        conflict.resolution = resolution
        await self.storage.save_conflict(merge_id, conflict)

        return conflict
```

```python
# storage/iceberg.py
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table

class IcebergBranchStorage:
    """Apache Iceberg backend for branch storage."""

    def __init__(self, catalog_config: dict):
        self.catalog = load_catalog(**catalog_config)

    async def create_branch(
        self,
        dataset_id: str,
        branch_name: str,
        from_commit: str | None = None
    ) -> Branch:
        """Create a new branch using Iceberg's branch feature."""
        table = self.catalog.load_table(dataset_id)

        if from_commit:
            # Branch from specific snapshot
            snapshot_id = await self._commit_to_snapshot(from_commit)
            table.manage_snapshots().create_branch(
                branch_name,
                snapshot_id
            ).commit()
        else:
            # Branch from current
            table.manage_snapshots().create_branch(
                branch_name
            ).commit()

        return Branch(
            id=f"{dataset_id}:{branch_name}",
            name=branch_name,
            dataset_id=dataset_id,
            head_commit_id=self._snapshot_to_commit(table.current_snapshot().snapshot_id),
            created_at=datetime.utcnow()
        )

    async def commit(
        self,
        dataset_id: str,
        branch_name: str,
        data: "DataFrame",
        message: str,
        author: str
    ) -> DataCommit:
        """Commit data changes to a branch."""
        table = self.catalog.load_table(dataset_id)

        # Switch to branch
        table.manage_snapshots().set_current_snapshot(
            branch=branch_name
        ).commit()

        # Write data
        table.append(data)

        # Get new snapshot
        snapshot = table.current_snapshot()

        return DataCommit(
            id=self._snapshot_to_commit(snapshot.snapshot_id),
            dataset_id=dataset_id,
            branch_id=branch_name,
            parent_ids=[self._snapshot_to_commit(snapshot.parent_id)] if snapshot.parent_id else [],
            message=message,
            author=author,
            timestamp=datetime.fromtimestamp(snapshot.timestamp_ms / 1000),
            snapshot_id=str(snapshot.snapshot_id),
            stats=self._compute_stats(snapshot)
        )

    async def time_travel(
        self,
        dataset_id: str,
        as_of: datetime | str  # datetime or commit_id
    ) -> Table:
        """Query data as of a specific point in time or commit."""
        table = self.catalog.load_table(dataset_id)

        if isinstance(as_of, datetime):
            return table.scan(snapshot_id=None, options={
                "as-of-timestamp": int(as_of.timestamp() * 1000)
            })
        else:
            snapshot_id = await self._commit_to_snapshot(as_of)
            return table.scan(snapshot_id=snapshot_id)
```

```python
# query/time_travel.py
class TimeTravelQuery:
    """Execute queries at specific points in time."""

    def __init__(self, storage: "BranchStorage"):
        self.storage = storage

    async def query_at_commit(
        self,
        dataset_id: str,
        commit_id: str,
        sql: str | None = None,
        filters: dict | None = None
    ) -> "DataFrame":
        """Query dataset as it existed at a specific commit."""
        table = await self.storage.time_travel(dataset_id, commit_id)

        if sql:
            return await self._execute_sql(table, sql)
        elif filters:
            return await self._apply_filters(table, filters)
        else:
            return table.to_arrow().to_pandas()

    async def query_at_time(
        self,
        dataset_id: str,
        timestamp: datetime,
        sql: str | None = None
    ) -> "DataFrame":
        """Query dataset as it existed at a specific time."""
        table = await self.storage.time_travel(dataset_id, timestamp)

        if sql:
            return await self._execute_sql(table, sql)
        return table.to_arrow().to_pandas()

    async def compare_versions(
        self,
        dataset_id: str,
        version_a: str,  # commit_id or datetime
        version_b: str,
        columns: list[str] | None = None
    ) -> DatasetDiff:
        """Compare two versions of a dataset."""
        data_a = await self.query_at_commit(dataset_id, version_a)
        data_b = await self.query_at_commit(dataset_id, version_b)

        return self._compute_diff(data_a, data_b, columns)
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/branches", tags=["branches"])

@router.get("/datasets/{dataset_id}/branches")
async def list_branches(
    dataset_id: str,
    status: BranchStatus | None = None
) -> list[Branch]:
    """List all branches for a dataset."""
    pass

@router.post("/datasets/{dataset_id}/branches")
async def create_branch(
    dataset_id: str,
    name: str,
    from_commit: str | None = None,
    description: str | None = None
) -> Branch:
    """Create a new branch."""
    pass

@router.get("/datasets/{dataset_id}/branches/{branch_name}")
async def get_branch(
    dataset_id: str,
    branch_name: str
) -> Branch:
    """Get branch details."""
    pass

@router.delete("/datasets/{dataset_id}/branches/{branch_name}")
async def delete_branch(
    dataset_id: str,
    branch_name: str
) -> dict:
    """Delete a branch."""
    pass

@router.get("/datasets/{dataset_id}/branches/{branch_name}/commits")
async def list_commits(
    dataset_id: str,
    branch_name: str,
    limit: int = 50,
    offset: int = 0
) -> CommitHistory:
    """List commits on a branch."""
    pass

@router.post("/datasets/{dataset_id}/branches/{branch_name}/commits")
async def create_commit(
    dataset_id: str,
    branch_name: str,
    message: str,
    data: UploadFile
) -> DataCommit:
    """Create a new commit."""
    pass

@router.get("/datasets/{dataset_id}/compare")
async def compare_branches(
    dataset_id: str,
    base: str,
    compare: str
) -> BranchComparison:
    """Compare two branches."""
    pass

@router.post("/datasets/{dataset_id}/merge")
async def merge_branches(
    dataset_id: str,
    source_branch: str,
    target_branch: str,
    strategy: MergeStrategy = MergeStrategy.THREE_WAY,
    message: str | None = None
) -> MergeResult:
    """Merge source branch into target."""
    pass

@router.post("/datasets/{dataset_id}/merges/{merge_id}/resolve")
async def resolve_conflict(
    dataset_id: str,
    merge_id: str,
    conflict_id: str,
    resolution: str,
    manual_value: Any | None = None
) -> MergeConflict:
    """Resolve a merge conflict."""
    pass

@router.get("/datasets/{dataset_id}/commits/{commit_id}/data")
async def query_at_commit(
    dataset_id: str,
    commit_id: str,
    sql: str | None = None,
    limit: int = 1000
) -> dict:
    """Query data at a specific commit (time travel)."""
    pass

@router.get("/datasets/{dataset_id}/diff")
async def get_diff(
    dataset_id: str,
    base_commit: str,
    compare_commit: str
) -> DatasetDiff:
    """Get diff between two commits."""
    pass
```

---

## Package 4: Forge Navigator

### Purpose

Unified data catalog and discovery platform providing search, documentation, ownership management, data profiling, and usage analytics.

### Module Structure

```
packages/forge-navigator/
├── src/
│   └── forge_navigator/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── asset.py           # Data asset model
│       │   ├── tag.py             # Tags and classification
│       │   ├── ownership.py       # Ownership model
│       │   └── glossary.py        # Business glossary
│       ├── catalog/
│       │   ├── __init__.py
│       │   ├── indexer.py         # Asset indexing
│       │   ├── crawler.py         # Schema crawling
│       │   └── sync.py            # Catalog sync
│       ├── search/
│       │   ├── __init__.py
│       │   ├── engine.py          # Search engine
│       │   ├── ranking.py         # Search ranking
│       │   └── filters.py         # Search filters
│       ├── discovery/
│       │   ├── __init__.py
│       │   ├── recommendations.py # Asset recommendations
│       │   ├── similar.py         # Similar assets
│       │   └── popular.py         # Popular assets
│       ├── profiling/
│       │   ├── __init__.py
│       │   ├── profiler.py        # Data profiling
│       │   └── statistics.py      # Column statistics
│       ├── governance/
│       │   ├── __init__.py
│       │   ├── classification.py  # Data classification
│       │   ├── pii.py             # PII detection
│       │   └── access.py          # Access patterns
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/asset.py
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Any

class AssetType(str, Enum):
    TABLE = "table"
    VIEW = "view"
    DATASET = "dataset"
    PIPELINE = "pipeline"
    DASHBOARD = "dashboard"
    MODEL = "model"
    FEATURE = "feature"
    METRIC = "metric"

class ColumnProfile(BaseModel):
    name: str
    data_type: str
    nullable: bool
    description: str | None = None
    statistics: dict[str, Any] | None = None
    sample_values: list[Any] | None = None
    pii_classification: str | None = None
    tags: list[str] = []

class DataAsset(BaseModel):
    id: str
    name: str
    qualified_name: str
    type: AssetType
    description: str | None = None

    # Schema
    columns: list[ColumnProfile] = []
    primary_key: list[str] | None = None

    # Ownership
    owner_id: str | None = None
    owner_team: str | None = None
    stewards: list[str] = []

    # Classification
    tags: list[str] = []
    classification: str | None = None  # "public", "internal", "confidential", "restricted"
    domain: str | None = None

    # Metadata
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime | None = None
    row_count: int | None = None
    byte_size: int | None = None

    # Source
    source_system: str | None = None
    source_location: str | None = None

    # Quality
    quality_score: float | None = None
    freshness_hours: float | None = None

    # Usage
    view_count: int = 0
    query_count: int = 0
    downstream_count: int = 0
```

```python
# models/glossary.py
class GlossaryTerm(BaseModel):
    id: str
    name: str
    definition: str
    domain: str | None = None
    synonyms: list[str] = []
    related_terms: list[str] = []
    examples: list[str] = []
    owner_id: str | None = None
    created_at: datetime
    updated_at: datetime

    # Linked assets
    linked_columns: list[str] = []
    linked_assets: list[str] = []

class BusinessGlossary(BaseModel):
    id: str
    name: str
    description: str | None = None
    domain: str
    terms: list[GlossaryTerm] = []
```

```python
# search/engine.py
from typing import Literal
from elasticsearch import AsyncElasticsearch

class CatalogSearchEngine:
    """Full-text search over data catalog."""

    def __init__(self, es_client: AsyncElasticsearch):
        self.es = es_client
        self.index_name = "forge_catalog"

    async def search(
        self,
        query: str,
        asset_types: list[AssetType] | None = None,
        domains: list[str] | None = None,
        tags: list[str] | None = None,
        owners: list[str] | None = None,
        classification: str | None = None,
        sort_by: Literal["relevance", "popularity", "freshness", "name"] = "relevance",
        limit: int = 50,
        offset: int = 0
    ) -> "SearchResults":
        """Execute catalog search."""
        # Build Elasticsearch query
        must_clauses = []
        filter_clauses = []

        # Full-text search across name, description, columns
        if query:
            must_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "name^3",
                        "description^2",
                        "columns.name^2",
                        "columns.description",
                        "tags^2",
                        "qualified_name"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })

        # Filters
        if asset_types:
            filter_clauses.append({"terms": {"type": [t.value for t in asset_types]}})
        if domains:
            filter_clauses.append({"terms": {"domain": domains}})
        if tags:
            filter_clauses.append({"terms": {"tags": tags}})
        if owners:
            filter_clauses.append({"terms": {"owner_id": owners}})
        if classification:
            filter_clauses.append({"term": {"classification": classification}})

        # Build full query
        es_query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}],
                "filter": filter_clauses
            }
        }

        # Sorting
        sort_config = self._get_sort_config(sort_by)

        # Execute search
        response = await self.es.search(
            index=self.index_name,
            query=es_query,
            sort=sort_config,
            from_=offset,
            size=limit,
            highlight={
                "fields": {
                    "name": {},
                    "description": {},
                    "columns.name": {}
                }
            }
        )

        return self._parse_results(response)

    async def suggest(
        self,
        prefix: str,
        limit: int = 10
    ) -> list[dict]:
        """Autocomplete suggestions."""
        response = await self.es.search(
            index=self.index_name,
            suggest={
                "asset-suggest": {
                    "prefix": prefix,
                    "completion": {
                        "field": "name.suggest",
                        "size": limit,
                        "skip_duplicates": True
                    }
                }
            }
        )
        return [s["text"] for s in response["suggest"]["asset-suggest"][0]["options"]]
```

```python
# discovery/recommendations.py
class AssetRecommender:
    """Recommend relevant data assets to users."""

    def __init__(
        self,
        usage_tracker: "UsageTracker",
        lineage_graph: "LineageGraph",
        search_engine: "CatalogSearchEngine"
    ):
        self.usage = usage_tracker
        self.lineage = lineage_graph
        self.search = search_engine

    async def get_recommendations(
        self,
        user_id: str,
        context: dict | None = None,
        limit: int = 10
    ) -> list[DataAsset]:
        """Get personalized asset recommendations."""
        # Get user's recent activity
        recent_views = await self.usage.get_recent_views(user_id, limit=50)
        recent_queries = await self.usage.get_recent_queries(user_id, limit=20)

        # Find similar assets based on:
        # 1. Assets used by similar users (collaborative filtering)
        similar_users = await self._find_similar_users(user_id)
        collaborative_assets = await self._get_collaborative_recommendations(similar_users)

        # 2. Assets related via lineage
        lineage_assets = []
        for view in recent_views[:10]:
            downstream = self.lineage.get_downstream(view.asset_id, depth=2)
            upstream = self.lineage.get_upstream(view.asset_id, depth=2)
            lineage_assets.extend(downstream._nodes.values())
            lineage_assets.extend(upstream._nodes.values())

        # 3. Assets in same domain/with similar tags
        content_assets = await self._get_content_recommendations(recent_views)

        # 4. Popular assets user hasn't seen
        popular_assets = await self.usage.get_popular_assets(limit=20)
        unseen_popular = [a for a in popular_assets if a.id not in {v.asset_id for v in recent_views}]

        # Score and rank recommendations
        candidates = self._merge_recommendations(
            collaborative=collaborative_assets,
            lineage=lineage_assets,
            content=content_assets,
            popular=unseen_popular
        )

        return candidates[:limit]

    async def get_similar_assets(
        self,
        asset_id: str,
        limit: int = 10
    ) -> list[DataAsset]:
        """Find assets similar to a given asset."""
        asset = await self._get_asset(asset_id)

        # Find similar by:
        # 1. Schema similarity (column names and types)
        schema_similar = await self._find_schema_similar(asset)

        # 2. Name/description similarity
        text_similar = await self.search.search(
            query=f"{asset.name} {asset.description or ''}",
            limit=limit * 2
        )

        # 3. Same domain/tags
        domain_similar = await self.search.search(
            query="",
            domains=[asset.domain] if asset.domain else None,
            tags=asset.tags[:3] if asset.tags else None,
            limit=limit * 2
        )

        # Combine and deduplicate
        candidates = {}
        for a in schema_similar:
            candidates[a.id] = candidates.get(a.id, 0) + 3
        for a in text_similar.assets:
            if a.id != asset_id:
                candidates[a.id] = candidates.get(a.id, 0) + 2
        for a in domain_similar.assets:
            if a.id != asset_id:
                candidates[a.id] = candidates.get(a.id, 0) + 1

        # Sort by score
        sorted_ids = sorted(candidates.keys(), key=lambda x: candidates[x], reverse=True)
        return [await self._get_asset(aid) for aid in sorted_ids[:limit]]
```

```python
# profiling/profiler.py
import pandas as pd
import numpy as np

class DataProfiler:
    """Generate statistical profiles for data assets."""

    async def profile_table(
        self,
        data: pd.DataFrame,
        sample_size: int = 10000
    ) -> "TableProfile":
        """Generate comprehensive table profile."""
        if len(data) > sample_size:
            data = data.sample(n=sample_size, random_state=42)

        column_profiles = []
        for col in data.columns:
            profile = await self._profile_column(data[col], col)
            column_profiles.append(profile)

        return TableProfile(
            row_count=len(data),
            column_count=len(data.columns),
            columns=column_profiles,
            memory_usage=int(data.memory_usage(deep=True).sum()),
            duplicate_row_count=int(data.duplicated().sum()),
            profiled_at=datetime.utcnow()
        )

    async def _profile_column(
        self,
        series: pd.Series,
        name: str
    ) -> ColumnProfile:
        """Profile a single column."""
        dtype = str(series.dtype)
        null_count = int(series.isna().sum())
        null_percentage = null_count / len(series) * 100 if len(series) > 0 else 0
        distinct_count = int(series.nunique())

        stats = {
            "null_count": null_count,
            "null_percentage": round(null_percentage, 2),
            "distinct_count": distinct_count,
            "distinct_percentage": round(distinct_count / len(series) * 100, 2) if len(series) > 0 else 0
        }

        # Numeric stats
        if pd.api.types.is_numeric_dtype(series):
            clean = series.dropna()
            stats.update({
                "min": float(clean.min()) if len(clean) > 0 else None,
                "max": float(clean.max()) if len(clean) > 0 else None,
                "mean": float(clean.mean()) if len(clean) > 0 else None,
                "median": float(clean.median()) if len(clean) > 0 else None,
                "std": float(clean.std()) if len(clean) > 0 else None,
                "percentile_25": float(clean.quantile(0.25)) if len(clean) > 0 else None,
                "percentile_75": float(clean.quantile(0.75)) if len(clean) > 0 else None,
                "zeros": int((clean == 0).sum()),
                "negatives": int((clean < 0).sum())
            })

        # String stats
        elif pd.api.types.is_string_dtype(series) or series.dtype == object:
            clean = series.dropna().astype(str)
            if len(clean) > 0:
                lengths = clean.str.len()
                stats.update({
                    "min_length": int(lengths.min()),
                    "max_length": int(lengths.max()),
                    "avg_length": round(lengths.mean(), 2),
                    "empty_count": int((clean == "").sum())
                })

                # Top values
                top_values = clean.value_counts().head(10).to_dict()
                stats["top_values"] = top_values

        # Date stats
        elif pd.api.types.is_datetime64_any_dtype(series):
            clean = series.dropna()
            if len(clean) > 0:
                stats.update({
                    "min_date": clean.min().isoformat(),
                    "max_date": clean.max().isoformat(),
                    "date_range_days": (clean.max() - clean.min()).days
                })

        # Sample values
        sample_values = series.dropna().head(5).tolist()

        return ColumnProfile(
            name=name,
            data_type=dtype,
            nullable=null_count > 0,
            statistics=stats,
            sample_values=sample_values
        )
```

```python
# governance/pii.py
import re
from enum import Enum

class PIIType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    ADDRESS = "address"
    NAME = "name"
    DATE_OF_BIRTH = "date_of_birth"
    IP_ADDRESS = "ip_address"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"

class PIIDetector:
    """Detect PII in data columns."""

    PATTERNS = {
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.PHONE: r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        PIIType.SSN: r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
        PIIType.CREDIT_CARD: r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        PIIType.IP_ADDRESS: r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }

    NAME_INDICATORS = ['name', 'first_name', 'last_name', 'full_name', 'customer_name']
    DOB_INDICATORS = ['dob', 'date_of_birth', 'birth_date', 'birthday']
    ADDRESS_INDICATORS = ['address', 'street', 'city', 'zip', 'postal']

    async def detect(
        self,
        column_name: str,
        sample_values: list[Any]
    ) -> PIIType | None:
        """Detect if column contains PII."""
        # Check column name for indicators
        col_lower = column_name.lower()

        if any(ind in col_lower for ind in self.NAME_INDICATORS):
            return PIIType.NAME
        if any(ind in col_lower for ind in self.DOB_INDICATORS):
            return PIIType.DATE_OF_BIRTH
        if any(ind in col_lower for ind in self.ADDRESS_INDICATORS):
            return PIIType.ADDRESS
        if 'email' in col_lower:
            return PIIType.EMAIL
        if 'phone' in col_lower or 'mobile' in col_lower:
            return PIIType.PHONE
        if 'ssn' in col_lower or 'social_security' in col_lower:
            return PIIType.SSN

        # Check sample values against patterns
        if sample_values:
            str_values = [str(v) for v in sample_values if v is not None]
            for pii_type, pattern in self.PATTERNS.items():
                matches = sum(1 for v in str_values if re.search(pattern, v))
                if matches / len(str_values) > 0.5:  # >50% match
                    return pii_type

        return None

    async def scan_asset(
        self,
        asset: DataAsset,
        sample_data: pd.DataFrame
    ) -> dict[str, PIIType]:
        """Scan all columns of an asset for PII."""
        pii_columns = {}

        for col in asset.columns:
            sample_values = sample_data[col.name].dropna().head(100).tolist()
            pii_type = await self.detect(col.name, sample_values)
            if pii_type:
                pii_columns[col.name] = pii_type

        return pii_columns
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])

@router.get("/search")
async def search_catalog(
    q: str,
    types: list[AssetType] | None = None,
    domains: list[str] | None = None,
    tags: list[str] | None = None,
    owners: list[str] | None = None,
    sort: Literal["relevance", "popularity", "freshness", "name"] = "relevance",
    limit: int = 50,
    offset: int = 0
) -> SearchResults:
    """Search the data catalog."""
    pass

@router.get("/suggest")
async def get_suggestions(
    prefix: str,
    limit: int = 10
) -> list[str]:
    """Get autocomplete suggestions."""
    pass

@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: str
) -> DataAsset:
    """Get asset details."""
    pass

@router.patch("/assets/{asset_id}")
async def update_asset(
    asset_id: str,
    updates: AssetUpdate
) -> DataAsset:
    """Update asset metadata."""
    pass

@router.get("/assets/{asset_id}/profile")
async def get_asset_profile(
    asset_id: str
) -> TableProfile:
    """Get data profile for asset."""
    pass

@router.post("/assets/{asset_id}/profile")
async def refresh_profile(
    asset_id: str
) -> TableProfile:
    """Refresh data profile."""
    pass

@router.get("/assets/{asset_id}/similar")
async def get_similar_assets(
    asset_id: str,
    limit: int = 10
) -> list[DataAsset]:
    """Get similar assets."""
    pass

@router.get("/recommendations")
async def get_recommendations(
    limit: int = 10
) -> list[DataAsset]:
    """Get personalized recommendations."""
    pass

@router.get("/popular")
async def get_popular_assets(
    domain: str | None = None,
    time_range: Literal["day", "week", "month"] = "week",
    limit: int = 20
) -> list[DataAsset]:
    """Get most popular assets."""
    pass

@router.get("/glossary")
async def list_glossaries(
    domain: str | None = None
) -> list[BusinessGlossary]:
    """List business glossaries."""
    pass

@router.get("/glossary/terms/{term_id}")
async def get_term(
    term_id: str
) -> GlossaryTerm:
    """Get glossary term."""
    pass

@router.post("/glossary/terms")
async def create_term(
    term: GlossaryTermCreate
) -> GlossaryTerm:
    """Create glossary term."""
    pass

@router.get("/domains")
async def list_domains() -> list[str]:
    """List all domains."""
    pass

@router.get("/tags")
async def list_tags(
    prefix: str | None = None
) -> list[str]:
    """List all tags."""
    pass
```

---

## Package 5: Forge Federation

### Purpose

Enable cross-source queries through virtual tables, query pushdown optimization, schema mapping, and intelligent caching.

### Module Structure

```
packages/forge-federation/
├── src/
│   └── forge_federation/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── virtual_table.py   # Virtual table definition
│       │   └── mapping.py         # Schema mapping
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── planner.py         # Query planner
│       │   ├── optimizer.py       # Query optimizer
│       │   ├── executor.py        # Query executor
│       │   └── pushdown.py        # Pushdown rules
│       ├── cache/
│       │   ├── __init__.py
│       │   ├── manager.py         # Cache manager
│       │   ├── invalidation.py    # Cache invalidation
│       │   └── storage.py         # Cache storage
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── base.py            # Base adapter
│       │   ├── sql.py             # SQL databases
│       │   └── api.py             # API sources
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/virtual_table.py
from pydantic import BaseModel
from typing import Any

class VirtualColumn(BaseModel):
    name: str
    data_type: str
    source_column: str | None = None  # If mapped from source
    expression: str | None = None     # If computed
    nullable: bool = True

class VirtualTable(BaseModel):
    id: str
    name: str
    description: str | None = None

    # Source definition
    sources: list["TableSource"]

    # Schema
    columns: list[VirtualColumn]

    # Join configuration (for multi-source)
    joins: list["JoinConfig"] | None = None

    # Default filters
    default_filters: list[dict] | None = None

    # Caching
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600

    # Access control
    allowed_operations: list[str] = ["SELECT"]

class TableSource(BaseModel):
    alias: str
    connector_id: str
    table_name: str
    schema_name: str | None = None
    database_name: str | None = None

    # Column mappings
    column_mappings: dict[str, str] | None = None  # virtual_col -> source_col

class JoinConfig(BaseModel):
    left_alias: str
    right_alias: str
    join_type: Literal["inner", "left", "right", "full"] = "inner"
    conditions: list[dict]  # [{"left": "col1", "right": "col2", "op": "="}]
```

```python
# engine/planner.py
from dataclasses import dataclass
from enum import Enum
from typing import Any

class PlanNodeType(str, Enum):
    SCAN = "scan"
    FILTER = "filter"
    PROJECT = "project"
    JOIN = "join"
    AGGREGATE = "aggregate"
    SORT = "sort"
    LIMIT = "limit"
    UNION = "union"

@dataclass
class PlanNode:
    node_type: PlanNodeType
    source: str | None = None
    columns: list[str] | None = None
    predicates: list[Any] | None = None
    children: list["PlanNode"] | None = None
    metadata: dict | None = None

class QueryPlanner:
    """Convert SQL queries into execution plans."""

    def __init__(self, virtual_tables: dict[str, VirtualTable]):
        self.virtual_tables = virtual_tables

    def plan(self, sql: str) -> PlanNode:
        """Parse SQL and create execution plan."""
        from sqlglot import parse, exp

        ast = parse(sql)[0]
        return self._plan_select(ast)

    def _plan_select(self, select: exp.Select) -> PlanNode:
        """Plan a SELECT statement."""
        # Start with source scans
        from_clause = select.find(exp.From)
        scan_nodes = self._plan_from(from_clause)

        # Apply joins
        if len(scan_nodes) > 1:
            current = self._plan_joins(scan_nodes, select)
        else:
            current = scan_nodes[0]

        # Apply WHERE
        where = select.find(exp.Where)
        if where:
            current = PlanNode(
                node_type=PlanNodeType.FILTER,
                predicates=self._extract_predicates(where),
                children=[current]
            )

        # Apply GROUP BY / aggregations
        group = select.find(exp.Group)
        if group or self._has_aggregations(select):
            current = PlanNode(
                node_type=PlanNodeType.AGGREGATE,
                columns=self._extract_group_columns(group),
                metadata={"aggregations": self._extract_aggregations(select)},
                children=[current]
            )

        # Apply projection
        current = PlanNode(
            node_type=PlanNodeType.PROJECT,
            columns=self._extract_select_columns(select),
            children=[current]
        )

        # Apply ORDER BY
        order = select.find(exp.Order)
        if order:
            current = PlanNode(
                node_type=PlanNodeType.SORT,
                metadata={"order_by": self._extract_order(order)},
                children=[current]
            )

        # Apply LIMIT
        limit = select.find(exp.Limit)
        if limit:
            current = PlanNode(
                node_type=PlanNodeType.LIMIT,
                metadata={"limit": int(limit.this.this)},
                children=[current]
            )

        return current
```

```python
# engine/optimizer.py
class QueryOptimizer:
    """Optimize query execution plans."""

    def __init__(self, adapters: dict[str, "SourceAdapter"]):
        self.adapters = adapters

    def optimize(self, plan: PlanNode) -> PlanNode:
        """Apply optimization rules to plan."""
        # Rule 1: Predicate pushdown
        plan = self._pushdown_predicates(plan)

        # Rule 2: Projection pushdown
        plan = self._pushdown_projections(plan)

        # Rule 3: Join reordering (small tables first)
        plan = self._reorder_joins(plan)

        # Rule 4: Limit pushdown
        plan = self._pushdown_limits(plan)

        return plan

    def _pushdown_predicates(self, plan: PlanNode) -> PlanNode:
        """Push filter predicates down to source scans."""
        if plan.node_type == PlanNodeType.FILTER:
            child = plan.children[0]

            if child.node_type == PlanNodeType.SCAN:
                # Check if source supports this predicate
                adapter = self.adapters[child.source]
                pushable, remaining = self._split_predicates(
                    plan.predicates,
                    adapter.supported_predicates
                )

                if pushable:
                    # Add predicates to scan node
                    child.predicates = (child.predicates or []) + pushable

                if remaining:
                    plan.predicates = remaining
                    plan.children = [child]
                else:
                    # All predicates pushed, remove filter node
                    return child

        # Recurse
        if plan.children:
            plan.children = [self._pushdown_predicates(c) for c in plan.children]

        return plan

    def _pushdown_projections(self, plan: PlanNode) -> PlanNode:
        """Push column projections down to reduce data transfer."""
        required_columns = self._collect_required_columns(plan)
        return self._apply_projection_pushdown(plan, required_columns)
```

```python
# engine/executor.py
import asyncio
from typing import AsyncIterator
import pandas as pd

class FederatedExecutor:
    """Execute federated query plans."""

    def __init__(
        self,
        adapters: dict[str, "SourceAdapter"],
        cache: "CacheManager"
    ):
        self.adapters = adapters
        self.cache = cache

    async def execute(
        self,
        plan: PlanNode,
        parameters: dict | None = None
    ) -> pd.DataFrame:
        """Execute a query plan."""
        return await self._execute_node(plan, parameters)

    async def _execute_node(
        self,
        node: PlanNode,
        parameters: dict | None
    ) -> pd.DataFrame:
        """Execute a single plan node."""
        if node.node_type == PlanNodeType.SCAN:
            return await self._execute_scan(node, parameters)

        elif node.node_type == PlanNodeType.FILTER:
            child_result = await self._execute_node(node.children[0], parameters)
            return self._apply_filter(child_result, node.predicates)

        elif node.node_type == PlanNodeType.PROJECT:
            child_result = await self._execute_node(node.children[0], parameters)
            return child_result[node.columns]

        elif node.node_type == PlanNodeType.JOIN:
            # Execute children in parallel
            left_task = self._execute_node(node.children[0], parameters)
            right_task = self._execute_node(node.children[1], parameters)
            left_result, right_result = await asyncio.gather(left_task, right_task)

            return self._apply_join(
                left_result,
                right_result,
                node.metadata["join_config"]
            )

        elif node.node_type == PlanNodeType.AGGREGATE:
            child_result = await self._execute_node(node.children[0], parameters)
            return self._apply_aggregation(
                child_result,
                node.columns,
                node.metadata["aggregations"]
            )

        elif node.node_type == PlanNodeType.SORT:
            child_result = await self._execute_node(node.children[0], parameters)
            return self._apply_sort(child_result, node.metadata["order_by"])

        elif node.node_type == PlanNodeType.LIMIT:
            child_result = await self._execute_node(node.children[0], parameters)
            return child_result.head(node.metadata["limit"])

    async def _execute_scan(
        self,
        node: PlanNode,
        parameters: dict | None
    ) -> pd.DataFrame:
        """Execute a source scan, with caching."""
        cache_key = self._compute_cache_key(node, parameters)

        # Check cache
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Execute against source
        adapter = self.adapters[node.source]
        result = await adapter.scan(
            table=node.metadata["table"],
            columns=node.columns,
            predicates=node.predicates,
            parameters=parameters
        )

        # Cache result
        await self.cache.set(cache_key, result, ttl=node.metadata.get("cache_ttl", 3600))

        return result
```

```python
# cache/manager.py
import hashlib
import pickle
from datetime import datetime, timedelta
import redis.asyncio as redis

class CacheManager:
    """Manage query result caching."""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.prefix = "forge:federation:cache:"

    async def get(self, key: str) -> pd.DataFrame | None:
        """Get cached result."""
        data = await self.redis.get(self.prefix + key)
        if data:
            return pickle.loads(data)
        return None

    async def set(
        self,
        key: str,
        data: pd.DataFrame,
        ttl: int = 3600
    ):
        """Cache a result."""
        serialized = pickle.dumps(data)
        await self.redis.setex(
            self.prefix + key,
            ttl,
            serialized
        )

    async def invalidate(self, pattern: str):
        """Invalidate cached entries matching pattern."""
        async for key in self.redis.scan_iter(match=self.prefix + pattern):
            await self.redis.delete(key)

    async def invalidate_for_source(self, source_id: str):
        """Invalidate all cache entries for a source."""
        await self.invalidate(f"*:{source_id}:*")

class CacheInvalidator:
    """Handle cache invalidation triggers."""

    def __init__(self, cache: CacheManager):
        self.cache = cache

    async def on_source_update(self, source_id: str, table: str):
        """Invalidate cache when source data changes."""
        await self.cache.invalidate_for_source(source_id)

    async def on_schema_change(self, source_id: str, table: str):
        """Invalidate cache on schema changes."""
        await self.cache.invalidate(f"*:{source_id}:{table}:*")
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/federation", tags=["federation"])

@router.get("/virtual-tables")
async def list_virtual_tables() -> list[VirtualTable]:
    """List all virtual tables."""
    pass

@router.post("/virtual-tables")
async def create_virtual_table(
    table: VirtualTableCreate
) -> VirtualTable:
    """Create a virtual table."""
    pass

@router.get("/virtual-tables/{table_id}")
async def get_virtual_table(
    table_id: str
) -> VirtualTable:
    """Get virtual table definition."""
    pass

@router.patch("/virtual-tables/{table_id}")
async def update_virtual_table(
    table_id: str,
    updates: VirtualTableUpdate
) -> VirtualTable:
    """Update virtual table."""
    pass

@router.delete("/virtual-tables/{table_id}")
async def delete_virtual_table(
    table_id: str
) -> dict:
    """Delete virtual table."""
    pass

@router.post("/query")
async def execute_query(
    sql: str,
    parameters: dict | None = None,
    explain: bool = False
) -> QueryResult:
    """Execute a federated query."""
    pass

@router.post("/query/explain")
async def explain_query(
    sql: str
) -> QueryPlan:
    """Get execution plan for query."""
    pass

@router.post("/cache/invalidate")
async def invalidate_cache(
    source_id: str | None = None,
    table: str | None = None
) -> dict:
    """Manually invalidate cache entries."""
    pass

@router.get("/cache/stats")
async def get_cache_stats() -> CacheStats:
    """Get cache statistics."""
    pass
```

---

## Package 6-9: Transforms

### Transforms Core

```python
# packages/transforms-core/src/forge_transforms/engine.py
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

class TransformEngine(str, Enum):
    SPARK = "spark"
    FLINK = "flink"
    DATAFUSION = "datafusion"
    PYTHON = "python"

class BaseTransform(ABC):
    """Base class for all transforms."""

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        self.name = name
        self.config = config or {}

    @property
    @abstractmethod
    def engine(self) -> TransformEngine:
        pass

    @abstractmethod
    async def execute(
        self,
        inputs: dict[str, "DataFrame"],
        context: "TransformContext"
    ) -> "DataFrame":
        pass

class TransformContext:
    """Runtime context for transform execution."""

    def __init__(
        self,
        run_id: str,
        parameters: dict[str, Any],
        secrets: dict[str, str],
        lineage_collector: "LineageCollector"
    ):
        self.run_id = run_id
        self.parameters = parameters
        self.secrets = secrets
        self.lineage = lineage_collector

class TransformRegistry:
    """Registry for transform implementations."""

    _transforms: dict[str, type[BaseTransform]] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(transform_cls: type[BaseTransform]):
            cls._transforms[name] = transform_cls
            return transform_cls
        return decorator

    @classmethod
    def get(cls, name: str) -> type[BaseTransform]:
        return cls._transforms[name]
```

### Transforms Spark

```python
# packages/transforms-spark/src/forge_transforms_spark/transform.py
from pyspark.sql import SparkSession, DataFrame
from forge_transforms import BaseTransform, TransformEngine

class SparkTransform(BaseTransform):
    """Spark-based transform."""

    @property
    def engine(self) -> TransformEngine:
        return TransformEngine.SPARK

    def __init__(self, name: str, spark: SparkSession, config: dict | None = None):
        super().__init__(name, config)
        self.spark = spark

@TransformRegistry.register("spark_sql")
class SparkSQLTransform(SparkTransform):
    """Execute SQL against Spark DataFrames."""

    async def execute(
        self,
        inputs: dict[str, DataFrame],
        context: "TransformContext"
    ) -> DataFrame:
        sql = self.config["sql"]

        # Register input DataFrames as temp views
        for name, df in inputs.items():
            df.createOrReplaceTempView(name)

        # Execute SQL
        result = self.spark.sql(sql)

        # Record lineage
        context.lineage.record_sql_transform(sql, inputs.keys(), self.name)

        return result

@TransformRegistry.register("spark_python")
class SparkPythonTransform(SparkTransform):
    """Execute Python function against Spark DataFrames."""

    async def execute(
        self,
        inputs: dict[str, DataFrame],
        context: "TransformContext"
    ) -> DataFrame:
        func_code = self.config["code"]

        # Create function namespace
        namespace = {
            "spark": self.spark,
            "inputs": inputs,
            "params": context.parameters,
            **inputs  # Allow direct access to DataFrames by name
        }

        # Execute transform code
        exec(func_code, namespace)

        return namespace.get("output", namespace.get("result"))
```

### Transforms Flink

```python
# packages/transforms-flink/src/forge_transforms_flink/transform.py
from pyflink.table import TableEnvironment
from pyflink.datastream import StreamExecutionEnvironment
from forge_transforms import BaseTransform, TransformEngine

class FlinkStreamTransform(BaseTransform):
    """Flink streaming transform."""

    @property
    def engine(self) -> TransformEngine:
        return TransformEngine.FLINK

    def __init__(
        self,
        name: str,
        env: StreamExecutionEnvironment,
        table_env: TableEnvironment,
        config: dict | None = None
    ):
        super().__init__(name, config)
        self.env = env
        self.table_env = table_env

@TransformRegistry.register("flink_sql")
class FlinkSQLTransform(FlinkStreamTransform):
    """Execute streaming SQL with Flink."""

    async def execute(
        self,
        inputs: dict[str, "Table"],
        context: "TransformContext"
    ) -> "Table":
        sql = self.config["sql"]

        # Register input tables
        for name, table in inputs.items():
            self.table_env.create_temporary_view(name, table)

        # Execute streaming SQL
        result = self.table_env.sql_query(sql)

        return result

@TransformRegistry.register("flink_window")
class FlinkWindowTransform(FlinkStreamTransform):
    """Window-based streaming aggregation."""

    async def execute(
        self,
        inputs: dict[str, "Table"],
        context: "TransformContext"
    ) -> "Table":
        window_type = self.config.get("window_type", "tumbling")
        window_size = self.config["window_size"]
        group_by = self.config.get("group_by", [])
        aggregations = self.config["aggregations"]

        input_table = list(inputs.values())[0]

        if window_type == "tumbling":
            window = Tumble.over(lit(window_size).seconds).on(col("event_time")).alias("w")
        elif window_type == "sliding":
            slide = self.config["slide"]
            window = Slide.over(lit(window_size).seconds).every(lit(slide).seconds).on(col("event_time")).alias("w")
        elif window_type == "session":
            gap = self.config["session_gap"]
            window = Session.with_gap(lit(gap).seconds).on(col("event_time")).alias("w")

        # Apply window aggregation
        result = input_table.window(window).group_by(*group_by, col("w"))

        for agg_name, agg_config in aggregations.items():
            result = result.select(
                *group_by,
                col("w").start.alias("window_start"),
                col("w").end.alias("window_end"),
                self._apply_aggregation(agg_config).alias(agg_name)
            )

        return result
```

### Transforms DataFusion

```python
# packages/transforms-datafusion/src/forge_transforms_datafusion/transform.py
import datafusion
from datafusion import SessionContext, DataFrame
from forge_transforms import BaseTransform, TransformEngine

class DataFusionTransform(BaseTransform):
    """Fast SQL transforms using Apache DataFusion (Rust)."""

    @property
    def engine(self) -> TransformEngine:
        return TransformEngine.DATAFUSION

    def __init__(self, name: str, config: dict | None = None):
        super().__init__(name, config)
        self.ctx = SessionContext()

@TransformRegistry.register("datafusion_sql")
class DataFusionSQLTransform(DataFusionTransform):
    """Execute SQL using DataFusion."""

    async def execute(
        self,
        inputs: dict[str, "pyarrow.Table"],
        context: "TransformContext"
    ) -> "pyarrow.Table":
        sql = self.config["sql"]

        # Register input tables
        for name, table in inputs.items():
            self.ctx.register_record_batch(name, table.to_batches())

        # Execute SQL (async native)
        result = await self.ctx.sql(sql).collect()

        return result
```

---

## Implementation Roadmap

### Phase B1: Quality + Lineage (Weeks 1-3)

**Goals:**
- Core quality check framework
- Basic lineage collection and visualization
- Integration with existing pipelines

**Deliverables:**
1. forge-quality package with 8 check types
2. forge-lineage package with SQL and Dagster collectors
3. API endpoints for both packages
4. UI components for quality dashboard and lineage graph

**Acceptance Criteria:**
- [ ] Can create and run quality monitors
- [ ] Can visualize column-level lineage
- [ ] Can perform impact analysis
- [ ] Alerts dispatch to Slack/email

### Phase B2: Streaming Transforms (Weeks 4-5)

**Goals:**
- Flink integration for streaming
- Window-based aggregations
- CDC processing

**Deliverables:**
1. transforms-flink package
2. Window transform operators
3. CDC event processing
4. Streaming lineage collection

**Acceptance Criteria:**
- [ ] Can process Kafka streams with Flink
- [ ] Tumbling, sliding, session windows work
- [ ] CDC events trigger downstream updates

### Phase B3: Branches + Federation (Weeks 6-8)

**Goals:**
- Git-like data versioning
- Federated query engine
- Time travel queries

**Deliverables:**
1. forge-branches package with Iceberg backend
2. forge-federation package with query planner
3. Branch UI (create, merge, compare)
4. Federation query builder UI

**Acceptance Criteria:**
- [ ] Can create branches and merge with conflict resolution
- [ ] Can query across multiple data sources
- [ ] Time travel queries work
- [ ] Query pushdown optimization works

### Phase B4: Navigator (Weeks 9-10)

**Goals:**
- Full data catalog
- Search and discovery
- Data profiling

**Deliverables:**
1. forge-navigator package
2. Elasticsearch-based search
3. Profiling and PII detection
4. Recommendation engine

**Acceptance Criteria:**
- [ ] Can search catalog with faceted filters
- [ ] Assets have automated profiles
- [ ] PII is automatically detected
- [ ] Recommendations are personalized

---

## Integration Points

### With Forge Connect (Track A)

- Lineage collection from connector sync jobs
- Quality checks on ingested data
- Schema discovery feeds Navigator

### With Forge AI (Track C)

- Navigator provides context for AI queries
- Quality metrics used in AI training data validation
- Lineage helps explain AI outputs

### With Forge Studio (Track D)

- Virtual tables as data sources for apps
- Quality dashboards as Studio widgets
- Lineage visualization component

### With Existing Packages

- **api**: All packages expose routes via FastAPI
- **pipelines**: Dagster integration for transforms and lineage
- **ontology**: Navigator catalogs ontology objects

---

## Security Considerations

1. **Data Access**: Federation respects source-level permissions
2. **PII Handling**: Navigator flags sensitive columns
3. **Audit Trail**: All queries logged for compliance
4. **Branch Permissions**: Protected branches require approval
5. **Cache Security**: Cached results inherit source permissions

---

## Appendix: Database Schema

### Quality Tables

```sql
CREATE TABLE quality_monitors (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    dataset_id VARCHAR(255) NOT NULL,
    checks JSONB NOT NULL,
    schedule JSONB NOT NULL,
    alerting JSONB,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE quality_results (
    id UUID PRIMARY KEY,
    monitor_id UUID REFERENCES quality_monitors(id),
    check_id VARCHAR(255) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    passed BOOLEAN NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT,
    details JSONB,
    executed_at TIMESTAMPTZ NOT NULL,
    execution_ms INTEGER
);

CREATE INDEX idx_quality_results_monitor ON quality_results(monitor_id, executed_at DESC);
```

### Lineage Tables

```sql
CREATE TABLE lineage_nodes (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    qualified_name VARCHAR(1024) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE lineage_edges (
    id VARCHAR(255) PRIMARY KEY,
    source_id VARCHAR(255) REFERENCES lineage_nodes(id),
    target_id VARCHAR(255) REFERENCES lineage_nodes(id),
    edge_type VARCHAR(50) NOT NULL,
    transformation VARCHAR(50),
    expression TEXT,
    confidence FLOAT DEFAULT 1.0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lineage_edges_source ON lineage_edges(source_id);
CREATE INDEX idx_lineage_edges_target ON lineage_edges(target_id);
```

### Branches Tables

```sql
CREATE TABLE data_branches (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    dataset_id VARCHAR(255) NOT NULL,
    parent_branch_id VARCHAR(255),
    parent_commit_id VARCHAR(255),
    head_commit_id VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    protected BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(dataset_id, name)
);

CREATE TABLE data_commits (
    id VARCHAR(255) PRIMARY KEY,
    dataset_id VARCHAR(255) NOT NULL,
    branch_id VARCHAR(255) REFERENCES data_branches(id),
    parent_ids VARCHAR(255)[],
    message TEXT,
    author VARCHAR(255),
    snapshot_id VARCHAR(255) NOT NULL,
    stats JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

### Navigator Tables

```sql
CREATE TABLE catalog_assets (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    qualified_name VARCHAR(1024) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    columns JSONB,
    owner_id VARCHAR(255),
    owner_team VARCHAR(255),
    tags VARCHAR(255)[],
    classification VARCHAR(50),
    domain VARCHAR(255),
    source_system VARCHAR(255),
    source_location VARCHAR(1024),
    row_count BIGINT,
    byte_size BIGINT,
    quality_score FLOAT,
    view_count INTEGER DEFAULT 0,
    query_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ
);

CREATE INDEX idx_catalog_assets_type ON catalog_assets(type);
CREATE INDEX idx_catalog_assets_domain ON catalog_assets(domain);
CREATE INDEX idx_catalog_assets_owner ON catalog_assets(owner_id);
CREATE INDEX idx_catalog_assets_tags ON catalog_assets USING GIN(tags);

CREATE TABLE glossary_terms (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    definition TEXT NOT NULL,
    domain VARCHAR(255),
    synonyms VARCHAR(255)[],
    related_terms UUID[],
    owner_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Federation Tables

```sql
CREATE TABLE virtual_tables (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    sources JSONB NOT NULL,
    columns JSONB NOT NULL,
    joins JSONB,
    default_filters JSONB,
    cache_enabled BOOLEAN DEFAULT TRUE,
    cache_ttl_seconds INTEGER DEFAULT 3600,
    allowed_operations VARCHAR(50)[] DEFAULT ARRAY['SELECT'],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```
