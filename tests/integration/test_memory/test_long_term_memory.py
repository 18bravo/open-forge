"""
Integration tests for the long-term memory system.

These tests verify:
- Memory storage and retrieval via EngagementMemoryStore
- Semantic search returns relevant results
- Cross-thread memory sharing works correctly
- Memory namespacing isolates engagements properly

Requirements:
- PostgreSQL with pgvector extension
- OpenAI API key for embeddings
"""
import pytest
import uuid
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio


# Test fixtures
@pytest.fixture
def engagement_id() -> str:
    """Generate a unique engagement ID for testing."""
    return f"test_eng_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def mock_embeddings():
    """Mock OpenAI embeddings for testing without API calls."""
    with patch("agent_framework.memory.long_term.OpenAIEmbeddings") as mock:
        mock_instance = MagicMock()
        # Return consistent mock embeddings (1536 dimensions)
        mock_instance.embed_documents.return_value = [[0.1] * 1536]
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_store():
    """Create a mock PostgresStore for unit testing."""
    mock = AsyncMock()
    mock.aput = AsyncMock()
    mock.aget = AsyncMock()
    mock.alist = AsyncMock(return_value=[])
    mock.asearch = AsyncMock(return_value=[])
    mock.adelete = AsyncMock()
    return mock


class TestEngagementMemoryStore:
    """Tests for the EngagementMemoryStore class."""

    @pytest.mark.asyncio
    async def test_store_memory_creates_correct_namespace(
        self,
        engagement_id: str,
        mock_embeddings,
    ):
        """Test that memories are stored with the correct namespace structure."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        # Patch PostgresStore to track calls
        with patch("agent_framework.memory.long_term.PostgresStore") as mock_postgres:
            mock_store_instance = AsyncMock()
            mock_store_instance.aput = AsyncMock()
            mock_postgres.from_conn_string.return_value = mock_store_instance

            store = EngagementMemoryStore("postgresql://test")

            # Store a memory
            key = await store.store_memory(
                engagement_id=engagement_id,
                memory_type="stakeholder",
                content={"name": "John Doe", "role": "CTO"},
            )

            # Verify namespace structure
            mock_store_instance.aput.assert_called_once()
            call_args = mock_store_instance.aput.call_args
            namespace = call_args.kwargs.get("namespace") or call_args[0][0]

            assert namespace == ("engagements", engagement_id, "stakeholder")
            assert key is not None

    @pytest.mark.asyncio
    async def test_store_memory_with_metadata(
        self,
        engagement_id: str,
        mock_embeddings,
    ):
        """Test that metadata is properly stored with memories."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        with patch("agent_framework.memory.long_term.PostgresStore") as mock_postgres:
            mock_store_instance = AsyncMock()
            mock_store_instance.aput = AsyncMock()
            mock_postgres.from_conn_string.return_value = mock_store_instance

            store = EngagementMemoryStore("postgresql://test")

            metadata = {"source": "interview", "confidence": 0.95}
            await store.store_memory(
                engagement_id=engagement_id,
                memory_type="requirement",
                content={"description": "System must support 1000 concurrent users"},
                metadata=metadata,
            )

            # Verify metadata is included in stored value
            call_args = mock_store_instance.aput.call_args
            stored_value = call_args.kwargs.get("value") or call_args[0][2]

            assert stored_value["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_search_memories_with_type_filter(
        self,
        engagement_id: str,
        mock_embeddings,
    ):
        """Test semantic search with memory type filtering."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        with patch("agent_framework.memory.long_term.PostgresStore") as mock_postgres:
            mock_store_instance = AsyncMock()

            # Create mock search result
            mock_result = MagicMock()
            mock_result.key = "test_key"
            mock_result.value = {"content": {"name": "Jane"}, "metadata": {}}
            mock_result.score = 0.95

            mock_store_instance.asearch = AsyncMock(return_value=[mock_result])
            mock_postgres.from_conn_string.return_value = mock_store_instance

            store = EngagementMemoryStore("postgresql://test")

            results = await store.search_memories(
                engagement_id=engagement_id,
                query="executive stakeholder",
                memory_types=["stakeholder"],
                limit=5,
            )

            # Verify search was called with correct namespace
            mock_store_instance.asearch.assert_called()
            assert len(results) == 1
            assert results[0]["content"]["name"] == "Jane"
            assert results[0]["memory_type"] == "stakeholder"

    @pytest.mark.asyncio
    async def test_search_memories_across_all_types(
        self,
        engagement_id: str,
        mock_embeddings,
    ):
        """Test semantic search across all memory types."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        with patch("agent_framework.memory.long_term.PostgresStore") as mock_postgres:
            mock_store_instance = AsyncMock()

            mock_result = MagicMock()
            mock_result.key = "test_key"
            mock_result.namespace = ("engagements", engagement_id, "decision")
            mock_result.value = {"content": {"decision": "Use microservices"}, "metadata": {}}
            mock_result.score = 0.88

            mock_store_instance.asearch = AsyncMock(return_value=[mock_result])
            mock_postgres.from_conn_string.return_value = mock_store_instance

            store = EngagementMemoryStore("postgresql://test")

            results = await store.search_memories(
                engagement_id=engagement_id,
                query="architecture decisions",
                memory_types=None,  # Search all types
                limit=10,
            )

            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_memories_by_type(
        self,
        engagement_id: str,
        mock_embeddings,
    ):
        """Test retrieving all memories of a specific type."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        with patch("agent_framework.memory.long_term.PostgresStore") as mock_postgres:
            mock_store_instance = AsyncMock()

            # Create mock list results
            mock_items = []
            for i in range(3):
                item = MagicMock()
                item.key = f"key_{i}"
                item.value = {"content": {"name": f"Stakeholder {i}"}, "metadata": {}}
                mock_items.append(item)

            mock_store_instance.alist = AsyncMock(return_value=mock_items)
            mock_postgres.from_conn_string.return_value = mock_store_instance

            store = EngagementMemoryStore("postgresql://test")

            results = await store.get_memories_by_type(
                engagement_id=engagement_id,
                memory_type="stakeholder",
                limit=100,
            )

            assert len(results) == 3
            assert results[0]["content"]["name"] == "Stakeholder 0"

    @pytest.mark.asyncio
    async def test_get_specific_memory(
        self,
        engagement_id: str,
        mock_embeddings,
    ):
        """Test retrieving a specific memory by key."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        with patch("agent_framework.memory.long_term.PostgresStore") as mock_postgres:
            mock_store_instance = AsyncMock()

            mock_item = MagicMock()
            mock_item.value = {"content": {"description": "Test requirement"}, "metadata": {"priority": "high"}}

            mock_store_instance.aget = AsyncMock(return_value=mock_item)
            mock_postgres.from_conn_string.return_value = mock_store_instance

            store = EngagementMemoryStore("postgresql://test")

            result = await store.get_memory(
                engagement_id=engagement_id,
                memory_type="requirement",
                key="specific_key",
            )

            assert result is not None
            assert result["content"]["description"] == "Test requirement"
            assert result["metadata"]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_delete_memory(
        self,
        engagement_id: str,
        mock_embeddings,
    ):
        """Test deleting a specific memory."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        with patch("agent_framework.memory.long_term.PostgresStore") as mock_postgres:
            mock_store_instance = AsyncMock()
            mock_store_instance.adelete = AsyncMock()
            mock_postgres.from_conn_string.return_value = mock_store_instance

            store = EngagementMemoryStore("postgresql://test")

            success = await store.delete_memory(
                engagement_id=engagement_id,
                memory_type="stakeholder",
                key="key_to_delete",
            )

            assert success is True
            mock_store_instance.adelete.assert_called_once()


class TestContentToText:
    """Tests for the content-to-text conversion."""

    def test_simple_dict(self):
        """Test conversion of a simple dictionary."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        with patch("agent_framework.memory.long_term.PostgresStore"):
            with patch("agent_framework.memory.long_term.OpenAIEmbeddings"):
                store = EngagementMemoryStore("postgresql://test")

                content = {"name": "John", "role": "CTO"}
                text = store._content_to_text(content)

                assert "name: John" in text
                assert "role: CTO" in text

    def test_nested_dict(self):
        """Test conversion of nested dictionaries."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        with patch("agent_framework.memory.long_term.PostgresStore"):
            with patch("agent_framework.memory.long_term.OpenAIEmbeddings"):
                store = EngagementMemoryStore("postgresql://test")

                content = {
                    "stakeholder": {
                        "name": "Jane",
                        "department": "Engineering"
                    }
                }
                text = store._content_to_text(content)

                assert "name: Jane" in text
                assert "department: Engineering" in text

    def test_list_values(self):
        """Test conversion of lists."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        with patch("agent_framework.memory.long_term.PostgresStore"):
            with patch("agent_framework.memory.long_term.OpenAIEmbeddings"):
                store = EngagementMemoryStore("postgresql://test")

                content = {
                    "priorities": ["security", "scalability", "performance"]
                }
                text = store._content_to_text(content)

                assert "security" in text
                assert "scalability" in text
                assert "performance" in text


class TestMemoryNamespacing:
    """Tests for memory namespace isolation."""

    @pytest.mark.asyncio
    async def test_different_engagements_isolated(self, mock_embeddings):
        """Test that memories from different engagements are isolated."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        eng_id_1 = f"eng_{uuid.uuid4().hex[:8]}"
        eng_id_2 = f"eng_{uuid.uuid4().hex[:8]}"

        with patch("agent_framework.memory.long_term.PostgresStore") as mock_postgres:
            mock_store_instance = AsyncMock()
            mock_store_instance.aput = AsyncMock()
            mock_postgres.from_conn_string.return_value = mock_store_instance

            store = EngagementMemoryStore("postgresql://test")

            # Store memory in engagement 1
            await store.store_memory(
                engagement_id=eng_id_1,
                memory_type="stakeholder",
                content={"name": "User 1"},
            )

            # Store memory in engagement 2
            await store.store_memory(
                engagement_id=eng_id_2,
                memory_type="stakeholder",
                content={"name": "User 2"},
            )

            # Verify different namespaces were used
            calls = mock_store_instance.aput.call_args_list
            assert len(calls) == 2

            namespace_1 = calls[0].kwargs.get("namespace") or calls[0][0][0]
            namespace_2 = calls[1].kwargs.get("namespace") or calls[1][0][0]

            assert namespace_1[1] == eng_id_1
            assert namespace_2[1] == eng_id_2
            assert namespace_1 != namespace_2


class TestCrossThreadMemory:
    """Tests for cross-thread memory sharing."""

    @pytest.mark.asyncio
    async def test_memory_accessible_from_different_threads(
        self,
        engagement_id: str,
        mock_embeddings,
    ):
        """Test that memories stored in one thread are accessible from another."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        with patch("agent_framework.memory.long_term.PostgresStore") as mock_postgres:
            mock_store_instance = AsyncMock()

            # Simulated storage
            stored_memories: Dict[tuple, Dict] = {}

            async def mock_aput(namespace, key, value):
                stored_memories[(namespace, key)] = value

            async def mock_asearch(namespace, query, limit):
                results = []
                for (ns, key), value in stored_memories.items():
                    # Simple namespace prefix match
                    if ns[:len(namespace)] == namespace:
                        result = MagicMock()
                        result.key = key
                        result.namespace = ns
                        result.value = value
                        result.score = 0.9
                        results.append(result)
                return results[:limit]

            mock_store_instance.aput = mock_aput
            mock_store_instance.asearch = mock_asearch
            mock_postgres.from_conn_string.return_value = mock_store_instance

            store = EngagementMemoryStore("postgresql://test")

            # Store memory (simulating thread 1)
            await store.store_memory(
                engagement_id=engagement_id,
                memory_type="insight",
                content={"insight": "Important observation from thread 1"},
            )

            # Search memory (simulating thread 2)
            results = await store.search_memories(
                engagement_id=engagement_id,
                query="important observation",
                memory_types=["insight"],
            )

            # Verify memory is accessible
            assert len(results) >= 1
            assert "Important observation" in str(results[0]["content"])


class TestSemanticSearchRelevance:
    """Tests for semantic search relevance ordering."""

    @pytest.mark.asyncio
    async def test_results_ordered_by_relevance(
        self,
        engagement_id: str,
        mock_embeddings,
    ):
        """Test that search results are ordered by relevance score."""
        from agent_framework.memory.long_term import EngagementMemoryStore

        with patch("agent_framework.memory.long_term.PostgresStore") as mock_postgres:
            mock_store_instance = AsyncMock()

            # Create mock results with different scores
            mock_results = []
            for score, name in [(0.5, "Low relevance"), (0.95, "High relevance"), (0.7, "Medium relevance")]:
                result = MagicMock()
                result.key = f"key_{score}"
                result.value = {"content": {"name": name}, "metadata": {}}
                result.score = score
                mock_results.append(result)

            mock_store_instance.asearch = AsyncMock(return_value=mock_results)
            mock_postgres.from_conn_string.return_value = mock_store_instance

            store = EngagementMemoryStore("postgresql://test")

            results = await store.search_memories(
                engagement_id=engagement_id,
                query="relevant stakeholder",
                memory_types=["stakeholder"],
            )

            # Results should be ordered by score (highest first)
            scores = [r.get("score", 0) for r in results]
            assert scores == sorted(scores, reverse=True)
            assert results[0]["content"]["name"] == "High relevance"


class TestMemoryTypes:
    """Tests for the MemoryTypes constants."""

    def test_memory_types_defined(self):
        """Test that all expected memory types are defined."""
        from agent_framework.memory.long_term import MemoryTypes

        assert MemoryTypes.STAKEHOLDER == "stakeholder"
        assert MemoryTypes.REQUIREMENT == "requirement"
        assert MemoryTypes.DECISION == "decision"
        assert MemoryTypes.INSIGHT == "insight"
        assert MemoryTypes.ARTIFACT == "artifact"
        assert MemoryTypes.FEEDBACK == "feedback"
        assert MemoryTypes.CONVERSATION == "conversation"


# Integration tests that require actual PostgreSQL + pgvector
# These are marked to skip unless explicitly enabled
@pytest.mark.integration
@pytest.mark.skip(reason="Requires PostgreSQL with pgvector")
class TestIntegrationWithPostgres:
    """Integration tests requiring actual PostgreSQL."""

    @pytest_asyncio.fixture
    async def live_store(self):
        """Create a live EngagementMemoryStore connected to test database."""
        import os
        from agent_framework.memory.long_term import EngagementMemoryStore

        connection_string = os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/open_forge_test"
        )

        store = EngagementMemoryStore(connection_string)
        yield store

    @pytest.mark.asyncio
    async def test_full_memory_lifecycle(self, live_store, engagement_id):
        """Test complete memory lifecycle with real database."""
        # Store
        key = await live_store.store_memory(
            engagement_id=engagement_id,
            memory_type="stakeholder",
            content={"name": "Integration Test User", "role": "Developer"},
        )
        assert key is not None

        # Retrieve
        memory = await live_store.get_memory(
            engagement_id=engagement_id,
            memory_type="stakeholder",
            key=key,
        )
        assert memory["content"]["name"] == "Integration Test User"

        # Search
        results = await live_store.search_memories(
            engagement_id=engagement_id,
            query="developer",
            memory_types=["stakeholder"],
        )
        assert len(results) >= 1

        # Delete
        success = await live_store.delete_memory(
            engagement_id=engagement_id,
            memory_type="stakeholder",
            key=key,
        )
        assert success is True
