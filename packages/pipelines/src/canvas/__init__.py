"""
Pipeline Canvas module for Open Forge.

This module provides visual canvas support for designing data pipelines
that compile to Dagster assets. It bridges the React Flow canvas UI
with Dagster's asset-based execution model.

Components:
- PipelineCanvasCompiler: Compiles canvas nodes/edges to Dagster Definitions
- PipelineCanvasGenerator: Generates canvas layouts from ontology definitions
"""

from canvas.compiler import (
    PipelineCanvasCompiler,
    CanvasNode,
    CanvasEdge,
    CompilationResult,
)
from canvas.generator import (
    PipelineCanvasGenerator,
    CanvasLayout,
)

__all__ = [
    # Compiler
    "PipelineCanvasCompiler",
    "CanvasNode",
    "CanvasEdge",
    "CompilationResult",
    # Generator
    "PipelineCanvasGenerator",
    "CanvasLayout",
]
