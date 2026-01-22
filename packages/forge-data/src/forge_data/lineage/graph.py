"""
Lineage graph data structures.

Provides the core data structures for representing data lineage:
nodes (datasets, columns, transforms) and edges (derivation relationships).
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of nodes in the lineage graph."""

    DATASET = "dataset"
    TABLE = "table"
    COLUMN = "column"
    TRANSFORM = "transform"
    PIPELINE = "pipeline"
    EXTERNAL = "external"
    MODEL = "model"


class EdgeType(str, Enum):
    """Types of edges in the lineage graph."""

    DERIVES_FROM = "derives_from"  # A is computed from B
    CONTAINS = "contains"  # Table contains column
    EXECUTES = "executes"  # Pipeline executes transform
    PRODUCES = "produces"  # Transform produces output
    CONSUMES = "consumes"  # Transform consumes input


class TransformationType(str, Enum):
    """Type of transformation between nodes."""

    DIRECT = "direct"  # 1:1 mapping
    AGGREGATION = "aggregation"  # Many:1
    FILTER = "filter"  # Subset
    JOIN = "join"  # Multiple sources
    UNION = "union"  # Combine
    EXPRESSION = "expression"  # Calculated
    UNKNOWN = "unknown"


class LineageNode(BaseModel):
    """
    A node in the lineage graph.

    Represents a data asset: dataset, table, column, transform, etc.
    """

    id: str
    type: NodeType
    name: str
    qualified_name: str  # Full path: database.schema.table.column
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # For columns
    data_type: str | None = None
    nullable: bool | None = None

    # For transforms
    transform_type: str | None = None
    code: str | None = None

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LineageNode):
            return False
        return self.id == other.id


class LineageEdge(BaseModel):
    """
    An edge in the lineage graph.

    Represents a relationship between two nodes, typically a data derivation.
    """

    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    transformation: TransformationType = TransformationType.UNKNOWN
    expression: str | None = None  # SQL/code that defines the transform
    confidence: float = 1.0  # For inferred lineage
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def __hash__(self) -> int:
        return hash(self.id)


class LineageGraph:
    """
    In-memory lineage graph with traversal operations.

    This class provides the data structure for storing lineage information.
    For querying with bounded limits, use LineageQuery.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, LineageNode] = {}
        self._edges: dict[str, LineageEdge] = {}
        self._outgoing: dict[str, set[str]] = {}  # node_id -> edge_ids
        self._incoming: dict[str, set[str]] = {}  # node_id -> edge_ids

    def add_node(self, node: LineageNode) -> None:
        """Add a node to the graph."""
        self._nodes[node.id] = node
        self._outgoing.setdefault(node.id, set())
        self._incoming.setdefault(node.id, set())

    def add_edge(self, edge: LineageEdge) -> None:
        """Add an edge to the graph."""
        self._edges[edge.id] = edge
        self._outgoing.setdefault(edge.source_id, set()).add(edge.id)
        self._incoming.setdefault(edge.target_id, set()).add(edge.id)

    def get_node(self, node_id: str) -> LineageNode | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_edge(self, edge_id: str) -> LineageEdge | None:
        """Get an edge by ID."""
        return self._edges.get(edge_id)

    def get_outgoing_edges(self, node_id: str) -> list[LineageEdge]:
        """Get all outgoing edges from a node."""
        edge_ids = self._outgoing.get(node_id, set())
        return [self._edges[eid] for eid in edge_ids if eid in self._edges]

    def get_incoming_edges(self, node_id: str) -> list[LineageEdge]:
        """Get all incoming edges to a node."""
        edge_ids = self._incoming.get(node_id, set())
        return [self._edges[eid] for eid in edge_ids if eid in self._edges]

    @property
    def node_count(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        """Return the number of edges in the graph."""
        return len(self._edges)

    def nodes(self) -> list[LineageNode]:
        """Return all nodes in the graph."""
        return list(self._nodes.values())

    def edges(self) -> list[LineageEdge]:
        """Return all edges in the graph."""
        return list(self._edges.values())

    def subgraph(self, node_ids: set[str]) -> "LineageGraph":
        """
        Create a subgraph containing only the specified nodes and their connecting edges.

        Args:
            node_ids: Set of node IDs to include

        Returns:
            A new LineageGraph containing only the specified nodes
        """
        subgraph = LineageGraph()

        for node_id in node_ids:
            if node_id in self._nodes:
                subgraph.add_node(self._nodes[node_id])

        for edge in self._edges.values():
            if edge.source_id in node_ids and edge.target_id in node_ids:
                subgraph.add_edge(edge)

        return subgraph
