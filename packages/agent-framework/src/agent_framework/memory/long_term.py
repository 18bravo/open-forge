"""
Long-term memory store using LangGraph's PostgresStore with pgvector for semantic search.

This module provides cross-thread, engagement-scoped memory with semantic search capabilities.
"""
from typing import Optional, Dict, Any, List
import uuid
import logging

from langgraph.store.postgres import PostgresStore
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)


class EngagementMemoryStore:
    """
    Long-term memory store for engagement context.

    Uses PostgresStore with pgvector for semantic indexing and search.
    Memories are namespaced by engagement and memory type for organization.

    Example:
        store = EngagementMemoryStore(connection_string)
        await store.store_memory(
            engagement_id="eng_123",
            memory_type="stakeholder",
            content={"name": "John", "role": "CTO", "priorities": ["security", "scalability"]}
        )

        results = await store.search_memories(
            engagement_id="eng_123",
            query="security concerns",
            memory_types=["stakeholder", "requirement"]
        )
    """

    def __init__(self, connection_string: str):
        """
        Initialize the memory store with PostgresStore and pgvector indexing.

        Args:
            connection_string: PostgreSQL connection string with pgvector extension enabled
        """
        self._connection_string = connection_string
        self._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self._store: Optional[PostgresStore] = None

    async def _get_store(self) -> PostgresStore:
        """Get or create the PostgresStore instance."""
        if self._store is None:
            self._store = PostgresStore.from_conn_string(
                self._connection_string,
                index={
                    "dims": 1536,  # OpenAI text-embedding-3-small dimensions
                    "embed": self._get_embeddings,
                }
            )
        return self._store

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for semantic search.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        return self._embeddings.embed_documents(texts)

    async def store_memory(
        self,
        engagement_id: str,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a memory item with semantic indexing.

        Args:
            engagement_id: The engagement this memory belongs to
            memory_type: Category of memory (stakeholder, requirement, decision, insight, etc.)
            content: The structured content to store
            metadata: Optional additional metadata

        Returns:
            The generated key for this memory item
        """
        store = await self._get_store()

        namespace = ("engagements", engagement_id, memory_type)
        key = str(uuid.uuid4())

        # Create searchable text from content
        search_text = self._content_to_text(content)

        await store.aput(
            namespace=namespace,
            key=key,
            value={
                "content": content,
                "metadata": metadata or {},
                "search_text": search_text,
            }
        )

        logger.debug(
            f"Stored memory: engagement={engagement_id}, type={memory_type}, key={key}"
        )

        return key

    async def search_memories(
        self,
        engagement_id: str,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across engagement memories.

        Args:
            engagement_id: The engagement to search within
            query: Natural language search query
            memory_types: Optional list of memory types to filter by
            limit: Maximum number of results to return

        Returns:
            List of matching memory items with relevance scores
        """
        store = await self._get_store()

        if memory_types:
            # Search specific types and merge results
            results = []
            for mtype in memory_types:
                namespace = ("engagements", engagement_id, mtype)
                try:
                    items = await store.asearch(
                        namespace=namespace,
                        query=query,
                        limit=limit,
                    )
                    for item in items:
                        results.append({
                            "key": item.key,
                            "namespace": namespace,
                            "memory_type": mtype,
                            "content": item.value.get("content", {}),
                            "metadata": item.value.get("metadata", {}),
                            "score": getattr(item, "score", None),
                        })
                except Exception as e:
                    logger.warning(f"Error searching namespace {namespace}: {e}")
                    continue

            # Sort by score and return top results
            results.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
            return results[:limit]
        else:
            # Search all engagement memories using wildcard namespace
            namespace = ("engagements", engagement_id)
            try:
                items = await store.asearch(
                    namespace=namespace,
                    query=query,
                    limit=limit,
                )
                return [
                    {
                        "key": item.key,
                        "namespace": item.namespace,
                        "content": item.value.get("content", {}),
                        "metadata": item.value.get("metadata", {}),
                        "score": getattr(item, "score", None),
                    }
                    for item in items
                ]
            except Exception as e:
                logger.error(f"Error searching engagement memories: {e}")
                return []

    async def get_memories_by_type(
        self,
        engagement_id: str,
        memory_type: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all memories of a specific type for an engagement.

        Args:
            engagement_id: The engagement to query
            memory_type: The type of memories to retrieve
            limit: Maximum number of results

        Returns:
            List of memory items
        """
        store = await self._get_store()

        namespace = ("engagements", engagement_id, memory_type)
        try:
            items = await store.alist(namespace=namespace, limit=limit)
            return [
                {
                    "key": item.key,
                    "content": item.value.get("content", {}),
                    "metadata": item.value.get("metadata", {}),
                }
                for item in items
            ]
        except Exception as e:
            logger.error(f"Error listing memories: {e}")
            return []

    async def get_memory(
        self,
        engagement_id: str,
        memory_type: str,
        key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory item by key.

        Args:
            engagement_id: The engagement ID
            memory_type: The memory type
            key: The memory key

        Returns:
            The memory item or None if not found
        """
        store = await self._get_store()

        namespace = ("engagements", engagement_id, memory_type)
        try:
            item = await store.aget(namespace=namespace, key=key)
            if item:
                return {
                    "key": key,
                    "content": item.value.get("content", {}),
                    "metadata": item.value.get("metadata", {}),
                }
            return None
        except Exception as e:
            logger.error(f"Error getting memory: {e}")
            return None

    async def delete_memory(
        self,
        engagement_id: str,
        memory_type: str,
        key: str
    ) -> bool:
        """
        Delete a specific memory item.

        Args:
            engagement_id: The engagement ID
            memory_type: The memory type
            key: The memory key

        Returns:
            True if deleted successfully
        """
        store = await self._get_store()

        namespace = ("engagements", engagement_id, memory_type)
        try:
            await store.adelete(namespace=namespace, key=key)
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False

    def _content_to_text(self, content: Dict[str, Any]) -> str:
        """
        Convert structured content to searchable text.

        Recursively extracts text from nested structures for semantic indexing.

        Args:
            content: The structured content dictionary

        Returns:
            A single text string for embedding
        """
        parts = []

        def extract_text(obj: Any, prefix: str = "") -> None:
            if isinstance(obj, str):
                parts.append(f"{prefix}{obj}" if prefix else obj)
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    key_prefix = f"{prefix}{key}: " if prefix else f"{key}: "
                    extract_text(value, key_prefix)
            elif isinstance(obj, list):
                for item in obj:
                    extract_text(item, prefix)
            elif obj is not None:
                parts.append(f"{prefix}{str(obj)}" if prefix else str(obj))

        extract_text(content)
        return " | ".join(parts)


# Memory type constants for type safety
class MemoryTypes:
    """Standard memory type identifiers."""
    STAKEHOLDER = "stakeholder"
    REQUIREMENT = "requirement"
    DECISION = "decision"
    INSIGHT = "insight"
    ARTIFACT = "artifact"
    FEEDBACK = "feedback"
    CONVERSATION = "conversation"
