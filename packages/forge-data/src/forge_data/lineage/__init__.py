"""
Forge Data Lineage Module

Provides lineage graph tracking with bounded traversal limits,
automatic capture, and impact analysis.

IMPORTANT: This module implements bounded query limits to prevent
unbounded graph traversal (P2 finding from architecture review):
- MAX_DEPTH = 10 (default)
- MAX_NODES = 1000 (default)
- TIMEOUT = 30 seconds (default)
"""

from forge_data.lineage.graph import (
    LineageGraph,
    LineageNode,
    LineageEdge,
    NodeType,
    EdgeType,
)
from forge_data.lineage.query import LineageQuery, LineageQueryResult
from forge_data.lineage.tracker import LineageTracker
from forge_data.lineage.impact import ImpactAnalyzer, ImpactReport

__all__ = [
    # Graph primitives
    "LineageGraph",
    "LineageNode",
    "LineageEdge",
    "NodeType",
    "EdgeType",
    # Query with bounded limits
    "LineageQuery",
    "LineageQueryResult",
    # Tracking
    "LineageTracker",
    # Impact analysis
    "ImpactAnalyzer",
    "ImpactReport",
]
