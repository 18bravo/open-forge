"""
Base search engine types and SearchEngine protocol.

This module defines the core abstractions for semantic and hybrid search.
"""

from abc import abstractmethod
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class SearchMode(str, Enum):
    """Search mode for query execution."""

    SEMANTIC = "semantic"  # Vector similarity only
    KEYWORD = "keyword"  # Full-text/keyword search only
    HYBRID = "hybrid"  # Combined semantic + keyword


class SearchQuery(BaseModel):
    """A search query with optional filters and configuration."""

    text: str = Field(..., description="Query text")
    collection: str = Field(..., description="Collection to search")
    mode: SearchMode = Field(
        default=SearchMode.SEMANTIC,
        description="Search mode",
    )
    limit: int = Field(default=10, description="Maximum results to return")
    filter: dict[str, Any] | None = Field(
        default=None,
        description="Metadata filter (key-value pairs)",
    )
    min_score: float | None = Field(
        default=None,
        description="Minimum score threshold",
    )
    rerank: bool = Field(
        default=False,
        description="Whether to apply reranking",
    )
    rerank_limit: int | None = Field(
        default=None,
        description="Number of results to fetch before reranking",
    )

    # For hybrid search
    semantic_weight: float = Field(
        default=0.7,
        description="Weight for semantic results (0-1) in hybrid mode",
    )
    keyword_weight: float = Field(
        default=0.3,
        description="Weight for keyword results (0-1) in hybrid mode",
    )


class SearchResult(BaseModel):
    """A search result with document and scoring information."""

    id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float = Field(..., description="Final relevance score")

    # Detailed scoring for debugging/transparency
    semantic_score: float | None = Field(
        default=None,
        description="Semantic similarity score",
    )
    keyword_score: float | None = Field(
        default=None,
        description="Keyword/BM25 score",
    )
    rerank_score: float | None = Field(
        default=None,
        description="Reranking score",
    )


class SearchConfig(BaseModel):
    """Configuration for search engine."""

    default_limit: int = Field(default=10, description="Default result limit")
    max_limit: int = Field(default=100, description="Maximum result limit")
    default_mode: SearchMode = Field(
        default=SearchMode.SEMANTIC,
        description="Default search mode",
    )
    enable_reranking: bool = Field(
        default=False,
        description="Enable reranking by default",
    )
    rerank_model: str | None = Field(
        default=None,
        description="Model to use for reranking (e.g., 'cohere-rerank-v3')",
    )


@runtime_checkable
class SearchEngine(Protocol):
    """
    Protocol for search engines.

    Search engines provide semantic, keyword, and hybrid search capabilities
    over vector stores, with optional reranking.
    """

    @abstractmethod
    async def search(self, query: SearchQuery) -> list[SearchResult]:
        """
        Execute a search query.

        Args:
            query: The search query with text, filters, and configuration.

        Returns:
            List of SearchResult sorted by relevance.

        Raises:
            SearchError: If search execution fails.
        """
        ...

    @abstractmethod
    async def semantic_search(
        self,
        text: str,
        collection: str,
        limit: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Execute a semantic (vector) search.

        Args:
            text: Query text.
            collection: Collection to search.
            limit: Maximum results.
            filter: Optional metadata filter.

        Returns:
            List of SearchResult sorted by semantic similarity.
        """
        ...

    @abstractmethod
    async def hybrid_search(
        self,
        text: str,
        collection: str,
        limit: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Execute a hybrid search combining semantic and keyword matching.

        Args:
            text: Query text.
            collection: Collection to search.
            limit: Maximum results.
            semantic_weight: Weight for semantic results.
            keyword_weight: Weight for keyword results.
            filter: Optional metadata filter.

        Returns:
            List of SearchResult with combined scoring.
        """
        ...

    @abstractmethod
    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        limit: int | None = None,
    ) -> list[SearchResult]:
        """
        Rerank search results using a reranking model.

        Args:
            query: Original query text.
            results: Initial search results to rerank.
            limit: Maximum results to return after reranking.

        Returns:
            Reranked list of SearchResult.
        """
        ...


class SearchError(Exception):
    """Base exception for search errors."""

    def __init__(self, message: str, query: str | None = None):
        self.query = query
        super().__init__(message)


class CollectionNotFoundError(SearchError):
    """Raised when a collection is not found."""

    def __init__(self, collection: str):
        self.collection = collection
        super().__init__(f"Collection '{collection}' not found")
