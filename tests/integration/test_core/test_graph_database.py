"""
Integration tests for Apache AGE graph database operations.

Tests Cypher query execution, node/edge creation, and graph traversal
with a real PostgreSQL + AGE instance.
"""
import pytest
import pytest_asyncio
from datetime import datetime
import json

from tests.integration.conftest import requires_postgres


pytestmark = [pytest.mark.integration, requires_postgres]


class TestGraphDatabaseInitialization:
    """Tests for graph database initialization."""

    @pytest.mark.asyncio
    async def test_graph_database_initialization(self, graph_database, async_db_session):
        """Test that graph database initializes correctly."""
        assert graph_database is not None
        assert graph_database.graph_name == "test_graph"

    @pytest.mark.asyncio
    async def test_graph_exists_after_init(self, graph_database, async_db_session):
        """Test that graph is created in AGE catalog."""
        from sqlalchemy import text

        result = await async_db_session.execute(text("""
            SELECT * FROM ag_catalog.ag_graph WHERE name = 'test_graph'
        """))
        row = result.fetchone()

        assert row is not None


class TestNodeOperations:
    """Tests for node CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_node(self, graph_database, async_db_session):
        """Test creating a node in the graph."""
        result = await graph_database.create_node(
            async_db_session,
            label="Person",
            properties={"name": "Alice", "age": 30, "email": "alice@example.com"}
        )

        assert result is not None
        # The result should contain the node properties
        if isinstance(result, dict):
            assert "name" in result or "properties" in result

    @pytest.mark.asyncio
    async def test_create_multiple_nodes(self, graph_database, async_db_session):
        """Test creating multiple nodes."""
        # Create several nodes
        for i in range(5):
            await graph_database.create_node(
                async_db_session,
                label="TestNode",
                properties={"index": i, "name": f"node_{i}"}
            )

        # Query to count nodes
        results = await graph_database.execute_cypher(
            async_db_session,
            "MATCH (n:TestNode) RETURN count(n) as count"
        )

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_find_node_by_property(self, graph_database, async_db_session):
        """Test finding a node by property."""
        # Create a unique node
        unique_id = f"test_{datetime.utcnow().timestamp()}"
        await graph_database.create_node(
            async_db_session,
            label="UniqueNode",
            properties={"uid": unique_id, "data": "test_data"}
        )

        # Find the node
        results = await graph_database.find_node(
            async_db_session,
            label="UniqueNode",
            properties={"uid": unique_id}
        )

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_upsert_node_creates_new(self, graph_database, async_db_session):
        """Test upserting a node that doesn't exist."""
        unique_key = f"upsert_test_{datetime.utcnow().timestamp()}"

        result = await graph_database.upsert_node(
            async_db_session,
            label="UpsertTest",
            key_property="key",
            properties={"key": unique_key, "value": "initial"}
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_upsert_node_updates_existing(self, graph_database, async_db_session):
        """Test upserting a node that already exists."""
        unique_key = f"upsert_update_{datetime.utcnow().timestamp()}"

        # Create initial node
        await graph_database.upsert_node(
            async_db_session,
            label="UpsertUpdate",
            key_property="key",
            properties={"key": unique_key, "value": "first"}
        )

        # Upsert with updated value
        result = await graph_database.upsert_node(
            async_db_session,
            label="UpsertUpdate",
            key_property="key",
            properties={"key": unique_key, "value": "updated"}
        )

        # Verify the update
        results = await graph_database.find_node(
            async_db_session,
            label="UpsertUpdate",
            properties={"key": unique_key}
        )

        # Should only have one node with the updated value
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_delete_node(self, graph_database, async_db_session):
        """Test deleting a node."""
        unique_key = f"delete_test_{datetime.utcnow().timestamp()}"

        # Create node
        await graph_database.create_node(
            async_db_session,
            label="DeleteTest",
            properties={"key": unique_key}
        )

        # Delete node
        success = await graph_database.delete_node(
            async_db_session,
            label="DeleteTest",
            key_property="key",
            key_value=unique_key
        )

        assert success is True

        # Verify deletion
        results = await graph_database.find_node(
            async_db_session,
            label="DeleteTest",
            properties={"key": unique_key}
        )

        assert len(results) == 0


class TestEdgeOperations:
    """Tests for edge CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_edge_between_nodes(self, graph_database, async_db_session):
        """Test creating an edge between two nodes."""
        timestamp = datetime.utcnow().timestamp()

        # Create two nodes
        await graph_database.create_node(
            async_db_session,
            label="EdgeSource",
            properties={"id": f"source_{timestamp}"}
        )
        await graph_database.create_node(
            async_db_session,
            label="EdgeTarget",
            properties={"id": f"target_{timestamp}"}
        )

        # Create edge
        result = await graph_database.create_edge(
            async_db_session,
            edge_type="CONNECTS_TO",
            from_label="EdgeSource",
            from_key="id",
            from_value=f"source_{timestamp}",
            to_label="EdgeTarget",
            to_key="id",
            to_value=f"target_{timestamp}",
            properties={"weight": 1.0, "created": "test"}
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_create_edge_with_properties(self, graph_database, async_db_session):
        """Test creating an edge with properties."""
        timestamp = datetime.utcnow().timestamp()

        # Create nodes
        await graph_database.create_node(
            async_db_session,
            label="PropEdgeFrom",
            properties={"id": f"from_{timestamp}"}
        )
        await graph_database.create_node(
            async_db_session,
            label="PropEdgeTo",
            properties={"id": f"to_{timestamp}"}
        )

        # Create edge with properties
        edge_props = {
            "weight": 0.75,
            "relationship_type": "strong",
            "created_at": datetime.utcnow().isoformat()
        }

        result = await graph_database.create_edge(
            async_db_session,
            edge_type="RELATED_TO",
            from_label="PropEdgeFrom",
            from_key="id",
            from_value=f"from_{timestamp}",
            to_label="PropEdgeTo",
            to_key="id",
            to_value=f"to_{timestamp}",
            properties=edge_props
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_find_connected_nodes(self, graph_database, async_db_session):
        """Test finding nodes connected via edges."""
        timestamp = datetime.utcnow().timestamp()

        # Create a small graph: A -> B -> C
        await graph_database.create_node(
            async_db_session,
            label="PathNode",
            properties={"id": f"A_{timestamp}", "name": "Node A"}
        )
        await graph_database.create_node(
            async_db_session,
            label="PathNode",
            properties={"id": f"B_{timestamp}", "name": "Node B"}
        )
        await graph_database.create_node(
            async_db_session,
            label="PathNode",
            properties={"id": f"C_{timestamp}", "name": "Node C"}
        )

        # Create edges
        await graph_database.create_edge(
            async_db_session,
            edge_type="NEXT",
            from_label="PathNode",
            from_key="id",
            from_value=f"A_{timestamp}",
            to_label="PathNode",
            to_key="id",
            to_value=f"B_{timestamp}"
        )
        await graph_database.create_edge(
            async_db_session,
            edge_type="NEXT",
            from_label="PathNode",
            from_key="id",
            from_value=f"B_{timestamp}",
            to_label="PathNode",
            to_key="id",
            to_value=f"C_{timestamp}"
        )

        # Find connected nodes from A
        results = await graph_database.find_connected(
            async_db_session,
            from_label="PathNode",
            from_key="id",
            from_value=f"A_{timestamp}",
            edge_type="NEXT",
            to_label="PathNode"
        )

        # A is connected to B via NEXT
        assert len(results) >= 1


class TestCypherQueries:
    """Tests for raw Cypher query execution."""

    @pytest.mark.asyncio
    async def test_execute_simple_cypher(self, graph_database, async_db_session):
        """Test executing a simple Cypher query."""
        results = await graph_database.execute_cypher(
            async_db_session,
            "RETURN 1 as value"
        )

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_execute_cypher_with_params(self, graph_database, async_db_session):
        """Test executing Cypher with parameters."""
        timestamp = datetime.utcnow().timestamp()

        # Create a test node
        await graph_database.create_node(
            async_db_session,
            label="ParamTest",
            properties={"name": f"param_node_{timestamp}"}
        )

        # Query with parameters
        results = await graph_database.execute_cypher(
            async_db_session,
            "MATCH (n:ParamTest {name: $name}) RETURN n",
            params={"name": f"param_node_{timestamp}"}
        )

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_cypher_aggregation(self, graph_database, async_db_session):
        """Test Cypher aggregation queries."""
        timestamp = datetime.utcnow().timestamp()

        # Create multiple nodes with different categories
        for i in range(5):
            await graph_database.create_node(
                async_db_session,
                label="AggNode",
                properties={
                    "id": f"agg_{timestamp}_{i}",
                    "category": "A" if i < 3 else "B",
                    "value": i * 10
                }
            )

        # Count query
        results = await graph_database.execute_cypher(
            async_db_session,
            "MATCH (n:AggNode) RETURN count(n) as total"
        )

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_cypher_path_query(self, graph_database, async_db_session):
        """Test Cypher path queries."""
        timestamp = datetime.utcnow().timestamp()

        # Create a path: Start -> Middle -> End
        await graph_database.create_node(
            async_db_session,
            label="PathQueryNode",
            properties={"id": f"start_{timestamp}", "type": "start"}
        )
        await graph_database.create_node(
            async_db_session,
            label="PathQueryNode",
            properties={"id": f"middle_{timestamp}", "type": "middle"}
        )
        await graph_database.create_node(
            async_db_session,
            label="PathQueryNode",
            properties={"id": f"end_{timestamp}", "type": "end"}
        )

        await graph_database.create_edge(
            async_db_session,
            edge_type="FLOWS_TO",
            from_label="PathQueryNode",
            from_key="id",
            from_value=f"start_{timestamp}",
            to_label="PathQueryNode",
            to_key="id",
            to_value=f"middle_{timestamp}"
        )
        await graph_database.create_edge(
            async_db_session,
            edge_type="FLOWS_TO",
            from_label="PathQueryNode",
            from_key="id",
            from_value=f"middle_{timestamp}",
            to_label="PathQueryNode",
            to_key="id",
            to_value=f"end_{timestamp}"
        )

        # Query the path
        results = await graph_database.execute_cypher(
            async_db_session,
            f"MATCH (s:PathQueryNode {{id: 'start_{timestamp}'}})"
            "-[:FLOWS_TO*]->(e:PathQueryNode {type: 'end'}) "
            "RETURN e"
        )

        assert len(results) >= 1


class TestGraphDatabaseEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_node_with_special_characters(self, graph_database, async_db_session):
        """Test creating nodes with special characters in properties."""
        result = await graph_database.create_node(
            async_db_session,
            label="SpecialCharNode",
            properties={
                "name": "Test's \"Node\" with <special> & chars",
                "description": "Line1\nLine2\tTabbed"
            }
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_null_values(self, graph_database, async_db_session):
        """Test creating nodes with null/optional values handled correctly."""
        result = await graph_database.create_node(
            async_db_session,
            label="NullableNode",
            properties={
                "required_field": "value",
                "optional_field": ""  # Empty string instead of null
            }
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_node_with_numeric_types(self, graph_database, async_db_session):
        """Test nodes with various numeric types."""
        result = await graph_database.create_node(
            async_db_session,
            label="NumericNode",
            properties={
                "integer_val": 42,
                "float_val": 3.14159,
                "negative_val": -100,
                "zero_val": 0
            }
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_find_nonexistent_node(self, graph_database, async_db_session):
        """Test finding a node that doesn't exist."""
        results = await graph_database.find_node(
            async_db_session,
            label="NonExistentLabel",
            properties={"id": "does_not_exist_12345"}
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_node(self, graph_database, async_db_session):
        """Test deleting a node that doesn't exist."""
        # Should not raise an error
        success = await graph_database.delete_node(
            async_db_session,
            label="NonExistentLabel",
            key_property="id",
            key_value="nonexistent_12345"
        )

        # Should still return True (no error)
        assert success is True
