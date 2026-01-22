"""
Forge Transforms Engine Module

Provides the execution engine abstraction and DataFusion implementation
for running data transformations.
"""

from forge_transforms.engine.protocol import TransformEngine, ExecutionResult, ExecutionConfig
from forge_transforms.engine.datafusion import DataFusionEngine
from forge_transforms.engine.context import SessionContext, SessionConfig
from forge_transforms.engine.udf import UserDefinedFunction, UDFRegistry, ScalarUDF, AggregateUDF

__all__ = [
    # Protocol
    "TransformEngine",
    "ExecutionResult",
    "ExecutionConfig",
    # DataFusion implementation
    "DataFusionEngine",
    # Context
    "SessionContext",
    "SessionConfig",
    # UDFs
    "UserDefinedFunction",
    "UDFRegistry",
    "ScalarUDF",
    "AggregateUDF",
]
