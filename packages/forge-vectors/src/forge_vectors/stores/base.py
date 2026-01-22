"""
Base vector store types and VectorStore protocol.

This module defines the core abstractions for vector storage and retrieval.
All store implementations must conform to the VectorStore protocol.
"""

from abc import abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class DistanceMetric(str, Enum):
    """Distance metrics for vector similarity."""

    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"


class VectorStoreConfig(BaseModel):
    """Base configuration for vector stores."""

    collection_name: str = Field(..., description="Name of the collection/table")
    dimensions: int = Field(..., description="Vector dimensions")
    distance_metric: DistanceMetric = Field(
        default=DistanceMetric.COSINE,
        description="Distance metric for similarity search",
    )


class VectorDocument(BaseModel):
    """A document stored in the vector store."""

    id: str = Field(..., description="Unique document identifier")
    vector: list[float] = Field(..., description="Embedding vector")
    content: str = Field(..., description="Original text content")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (source, chunk_index, etc.)",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None


class VectorSearchResult(BaseModel):
    """A search result from the vector store."""

    document: VectorDocument
    score: float = Field(..., description="Similarity score")
    distance: float | None = Field(default=None, description="Raw distance value")


class CollectionInfo(BaseModel):
    """Information about a vector collection."""

    name: str
    dimensions: int
    distance_metric: DistanceMetric
    document_count: int
    index_type: str | None = None
    created_at: datetime | None = None


class IndexConfig(BaseModel):
    """Configuration for vector index creation."""

    index_type: str = Field(
        default="ivfflat",
        description="Index type (ivfflat, hnsw for pgvector)",
    )
    lists: int = Field(
        default=100,
        description="Number of lists for IVFFlat index",
    )
    m: int = Field(
        default=16,
        description="HNSW M parameter (max connections per node)",
    )
    ef_construction: int = Field(
        default=64,
        description="HNSW ef_construction parameter",
    )


@runtime_checkable
class VectorStore(Protocol):
    """
    Protocol for vector stores.

    All vector store implementations must implement this protocol to ensure
    consistent behavior across different backends (pgvector, Qdrant, etc.).
    """

    @abstractmethod
    async def create_collection(
        self,
        name: str,
        dimensions: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        index_config: IndexConfig | None = None,
    ) -> None:
        """
        Create a new vector collection.

        Args:
            name: Collection name.
            dimensions: Vector dimensions.
            distance_metric: Distance metric for similarity search.
            index_config: Optional index configuration.

        Raises:
            VectorStoreError: If collection creation fails.
        """
        ...

    @abstractmethod
    async def delete_collection(self, name: str) -> bool:
        """
        Delete a vector collection.

        Args:
            name: Collection name to delete.

        Returns:
            True if collection was deleted, False if not found.
        """
        ...

    @abstractmethod
    async def list_collections(self) -> list[CollectionInfo]:
        """
        List all vector collections.

        Returns:
            List of CollectionInfo describing each collection.
        """
        ...

    @abstractmethod
    async def collection_exists(self, name: str) -> bool:
        """
        Check if a collection exists.

        Args:
            name: Collection name.

        Returns:
            True if collection exists.
        """
        ...

    @abstractmethod
    async def upsert(
        self,
        collection: str,
        documents: list[VectorDocument],
    ) -> int:
        """
        Insert or update documents in a collection.

        Args:
            collection: Collection name.
            documents: Documents to upsert.

        Returns:
            Number of documents upserted.
        """
        ...

    @abstractmethod
    async def delete(
        self,
        collection: str,
        ids: list[str],
    ) -> int:
        """
        Delete documents by ID.

        Args:
            collection: Collection name.
            ids: Document IDs to delete.

        Returns:
            Number of documents deleted.
        """
        ...

    @abstractmethod
    async def get(
        self,
        collection: str,
        ids: list[str],
    ) -> list[VectorDocument | None]:
        """
        Retrieve documents by ID.

        Args:
            collection: Collection name.
            ids: Document IDs to retrieve.

        Returns:
            List of documents (None for missing IDs).
        """
        ...

    @abstractmethod
    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 10,
        filter: dict[str, Any] | None = None,
        include_vectors: bool = False,
    ) -> list[VectorSearchResult]:
        """
        Search for similar vectors.

        Args:
            collection: Collection name.
            vector: Query vector.
            limit: Maximum number of results.
            filter: Optional metadata filter.
            include_vectors: Whether to include vectors in results.

        Returns:
            List of search results sorted by similarity.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the store is healthy and accessible.

        Returns:
            True if healthy, False otherwise.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """
        Close the connection and release resources.
        """
        ...


class VectorStoreError(Exception):
    """Base exception for vector store errors."""

    def __init__(self, message: str, store: str):
        self.store = store
        super().__init__(f"[{store}] {message}")


class CollectionNotFoundError(VectorStoreError):
    """Raised when a collection is not found."""

    def __init__(self, collection: str, store: str):
        self.collection = collection
        super().__init__(f"Collection '{collection}' not found", store)


class DocumentNotFoundError(VectorStoreError):
    """Raised when a document is not found."""

    def __init__(self, document_id: str, store: str):
        self.document_id = document_id
        super().__init__(f"Document '{document_id}' not found", store)
