"""
Lineage query with bounded traversal limits.

CRITICAL: This module implements bounded query limits to prevent
unbounded graph traversal (P2 finding from architecture review).

Default limits:
- MAX_DEPTH = 10: Maximum traversal depth
- MAX_NODES = 1000: Maximum nodes in result
- TIMEOUT = 30 seconds: Maximum query execution time
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from forge_data.lineage.graph import EdgeType, LineageEdge, LineageGraph, LineageNode


class TraversalDirection(str, Enum):
    """Direction of lineage traversal."""

    UPSTREAM = "upstream"  # Find sources
    DOWNSTREAM = "downstream"  # Find dependents
    BOTH = "both"  # Find both


class QueryLimitExceeded(Exception):
    """Raised when a query exceeds configured limits."""

    def __init__(self, limit_type: str, limit_value: int, message: str):
        self.limit_type = limit_type
        self.limit_value = limit_value
        super().__init__(message)


@dataclass
class LineageQueryResult:
    """
    Result of a lineage query.

    Includes the resulting subgraph plus metadata about the query execution.
    """

    graph: LineageGraph
    root_node_id: str
    direction: TraversalDirection
    depth_reached: int
    nodes_visited: int
    execution_ms: int
    truncated: bool = False  # True if limits were hit
    truncation_reason: str | None = None


@dataclass
class LineageQuery:
    """
    Bounded lineage query configuration.

    IMPORTANT: This class enforces limits to prevent unbounded graph traversal,
    which was identified as a P2 security/performance finding in architecture review.

    Default limits (from consolidated architecture spec):
    - max_depth: 10 - Prevents infinite recursion in cyclic graphs
    - max_nodes: 1000 - Limits memory usage and response size
    - timeout: 30 seconds - Prevents long-running queries

    Example:
        query = LineageQuery(
            root_node_id="dataset.table.column",
            direction=TraversalDirection.UPSTREAM,
            max_depth=5,  # Override default
        )
        result = await query.execute(graph)

        if result.truncated:
            logger.warning(f"Query truncated: {result.truncation_reason}")
    """

    root_node_id: str
    direction: TraversalDirection = TraversalDirection.UPSTREAM
    edge_types: list[EdgeType] | None = None  # None means all types

    # Bounded limits - CRITICAL for preventing unbounded traversal
    max_depth: int = 10  # Default from architecture spec
    max_nodes: int = 1000  # Default from architecture spec
    timeout: timedelta = field(default_factory=lambda: timedelta(seconds=30))

    # Optional filters
    node_types: list[str] | None = None
    metadata_filters: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate query parameters."""
        if self.max_depth < 1:
            raise ValueError("max_depth must be at least 1")
        if self.max_nodes < 1:
            raise ValueError("max_nodes must be at least 1")
        if self.timeout.total_seconds() < 1:
            raise ValueError("timeout must be at least 1 second")

        # Enforce maximum limits to prevent abuse
        if self.max_depth > 100:
            raise ValueError("max_depth cannot exceed 100")
        if self.max_nodes > 10000:
            raise ValueError("max_nodes cannot exceed 10000")
        if self.timeout.total_seconds() > 300:
            raise ValueError("timeout cannot exceed 300 seconds")

    async def execute(self, graph: LineageGraph) -> LineageQueryResult:
        """
        Execute the lineage query with bounded traversal.

        Args:
            graph: The lineage graph to query

        Returns:
            LineageQueryResult with the subgraph and execution metadata

        Raises:
            QueryLimitExceeded: If query is forcefully stopped (only in strict mode)
        """
        start_time = datetime.utcnow()
        deadline = start_time + self.timeout

        result_graph = LineageGraph()
        visited: set[str] = set()
        depth_reached = 0
        truncated = False
        truncation_reason: str | None = None

        # Get root node
        root_node = graph.get_node(self.root_node_id)
        if root_node is None:
            return LineageQueryResult(
                graph=result_graph,
                root_node_id=self.root_node_id,
                direction=self.direction,
                depth_reached=0,
                nodes_visited=0,
                execution_ms=0,
                truncated=False,
            )

        result_graph.add_node(root_node)
        visited.add(self.root_node_id)

        # BFS traversal with depth tracking
        current_level = [self.root_node_id]
        current_depth = 0

        while current_level and current_depth < self.max_depth:
            # Check timeout
            if datetime.utcnow() > deadline:
                truncated = True
                truncation_reason = f"Timeout exceeded ({self.timeout.total_seconds()}s)"
                break

            # Check node limit
            if len(visited) >= self.max_nodes:
                truncated = True
                truncation_reason = f"Node limit exceeded ({self.max_nodes} nodes)"
                break

            next_level: list[str] = []
            current_depth += 1

            for node_id in current_level:
                # Get edges based on direction
                if self.direction in (TraversalDirection.UPSTREAM, TraversalDirection.BOTH):
                    for edge in graph.get_incoming_edges(node_id):
                        if self._edge_matches(edge) and edge.source_id not in visited:
                            if len(visited) >= self.max_nodes:
                                truncated = True
                                truncation_reason = f"Node limit exceeded ({self.max_nodes} nodes)"
                                break

                            source_node = graph.get_node(edge.source_id)
                            if source_node and self._node_matches(source_node):
                                result_graph.add_node(source_node)
                                result_graph.add_edge(edge)
                                visited.add(edge.source_id)
                                next_level.append(edge.source_id)

                if self.direction in (TraversalDirection.DOWNSTREAM, TraversalDirection.BOTH):
                    for edge in graph.get_outgoing_edges(node_id):
                        if self._edge_matches(edge) and edge.target_id not in visited:
                            if len(visited) >= self.max_nodes:
                                truncated = True
                                truncation_reason = f"Node limit exceeded ({self.max_nodes} nodes)"
                                break

                            target_node = graph.get_node(edge.target_id)
                            if target_node and self._node_matches(target_node):
                                result_graph.add_node(target_node)
                                result_graph.add_edge(edge)
                                visited.add(edge.target_id)
                                next_level.append(edge.target_id)

                if truncated:
                    break

            if truncated:
                break

            if next_level:
                depth_reached = current_depth
            current_level = next_level

            # Yield to event loop periodically for responsiveness
            await asyncio.sleep(0)

        execution_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return LineageQueryResult(
            graph=result_graph,
            root_node_id=self.root_node_id,
            direction=self.direction,
            depth_reached=depth_reached,
            nodes_visited=len(visited),
            execution_ms=execution_ms,
            truncated=truncated,
            truncation_reason=truncation_reason,
        )

    def _edge_matches(self, edge: LineageEdge) -> bool:
        """Check if an edge matches the query filters."""
        if self.edge_types is None:
            return True
        return edge.edge_type in self.edge_types

    def _node_matches(self, node: LineageNode) -> bool:
        """Check if a node matches the query filters."""
        if self.node_types is not None:
            if node.type.value not in self.node_types:
                return False

        if self.metadata_filters is not None:
            for key, value in self.metadata_filters.items():
                if node.metadata.get(key) != value:
                    return False

        return True


def create_bounded_query(
    root_node_id: str,
    direction: TraversalDirection = TraversalDirection.UPSTREAM,
    max_depth: int | None = None,
    max_nodes: int | None = None,
    timeout_seconds: int | None = None,
) -> LineageQuery:
    """
    Factory function to create a bounded lineage query with sensible defaults.

    This ensures all queries have limits even if not explicitly specified.

    Args:
        root_node_id: Starting node for traversal
        direction: Direction to traverse
        max_depth: Maximum depth (default: 10)
        max_nodes: Maximum nodes (default: 1000)
        timeout_seconds: Timeout in seconds (default: 30)

    Returns:
        Configured LineageQuery with bounded limits
    """
    return LineageQuery(
        root_node_id=root_node_id,
        direction=direction,
        max_depth=max_depth or 10,
        max_nodes=max_nodes or 1000,
        timeout=timedelta(seconds=timeout_seconds or 30),
    )
