"""
Tests for database connection module.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os


class TestDatabaseConnection:
    """Tests for database connection management."""

    @pytest.mark.asyncio
    async def test_get_async_db_yields_session(self, mock_env_vars, mock_async_session):
        """Test that get_async_db yields a session."""
        from core.database.connection import get_async_db

        mock_session_factory = MagicMock()
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_async_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_session_factory.return_value = mock_context

        with patch("core.database.connection._async_session_factory", mock_session_factory):
            async with get_async_db() as session:
                assert session is not None


class TestGraphDatabase:
    """Tests for graph database operations."""

    def test_graph_database_initialization(self, mock_env_vars):
        """Test GraphDatabase initialization."""
        from core.database.graph import GraphDatabase

        with patch.dict(os.environ, mock_env_vars, clear=False):
            graph_db = GraphDatabase()
            assert graph_db.graph_name == "openforge_graph"

    def test_build_cypher_query(self, mock_env_vars):
        """Test Cypher query building."""
        from core.database.graph import GraphDatabase

        with patch.dict(os.environ, mock_env_vars, clear=False):
            graph_db = GraphDatabase()
            query = "MATCH (n) RETURN n"
            wrapped = graph_db._build_query(query)

            assert "openforge_graph" in wrapped
            assert "MATCH (n) RETURN n" in wrapped
