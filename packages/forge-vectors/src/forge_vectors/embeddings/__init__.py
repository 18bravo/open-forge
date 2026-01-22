"""
Embedding providers and caching.

This module provides:
- EmbeddingProvider protocol for embedding generation
- OpenAI embeddings implementation
- Sentence Transformers local embeddings (optional)
- Embedding cache for performance optimization
"""

from forge_vectors.embeddings.base import (
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingModel,
    EmbeddingError,
)

__all__ = [
    "EmbeddingProvider",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "EmbeddingModel",
    "EmbeddingError",
]
