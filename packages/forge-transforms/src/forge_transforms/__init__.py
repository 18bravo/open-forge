"""
Forge Transforms - Data Transformation Engine

This package provides data transformation capabilities for the Open Forge
platform using Apache DataFusion. Per the consolidated architecture
(2026-01-21), this replaces the original multi-engine approach with a
DataFusion-only implementation for MVP. Spark and Flink support is deferred.

## Package Structure

1. **engine/** - DataFusion execution engine, session context management,
   and user-defined functions
2. **transforms/** - Transform definitions including SQL transforms,
   expression-based transforms, and aggregations
3. **incremental/** - Incremental processing engine with watermark tracking
   and state checkpointing

## Key Features

### DataFusion-Based Execution
Uses Apache DataFusion for high-performance, Rust-based query execution
with full SQL support and Arrow-native data handling.

```python
from forge_transforms import DataFusionEngine, SQLTransform, SQLTransformConfig

# Create engine
engine = DataFusionEngine()
await engine.initialize()

# Create and execute transform
config = SQLTransformConfig(
    transform_id="filter_active",
    sql="SELECT * FROM input WHERE status = 'active'",
)
transform = SQLTransform(config)
result = await transform.execute(engine, input_data)
```

### Expression-Based Transforms
Build transforms programmatically using expression trees:

```python
from forge_transforms import (
    ExpressionTransform,
    ExpressionTransformConfig,
    ColumnExpression,
    FunctionExpression,
    LiteralExpression,
)

config = ExpressionTransformConfig(
    transform_id="calc_total",
    select_expressions={
        "id": ColumnExpression("id"),
        "total": FunctionExpression("*",
            ColumnExpression("price"),
            ColumnExpression("quantity")
        ),
    },
)
```

### Incremental Processing
Process data incrementally with checkpoint support:

```python
from forge_transforms import IncrementalProcessor, IncrementalConfig

config = IncrementalConfig(
    processor_id="sales_incremental",
    watermark_column="created_at",
    checkpoint_interval=5000,
)
processor = IncrementalProcessor(config)
result = await processor.process(engine, transform, "raw_sales")
```

## Architecture Notes

This package is part of the consolidated Open Forge architecture that
reduced 64 packages to 20. It replaces:
- transforms-core
- transforms-spark (deferred)
- transforms-flink (deferred)
- transforms-datafusion

See docs/plans/2026-01-21-consolidated-architecture.md for details.
"""

__version__ = "0.1.0"

# Engine exports
from forge_transforms.engine import (
    TransformEngine,
    ExecutionResult,
    ExecutionConfig,
    DataFusionEngine,
    SessionContext,
    SessionConfig,
    UserDefinedFunction,
    UDFRegistry,
    ScalarUDF,
    AggregateUDF,
)

# Transform exports
from forge_transforms.transforms import (
    Transform,
    TransformConfig,
    TransformResult,
    TransformStatus,
    SQLTransform,
    SQLTransformConfig,
    ExpressionTransform,
    Expression,
    ColumnExpression,
    LiteralExpression,
    FunctionExpression,
    AggregateTransform,
    AggregateConfig,
    AggregateFunction,
)

# Incremental processing exports
from forge_transforms.incremental import (
    IncrementalProcessor,
    IncrementalConfig,
    ProcessingMode,
    WatermarkStrategy,
    Checkpoint,
    CheckpointStore,
    FileCheckpointStore,
    MemoryCheckpointStore,
    CheckpointMetadata,
)

__all__ = [
    # Version
    "__version__",
    # Engine
    "TransformEngine",
    "ExecutionResult",
    "ExecutionConfig",
    "DataFusionEngine",
    "SessionContext",
    "SessionConfig",
    "UserDefinedFunction",
    "UDFRegistry",
    "ScalarUDF",
    "AggregateUDF",
    # Transforms
    "Transform",
    "TransformConfig",
    "TransformResult",
    "TransformStatus",
    "SQLTransform",
    "SQLTransformConfig",
    "ExpressionTransform",
    "Expression",
    "ColumnExpression",
    "LiteralExpression",
    "FunctionExpression",
    "AggregateTransform",
    "AggregateConfig",
    "AggregateFunction",
    # Incremental
    "IncrementalProcessor",
    "IncrementalConfig",
    "ProcessingMode",
    "WatermarkStrategy",
    "Checkpoint",
    "CheckpointStore",
    "FileCheckpointStore",
    "MemoryCheckpointStore",
    "CheckpointMetadata",
]
