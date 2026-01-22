"""
Tests for bounded lineage queries.

Verifies that the P2 finding (unbounded graph traversal) is addressed
with proper limits on depth, nodes, and timeout.
"""

from datetime import timedelta

import pytest

from forge_data.lineage import (
    EdgeType,
    LineageEdge,
    LineageGraph,
    LineageNode,
    LineageQuery,
    NodeType,
    TraversalDirection,
)
from forge_data.lineage.query import create_bounded_query


class TestLineageQueryLimits:
    """Test that lineage queries enforce bounded limits."""

    def test_default_limits(self):
        """Test that default limits match architecture spec."""
        query = LineageQuery(root_node_id="test")

        assert query.max_depth == 10, "Default max_depth should be 10"
        assert query.max_nodes == 1000, "Default max_nodes should be 1000"
        assert query.timeout == timedelta(seconds=30), "Default timeout should be 30s"

    def test_max_depth_validation(self):
        """Test that max_depth cannot exceed 100."""
        with pytest.raises(ValueError, match="max_depth cannot exceed 100"):
            LineageQuery(root_node_id="test", max_depth=101)

    def test_max_nodes_validation(self):
        """Test that max_nodes cannot exceed 10000."""
        with pytest.raises(ValueError, match="max_nodes cannot exceed 10000"):
            LineageQuery(root_node_id="test", max_nodes=10001)

    def test_timeout_validation(self):
        """Test that timeout cannot exceed 300 seconds."""
        with pytest.raises(ValueError, match="timeout cannot exceed 300 seconds"):
            LineageQuery(root_node_id="test", timeout=timedelta(seconds=301))

    def test_minimum_values(self):
        """Test that minimum values are enforced."""
        with pytest.raises(ValueError, match="max_depth must be at least 1"):
            LineageQuery(root_node_id="test", max_depth=0)

        with pytest.raises(ValueError, match="max_nodes must be at least 1"):
            LineageQuery(root_node_id="test", max_nodes=0)

        with pytest.raises(ValueError, match="timeout must be at least 1 second"):
            LineageQuery(root_node_id="test", timeout=timedelta(seconds=0))

    def test_create_bounded_query_factory(self):
        """Test the factory function creates properly bounded queries."""
        query = create_bounded_query(
            root_node_id="test",
            direction=TraversalDirection.DOWNSTREAM,
        )

        assert query.root_node_id == "test"
        assert query.direction == TraversalDirection.DOWNSTREAM
        assert query.max_depth == 10
        assert query.max_nodes == 1000


class TestLineageQueryExecution:
    """Test lineage query execution with limits."""

    @pytest.fixture
    def sample_graph(self) -> LineageGraph:
        """Create a sample lineage graph for testing."""
        graph = LineageGraph()

        # Create a chain of 20 nodes
        for i in range(20):
            node = LineageNode(
                id=f"node-{i}",
                type=NodeType.COLUMN,
                name=f"column_{i}",
                qualified_name=f"db.schema.table.column_{i}",
            )
            graph.add_node(node)

            if i > 0:
                edge = LineageEdge(
                    id=f"edge-{i-1}-{i}",
                    source_id=f"node-{i-1}",
                    target_id=f"node-{i}",
                    edge_type=EdgeType.DERIVES_FROM,
                )
                graph.add_edge(edge)

        return graph

    @pytest.mark.asyncio
    async def test_depth_limit_respected(self, sample_graph: LineageGraph):
        """Test that depth limit truncates results."""
        query = LineageQuery(
            root_node_id="node-0",
            direction=TraversalDirection.DOWNSTREAM,
            max_depth=5,
        )

        result = await query.execute(sample_graph)

        # Should have traversed at most 5 levels
        assert result.depth_reached <= 5
        assert result.nodes_visited <= 6  # Root + 5 levels

    @pytest.mark.asyncio
    async def test_node_limit_respected(self, sample_graph: LineageGraph):
        """Test that node limit truncates results."""
        query = LineageQuery(
            root_node_id="node-0",
            direction=TraversalDirection.DOWNSTREAM,
            max_nodes=5,
        )

        result = await query.execute(sample_graph)

        assert result.nodes_visited <= 5
        if result.nodes_visited == 5:
            assert result.truncated is True
            assert "Node limit" in (result.truncation_reason or "")

    @pytest.mark.asyncio
    async def test_truncation_metadata(self, sample_graph: LineageGraph):
        """Test that truncation is properly reported."""
        query = LineageQuery(
            root_node_id="node-0",
            direction=TraversalDirection.DOWNSTREAM,
            max_depth=3,
            max_nodes=3,
        )

        result = await query.execute(sample_graph)

        # Result should indicate truncation
        assert result.graph is not None
        assert result.root_node_id == "node-0"
        assert result.direction == TraversalDirection.DOWNSTREAM

    @pytest.mark.asyncio
    async def test_empty_graph(self):
        """Test query on empty graph."""
        graph = LineageGraph()
        query = LineageQuery(root_node_id="nonexistent")

        result = await query.execute(graph)

        assert result.nodes_visited == 0
        assert result.truncated is False

    @pytest.mark.asyncio
    async def test_single_node(self):
        """Test query with single node (no edges)."""
        graph = LineageGraph()
        graph.add_node(
            LineageNode(
                id="solo",
                type=NodeType.TABLE,
                name="solo_table",
                qualified_name="db.solo_table",
            )
        )

        query = LineageQuery(root_node_id="solo")
        result = await query.execute(graph)

        assert result.nodes_visited == 1
        assert result.depth_reached == 0
        assert result.truncated is False


class TestLineageQueryFilters:
    """Test lineage query filtering capabilities."""

    @pytest.fixture
    def mixed_graph(self) -> LineageGraph:
        """Create a graph with mixed node types."""
        graph = LineageGraph()

        # Add nodes of different types
        for node_type in [NodeType.COLUMN, NodeType.TABLE, NodeType.TRANSFORM]:
            for i in range(3):
                graph.add_node(
                    LineageNode(
                        id=f"{node_type.value}-{i}",
                        type=node_type,
                        name=f"{node_type.value}_{i}",
                        qualified_name=f"test.{node_type.value}_{i}",
                    )
                )

        return graph

    def test_edge_type_filter(self):
        """Test filtering by edge types."""
        query = LineageQuery(
            root_node_id="test",
            edge_types=[EdgeType.DERIVES_FROM, EdgeType.CONTAINS],
        )

        assert query.edge_types == [EdgeType.DERIVES_FROM, EdgeType.CONTAINS]

    def test_node_type_filter(self):
        """Test filtering by node types."""
        query = LineageQuery(
            root_node_id="test",
            node_types=["column", "table"],
        )

        assert query.node_types == ["column", "table"]
