"""
Forge Vectors - Vector Storage, Embeddings, and Semantic Search for Open Forge

This package provides:
- embeddings/: Embedding providers (OpenAI, Sentence Transformers) with caching
- stores/: Vector stores (pgvector primary, Qdrant optional)
- search/: k-NN search, hybrid keyword + semantic search, result reranking
- chunking/: Text chunking strategies for document processing
"""

from forge_vectors.embeddings.base import (
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingModel,
)
from forge_vectors.stores.base import (
    VectorStore,
    VectorDocument,
    VectorSearchResult,
    VectorStoreConfig,
)
from forge_vectors.search.base import (
    SearchEngine,
    SearchQuery,
    SearchResult,
    SearchMode,
)
from forge_vectors.chunking.base import (
    ChunkingStrategy,
    TextChunk,
    ChunkingConfig,
)

__version__ = "0.1.0"

__all__ = [
    # Embeddings
    "EmbeddingProvider",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "EmbeddingModel",
    # Vector Stores
    "VectorStore",
    "VectorDocument",
    "VectorSearchResult",
    "VectorStoreConfig",
    # Search
    "SearchEngine",
    "SearchQuery",
    "SearchResult",
    "SearchMode",
    # Chunking
    "ChunkingStrategy",
    "TextChunk",
    "ChunkingConfig",
]
