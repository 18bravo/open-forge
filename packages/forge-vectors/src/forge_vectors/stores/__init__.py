"""
Vector store implementations.

This module provides:
- VectorStore protocol for vector storage and retrieval
- pgvector: PostgreSQL with pgvector extension (primary implementation)
- qdrant: Qdrant vector database (optional)
"""

from forge_vectors.stores.base import (
    VectorStore,
    VectorDocument,
    VectorSearchResult,
    VectorStoreConfig,
    VectorStoreError,
    CollectionNotFoundError,
    DocumentNotFoundError,
)

__all__ = [
    "VectorStore",
    "VectorDocument",
    "VectorSearchResult",
    "VectorStoreConfig",
    "VectorStoreError",
    "CollectionNotFoundError",
    "DocumentNotFoundError",
]
