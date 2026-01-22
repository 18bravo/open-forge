"""
Embedding cache for performance optimization.

This module provides caching capabilities for embeddings to avoid
redundant API calls and improve performance.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import hashlib
from typing import Any

from pydantic import BaseModel, Field


class CacheConfig(BaseModel):
    """Configuration for embedding cache."""

    ttl: timedelta = Field(
        default=timedelta(days=7),
        description="Time-to-live for cached embeddings",
    )
    max_entries: int = Field(
        default=100_000,
        description="Maximum number of cached entries",
    )
    enabled: bool = Field(default=True, description="Whether caching is enabled")


class CacheEntry(BaseModel):
    """A cached embedding entry."""

    text_hash: str
    model: str
    embedding: list[float]
    dimensions: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime


class EmbeddingCache(ABC):
    """
    Abstract base class for embedding caches.

    Implementations provide storage backends for caching embeddings
    to reduce API calls and improve performance.
    """

    @abstractmethod
    async def get(
        self, text: str, model: str
    ) -> list[float] | None:
        """
        Retrieve a cached embedding.

        Args:
            text: The original text.
            model: The model used for embedding.

        Returns:
            The cached embedding vector, or None if not found.
        """
        ...

    @abstractmethod
    async def get_batch(
        self, texts: list[str], model: str
    ) -> dict[str, list[float] | None]:
        """
        Retrieve multiple cached embeddings.

        Args:
            texts: List of texts to look up.
            model: The model used for embedding.

        Returns:
            Dict mapping texts to their cached embeddings (None if not found).
        """
        ...

    @abstractmethod
    async def set(
        self, text: str, model: str, embedding: list[float]
    ) -> None:
        """
        Cache an embedding.

        Args:
            text: The original text.
            model: The model used for embedding.
            embedding: The embedding vector.
        """
        ...

    @abstractmethod
    async def set_batch(
        self, items: list[tuple[str, str, list[float]]]
    ) -> None:
        """
        Cache multiple embeddings.

        Args:
            items: List of (text, model, embedding) tuples.
        """
        ...

    @abstractmethod
    async def invalidate(self, text: str, model: str) -> bool:
        """
        Invalidate a cached embedding.

        Args:
            text: The original text.
            model: The model used for embedding.

        Returns:
            True if the entry was found and removed.
        """
        ...

    @abstractmethod
    async def clear(self) -> int:
        """
        Clear all cached embeddings.

        Returns:
            Number of entries cleared.
        """
        ...

    @staticmethod
    def hash_text(text: str, model: str) -> str:
        """Generate a hash key for a text/model combination."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()


class InMemoryCache(EmbeddingCache):
    """
    In-memory embedding cache.

    Suitable for development and single-instance deployments.
    For production multi-instance deployments, use Redis-based cache.
    """

    def __init__(self, config: CacheConfig | None = None):
        self.config = config or CacheConfig()
        self._cache: dict[str, CacheEntry] = {}

    async def get(self, text: str, model: str) -> list[float] | None:
        """Retrieve a cached embedding."""
        if not self.config.enabled:
            return None

        key = self.hash_text(text, model)
        entry = self._cache.get(key)

        if entry is None:
            return None

        if datetime.utcnow() > entry.expires_at:
            del self._cache[key]
            return None

        return entry.embedding

    async def get_batch(
        self, texts: list[str], model: str
    ) -> dict[str, list[float] | None]:
        """Retrieve multiple cached embeddings."""
        result: dict[str, list[float] | None] = {}
        for text in texts:
            result[text] = await self.get(text, model)
        return result

    async def set(
        self, text: str, model: str, embedding: list[float]
    ) -> None:
        """Cache an embedding."""
        if not self.config.enabled:
            return

        # Evict oldest entries if at capacity
        if len(self._cache) >= self.config.max_entries:
            await self._evict_oldest()

        key = self.hash_text(text, model)
        self._cache[key] = CacheEntry(
            text_hash=key,
            model=model,
            embedding=embedding,
            dimensions=len(embedding),
            expires_at=datetime.utcnow() + self.config.ttl,
        )

    async def set_batch(
        self, items: list[tuple[str, str, list[float]]]
    ) -> None:
        """Cache multiple embeddings."""
        for text, model, embedding in items:
            await self.set(text, model, embedding)

    async def invalidate(self, text: str, model: str) -> bool:
        """Invalidate a cached embedding."""
        key = self.hash_text(text, model)
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def clear(self) -> int:
        """Clear all cached embeddings."""
        count = len(self._cache)
        self._cache.clear()
        return count

    async def _evict_oldest(self) -> None:
        """Evict oldest 10% of entries when at capacity."""
        if not self._cache:
            return

        entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].created_at,
        )
        evict_count = max(1, len(entries) // 10)

        for key, _ in entries[:evict_count]:
            del self._cache[key]


class CachedEmbeddingProvider:
    """
    Wrapper that adds caching to any embedding provider.

    Example:
        provider = CachedEmbeddingProvider(
            provider=OpenAIEmbeddings(),
            cache=InMemoryCache(),
        )
    """

    def __init__(
        self,
        provider: Any,  # EmbeddingProvider protocol
        cache: EmbeddingCache,
    ):
        self.provider = provider
        self.cache = cache

    async def embed(self, request: Any) -> Any:  # EmbeddingRequest -> EmbeddingResponse
        """
        Generate embeddings with caching.

        First checks cache for existing embeddings, then calls
        the underlying provider for any misses.
        """
        from forge_vectors.embeddings.base import EmbeddingRequest, EmbeddingResponse

        # Check cache for all texts
        cached = await self.cache.get_batch(request.texts, request.model)

        # Identify cache hits and misses
        hits: dict[int, list[float]] = {}
        misses: list[tuple[int, str]] = []

        for i, text in enumerate(request.texts):
            if cached[text] is not None:
                hits[i] = cached[text]
            else:
                misses.append((i, text))

        # If all cached, return immediately
        if not misses:
            return EmbeddingResponse(
                embeddings=[hits[i] for i in range(len(request.texts))],
                model=request.model,
                dimensions=len(hits[0]) if hits else 0,
            )

        # Embed missing texts
        miss_texts = [text for _, text in misses]
        miss_request = EmbeddingRequest(
            texts=miss_texts,
            model=request.model,
            dimensions=request.dimensions,
            normalize=request.normalize,
        )
        miss_response = await self.provider.embed(miss_request)

        # Cache new embeddings
        cache_items = [
            (miss_texts[i], request.model, miss_response.embeddings[i])
            for i in range(len(miss_texts))
        ]
        await self.cache.set_batch(cache_items)

        # Merge results
        result_embeddings: list[list[float]] = []
        miss_idx = 0
        for i in range(len(request.texts)):
            if i in hits:
                result_embeddings.append(hits[i])
            else:
                result_embeddings.append(miss_response.embeddings[miss_idx])
                miss_idx += 1

        return EmbeddingResponse(
            embeddings=result_embeddings,
            model=miss_response.model,
            dimensions=miss_response.dimensions,
            usage=miss_response.usage,
            latency_ms=miss_response.latency_ms,
        )

    async def embed_text(self, text: str, model: str | None = None) -> list[float]:
        """Generate embedding for a single text with caching."""
        model = model or getattr(self.provider, 'config', {}).get('default_model', 'unknown')

        # Check cache first
        cached = await self.cache.get(text, model)
        if cached is not None:
            return cached

        # Generate and cache
        embedding = await self.provider.embed_text(text, model)
        await self.cache.set(text, model, embedding)
        return embedding

    def supported_models(self) -> list[Any]:
        """Delegate to underlying provider."""
        return self.provider.supported_models()

    async def health_check(self) -> bool:
        """Delegate to underlying provider."""
        return await self.provider.health_check()
