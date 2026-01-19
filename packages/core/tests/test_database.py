# packages/core/tests/test_database.py
"""Tests for database operations."""
import pytest
from sqlalchemy import text
from core.database.connection import get_async_db
from core.database.graph import GraphDatabase

@pytest.mark.asyncio
async def test_database_connection():
    """Test that we can connect to PostgreSQL."""
    async with get_async_db() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

@pytest.mark.asyncio
async def test_age_extension_loaded():
    """Test that Apache AGE is available."""
    async with get_async_db() as session:
        result = await session.execute(text(
            "SELECT extname FROM pg_extension WHERE extname = 'age'"
        ))
        assert result.scalar() == 'age'

@pytest.mark.asyncio
async def test_graph_create_node():
    """Test creating a node in the graph."""
    graph = GraphDatabase()
    async with get_async_db() as session:
        await graph.initialize(session)
        
        node = await graph.create_node(session, "TestNode", {
            "id": "test-1",
            "name": "Test"
        })
        
        assert node is not None

@pytest.mark.asyncio
async def test_graph_create_edge():
    """Test creating an edge between nodes."""
    graph = GraphDatabase()
    async with get_async_db() as session:
        await graph.initialize(session)
        
        # Create two nodes
        await graph.create_node(session, "Person", {"id": "p1", "name": "Alice"})
        await graph.create_node(session, "Person", {"id": "p2", "name": "Bob"})
        
        # Create edge
        edge = await graph.create_edge(
            session,
            "KNOWS",
            "Person", "id", "p1",
            "Person", "id", "p2",
            {"since": "2024"}
        )
        
        assert edge is not None