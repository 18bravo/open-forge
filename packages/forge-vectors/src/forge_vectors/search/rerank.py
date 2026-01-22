"""
Result reranking implementations.

This module provides reranking capabilities to improve search result relevance
by scoring query-document pairs with specialized reranking models.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from forge_vectors.search.base import SearchResult


class RerankConfig(BaseModel):
    """Configuration for reranking."""

    model: str = Field(
        default="rerank-english-v3.0",
        description="Reranking model identifier",
    )
    top_n: int | None = Field(
        default=None,
        description="Number of top results to return (None for all)",
    )
    return_documents: bool = Field(
        default=False,
        description="Whether to return document text in response",
    )


class RerankResult(BaseModel):
    """Result from reranking."""

    index: int = Field(..., description="Original index in input list")
    relevance_score: float = Field(..., description="Reranking relevance score")


class Reranker(ABC):
    """
    Abstract base class for rerankers.

    Rerankers score query-document pairs to improve retrieval relevance.
    """

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> list[RerankResult]:
        """
        Rerank documents for a given query.

        Args:
            query: The search query.
            documents: List of document texts to rerank.
            top_n: Number of top results to return.

        Returns:
            List of RerankResult sorted by relevance.
        """
        ...

    async def rerank_results(
        self,
        query: str,
        results: list[SearchResult],
        top_n: int | None = None,
    ) -> list[SearchResult]:
        """
        Rerank SearchResult objects.

        Args:
            query: The search query.
            results: List of SearchResult to rerank.
            top_n: Number of top results to return.

        Returns:
            Reranked list of SearchResult with updated scores.
        """
        if not results:
            return []

        # Extract documents for reranking
        documents = [r.content for r in results]

        # Get reranked indices and scores
        reranked = await self.rerank(query, documents, top_n)

        # Build reranked results
        reranked_results = []
        for rr in reranked:
            original = results[rr.index]
            reranked_results.append(
                SearchResult(
                    id=original.id,
                    content=original.content,
                    metadata=original.metadata,
                    score=rr.relevance_score,
                    semantic_score=original.semantic_score,
                    keyword_score=original.keyword_score,
                    rerank_score=rr.relevance_score,
                )
            )

        return reranked_results


class CohereReranker(Reranker):
    """
    Cohere reranking implementation.

    Uses Cohere's rerank API for high-quality cross-encoder reranking.
    Requires the 'rerank' optional dependency:
        pip install forge-vectors[rerank]

    Example:
        reranker = CohereReranker(api_key="your-api-key")
        results = await reranker.rerank_results(
            query="How to configure auth?",
            results=search_results,
            top_n=5,
        )
    """

    def __init__(self, config: RerankConfig | None = None, api_key: str | None = None):
        self.config = config or RerankConfig()
        self.api_key = api_key
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create Cohere client."""
        if self._client is None:
            try:
                import cohere
            except ImportError as e:
                raise ImportError(
                    "cohere package required. Install with: pip install forge-vectors[rerank]"
                ) from e

            self._client = cohere.Client(api_key=self.api_key)

        return self._client

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> list[RerankResult]:
        """
        Rerank documents using Cohere's rerank API.

        Args:
            query: Search query.
            documents: Documents to rerank.
            top_n: Number of top results (defaults to config).

        Returns:
            List of RerankResult sorted by relevance.
        """
        if not documents:
            return []

        client = self._get_client()
        top_n = top_n or self.config.top_n or len(documents)

        # Call Cohere rerank API
        # Note: This is synchronous; wrap in executor for true async
        response = client.rerank(
            model=self.config.model,
            query=query,
            documents=documents,
            top_n=top_n,
            return_documents=False,
        )

        return [
            RerankResult(
                index=r.index,
                relevance_score=r.relevance_score,
            )
            for r in response.results
        ]


class CrossEncoderReranker(Reranker):
    """
    Local cross-encoder reranking using Sentence Transformers.

    Uses a cross-encoder model for reranking without external API calls.
    Requires the 'local' optional dependency:
        pip install forge-vectors[local]

    Example:
        reranker = CrossEncoderReranker(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
        results = await reranker.rerank_results(
            query="How to configure auth?",
            results=search_results,
            top_n=5,
        )
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str | None = None,
    ):
        self.model_name = model_name
        self.device = device
        self._model: Any = None

    def _get_model(self) -> Any:
        """Get or create cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers package required. "
                    "Install with: pip install forge-vectors[local]"
                ) from e

            self._model = CrossEncoder(self.model_name, device=self.device)

        return self._model

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> list[RerankResult]:
        """
        Rerank documents using a local cross-encoder model.

        Args:
            query: Search query.
            documents: Documents to rerank.
            top_n: Number of top results.

        Returns:
            List of RerankResult sorted by relevance.
        """
        if not documents:
            return []

        model = self._get_model()

        # Create query-document pairs
        pairs = [(query, doc) for doc in documents]

        # Get relevance scores
        scores = model.predict(pairs)

        # Create results with indices
        results = [
            RerankResult(index=i, relevance_score=float(score))
            for i, score in enumerate(scores)
        ]

        # Sort by score descending
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        # Return top_n
        if top_n:
            results = results[:top_n]

        return results
