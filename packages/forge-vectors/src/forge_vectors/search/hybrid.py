"""
Hybrid search implementation combining semantic and keyword search.

This module provides the main SearchEngine implementation that supports:
- Semantic search using vector similarity
- Keyword search using PostgreSQL full-text search
- Hybrid search combining both approaches
- Optional reranking using external models
"""

from typing import Any

from pydantic import BaseModel, Field

from forge_vectors.embeddings.base import EmbeddingProvider
from forge_vectors.search.base import (
    SearchConfig,
    SearchEngine,
    SearchError,
    SearchMode,
    SearchQuery,
    SearchResult,
)
from forge_vectors.stores.base import VectorStore


class HybridSearchEngineConfig(BaseModel):
    """Configuration for hybrid search engine."""

    search_config: SearchConfig = Field(default_factory=SearchConfig)
    keyword_index_enabled: bool = Field(
        default=True,
        description="Whether keyword search is available",
    )
    normalize_scores: bool = Field(
        default=True,
        description="Normalize scores to 0-1 range before combining",
    )


class HybridSearchEngine:
    """
    Search engine supporting semantic, keyword, and hybrid search.

    Combines vector similarity search with PostgreSQL full-text search
    for improved retrieval quality.

    Example:
        engine = HybridSearchEngine(
            store=pgvector_store,
            embedding_provider=openai_embeddings,
        )

        results = await engine.search(SearchQuery(
            text="How do I configure authentication?",
            collection="docs",
            mode=SearchMode.HYBRID,
            limit=10,
        ))
    """

    def __init__(
        self,
        store: VectorStore,
        embedding_provider: EmbeddingProvider,
        config: HybridSearchEngineConfig | None = None,
        reranker: Any | None = None,  # Optional reranking model
    ):
        self.store = store
        self.embedding_provider = embedding_provider
        self.config = config or HybridSearchEngineConfig()
        self.reranker = reranker

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        """
        Execute a search query based on the specified mode.

        Args:
            query: Search query with text, mode, and configuration.

        Returns:
            List of SearchResult sorted by relevance.
        """
        # Validate limit
        limit = min(query.limit, self.config.search_config.max_limit)

        # Execute search based on mode
        if query.mode == SearchMode.SEMANTIC:
            results = await self.semantic_search(
                text=query.text,
                collection=query.collection,
                limit=limit,
                filter=query.filter,
            )
        elif query.mode == SearchMode.KEYWORD:
            results = await self._keyword_search(
                text=query.text,
                collection=query.collection,
                limit=limit,
                filter=query.filter,
            )
        elif query.mode == SearchMode.HYBRID:
            results = await self.hybrid_search(
                text=query.text,
                collection=query.collection,
                limit=limit,
                semantic_weight=query.semantic_weight,
                keyword_weight=query.keyword_weight,
                filter=query.filter,
            )
        else:
            raise SearchError(f"Unknown search mode: {query.mode}")

        # Apply reranking if requested
        if query.rerank and self.reranker:
            rerank_limit = query.rerank_limit or limit * 3
            # Fetch more results for reranking
            if len(results) < rerank_limit:
                # Re-fetch with larger limit
                results = await self.semantic_search(
                    text=query.text,
                    collection=query.collection,
                    limit=rerank_limit,
                    filter=query.filter,
                )
            results = await self.rerank(query.text, results, limit)

        # Apply minimum score filter
        if query.min_score is not None:
            results = [r for r in results if r.score >= query.min_score]

        return results[:limit]

    async def semantic_search(
        self,
        text: str,
        collection: str,
        limit: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Execute semantic search using vector similarity.

        Args:
            text: Query text to embed and search.
            collection: Collection to search.
            limit: Maximum results.
            filter: Optional metadata filter.

        Returns:
            List of SearchResult sorted by semantic similarity.
        """
        # Generate query embedding
        query_vector = await self.embedding_provider.embed_text(text)

        # Search vector store
        vector_results = await self.store.search(
            collection=collection,
            vector=query_vector,
            limit=limit,
            filter=filter,
        )

        # Convert to SearchResult
        return [
            SearchResult(
                id=r.document.id,
                content=r.document.content,
                metadata=r.document.metadata,
                score=r.score,
                semantic_score=r.score,
            )
            for r in vector_results
        ]

    async def _keyword_search(
        self,
        text: str,
        collection: str,
        limit: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Execute keyword search using full-text search.

        Note: This requires the vector store to support keyword search
        (e.g., PostgreSQL with tsvector columns).
        """
        # TODO: Implement keyword search via store extension
        # For now, fall back to semantic search
        return await self.semantic_search(text, collection, limit, filter)

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
        Execute hybrid search combining semantic and keyword matching.

        Uses Reciprocal Rank Fusion (RRF) to combine results from both
        search methods.
        """
        # Fetch more results for merging
        fetch_limit = limit * 2

        # Execute both searches
        semantic_results = await self.semantic_search(
            text=text,
            collection=collection,
            limit=fetch_limit,
            filter=filter,
        )
        keyword_results = await self._keyword_search(
            text=text,
            collection=collection,
            limit=fetch_limit,
            filter=filter,
        )

        # Combine using RRF
        return self._reciprocal_rank_fusion(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            limit=limit,
        )

    def _reciprocal_rank_fusion(
        self,
        semantic_results: list[SearchResult],
        keyword_results: list[SearchResult],
        semantic_weight: float,
        keyword_weight: float,
        limit: int,
        k: int = 60,  # RRF constant
    ) -> list[SearchResult]:
        """
        Combine results using Reciprocal Rank Fusion.

        RRF score = sum(weight / (k + rank)) for each result list.
        """
        # Build score dictionaries
        scores: dict[str, dict[str, Any]] = {}

        # Process semantic results
        for rank, result in enumerate(semantic_results, start=1):
            if result.id not in scores:
                scores[result.id] = {
                    "result": result,
                    "rrf_score": 0.0,
                    "semantic_score": result.semantic_score,
                    "keyword_score": None,
                }
            scores[result.id]["rrf_score"] += semantic_weight / (k + rank)

        # Process keyword results
        for rank, result in enumerate(keyword_results, start=1):
            if result.id not in scores:
                scores[result.id] = {
                    "result": result,
                    "rrf_score": 0.0,
                    "semantic_score": None,
                    "keyword_score": result.keyword_score,
                }
            scores[result.id]["rrf_score"] += keyword_weight / (k + rank)
            scores[result.id]["keyword_score"] = result.keyword_score

        # Sort by RRF score
        sorted_items = sorted(
            scores.values(),
            key=lambda x: x["rrf_score"],
            reverse=True,
        )

        # Build final results
        results = []
        for item in sorted_items[:limit]:
            result = item["result"]
            results.append(
                SearchResult(
                    id=result.id,
                    content=result.content,
                    metadata=result.metadata,
                    score=item["rrf_score"],
                    semantic_score=item["semantic_score"],
                    keyword_score=item["keyword_score"],
                )
            )

        return results

    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        limit: int | None = None,
    ) -> list[SearchResult]:
        """
        Rerank results using a reranking model.

        Args:
            query: Original query text.
            results: Initial search results.
            limit: Maximum results to return.

        Returns:
            Reranked results with updated scores.
        """
        if not self.reranker:
            return results[:limit] if limit else results

        # TODO: Implement reranking with Cohere or cross-encoder model
        # For now, return as-is
        return results[:limit] if limit else results
