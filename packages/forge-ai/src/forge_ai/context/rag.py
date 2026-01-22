"""
RAG (Retrieval Augmented Generation) integration.

This module provides RAG retrieval for injecting relevant context
into LLM requests.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RAGConfig:
    """Configuration for RAG retrieval."""

    # Retrieval settings
    top_k: int = 5
    min_score: float = 0.0
    max_tokens: int = 3000

    # Filtering
    object_types: list[str] | None = None
    metadata_filters: dict[str, Any] | None = None

    # Reranking
    enable_reranking: bool = False
    rerank_top_k: int = 20


@dataclass
class RAGResult:
    """A single RAG retrieval result."""

    content: str
    score: float
    object_type: str | None = None
    object_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_index: int | None = None


class RAGRetriever(ABC):
    """
    Abstract RAG retriever interface.

    Implementations would integrate with vector stores (pgvector, Qdrant, etc.)
    """

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        ontology_id: str,
        object_types: list[str] | None = None,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[RAGResult]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: The search query.
            ontology_id: The ontology to search within.
            object_types: Optional filter for specific object types.
            top_k: Maximum number of results.
            min_score: Minimum relevance score.

        Returns:
            List of RAG results ordered by relevance.
        """
        ...

    @abstractmethod
    async def index(
        self,
        content: str,
        ontology_id: str,
        object_type: str,
        object_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Index content for RAG retrieval.

        Args:
            content: The content to index.
            ontology_id: The ontology this content belongs to.
            object_type: The type of object.
            object_id: The ID of the object.
            metadata: Additional metadata to store.
        """
        ...

    @abstractmethod
    async def delete(
        self,
        ontology_id: str,
        object_type: str | None = None,
        object_id: str | None = None,
    ) -> int:
        """
        Delete indexed content.

        Args:
            ontology_id: The ontology to delete from.
            object_type: Optional object type filter.
            object_id: Optional object ID filter.

        Returns:
            Number of documents deleted.
        """
        ...


class StubRAGRetriever(RAGRetriever):
    """
    Stub RAG retriever for testing and development.

    Returns empty/mock results for all operations.
    """

    def __init__(self):
        self._index: list[tuple[str, str, str, str, dict]] = []

    async def retrieve(
        self,
        query: str,
        ontology_id: str,
        object_types: list[str] | None = None,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[RAGResult]:
        """Retrieve relevant documents (stub returns empty list)."""
        # In a real implementation, this would:
        # 1. Embed the query
        # 2. Search the vector store
        # 3. Return top-k results

        # Stub: simple keyword matching
        results = []
        query_lower = query.lower()

        for content, ont_id, obj_type, obj_id, metadata in self._index:
            if ont_id != ontology_id:
                continue
            if object_types and obj_type not in object_types:
                continue

            # Simple relevance: check if query words are in content
            content_lower = content.lower()
            score = sum(1 for word in query_lower.split() if word in content_lower)
            if score > 0:
                results.append(
                    RAGResult(
                        content=content,
                        score=score / len(query_lower.split()),
                        object_type=obj_type,
                        object_id=obj_id,
                        metadata=metadata,
                    )
                )

        # Sort by score and return top_k
        results.sort(key=lambda r: r.score, reverse=True)
        return [r for r in results[:top_k] if r.score >= min_score]

    async def index(
        self,
        content: str,
        ontology_id: str,
        object_type: str,
        object_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Index content (stub stores in memory)."""
        self._index.append(
            (content, ontology_id, object_type, object_id, metadata or {})
        )

    async def delete(
        self,
        ontology_id: str,
        object_type: str | None = None,
        object_id: str | None = None,
    ) -> int:
        """Delete indexed content (stub removes from memory)."""
        original_count = len(self._index)

        self._index = [
            (content, ont_id, obj_type, obj_id, metadata)
            for content, ont_id, obj_type, obj_id, metadata in self._index
            if not (
                ont_id == ontology_id
                and (object_type is None or obj_type == object_type)
                and (object_id is None or obj_id == object_id)
            )
        ]

        return original_count - len(self._index)


class HybridRAGRetriever(RAGRetriever):
    """
    Hybrid RAG retriever combining semantic and keyword search.

    This is a stub implementation showing the pattern for hybrid search.
    """

    def __init__(
        self,
        semantic_retriever: RAGRetriever | None = None,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7,
    ):
        """
        Initialize hybrid retriever.

        Args:
            semantic_retriever: The semantic (vector) retriever.
            keyword_weight: Weight for keyword search results.
            semantic_weight: Weight for semantic search results.
        """
        self.semantic_retriever = semantic_retriever or StubRAGRetriever()
        self.keyword_retriever = StubRAGRetriever()
        self.keyword_weight = keyword_weight
        self.semantic_weight = semantic_weight

    async def retrieve(
        self,
        query: str,
        ontology_id: str,
        object_types: list[str] | None = None,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[RAGResult]:
        """Retrieve using hybrid search."""
        # Get results from both retrievers
        semantic_results = await self.semantic_retriever.retrieve(
            query, ontology_id, object_types, top_k * 2, 0.0
        )
        keyword_results = await self.keyword_retriever.retrieve(
            query, ontology_id, object_types, top_k * 2, 0.0
        )

        # Combine and deduplicate
        seen_ids: set[str] = set()
        combined: dict[str, RAGResult] = {}

        for result in semantic_results:
            key = f"{result.object_type}:{result.object_id}"
            if key not in seen_ids:
                seen_ids.add(key)
                combined[key] = RAGResult(
                    content=result.content,
                    score=result.score * self.semantic_weight,
                    object_type=result.object_type,
                    object_id=result.object_id,
                    metadata=result.metadata,
                )

        for result in keyword_results:
            key = f"{result.object_type}:{result.object_id}"
            if key in combined:
                combined[key].score += result.score * self.keyword_weight
            else:
                seen_ids.add(key)
                combined[key] = RAGResult(
                    content=result.content,
                    score=result.score * self.keyword_weight,
                    object_type=result.object_type,
                    object_id=result.object_id,
                    metadata=result.metadata,
                )

        # Sort by combined score and return top_k
        results = sorted(combined.values(), key=lambda r: r.score, reverse=True)
        return [r for r in results[:top_k] if r.score >= min_score]

    async def index(
        self,
        content: str,
        ontology_id: str,
        object_type: str,
        object_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Index in both retrievers."""
        await self.semantic_retriever.index(
            content, ontology_id, object_type, object_id, metadata
        )
        await self.keyword_retriever.index(
            content, ontology_id, object_type, object_id, metadata
        )

    async def delete(
        self,
        ontology_id: str,
        object_type: str | None = None,
        object_id: str | None = None,
    ) -> int:
        """Delete from both retrievers."""
        count1 = await self.semantic_retriever.delete(ontology_id, object_type, object_id)
        count2 = await self.keyword_retriever.delete(ontology_id, object_type, object_id)
        return max(count1, count2)  # Return max since they should have same content
