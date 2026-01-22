"""
Qdrant vector store implementation (optional).

Qdrant is a high-performance vector database optimized for similarity search.
This implementation requires the 'qdrant' optional dependency:
    pip install forge-vectors[qdrant]
"""

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, Field

from forge_vectors.stores.base import (
    CollectionInfo,
    CollectionNotFoundError,
    DistanceMetric,
    IndexConfig,
    VectorDocument,
    VectorSearchResult,
    VectorStore,
    VectorStoreError,
)


class QdrantConfig(BaseModel):
    """Configuration for Qdrant vector store."""

    host: str = Field(default="localhost", description="Qdrant host")
    port: int = Field(default=6333, description="Qdrant REST port")
    grpc_port: int | None = Field(default=6334, description="Qdrant gRPC port")
    api_key: str | None = Field(default=None, description="API key for Qdrant Cloud")
    url: str | None = Field(default=None, description="Full URL (overrides host/port)")
    prefer_grpc: bool = Field(default=True, description="Use gRPC when available")
    timeout: float = Field(default=30.0, description="Request timeout")


class QdrantVectorStore:
    """
    Qdrant implementation of VectorStore.

    Qdrant is a vector similarity search engine with extended filtering support.
    It can be run locally or as a managed service (Qdrant Cloud).

    Example:
        store = QdrantVectorStore(config=QdrantConfig(
            host="localhost",
            port=6333,
        ))
        await store.connect()

        await store.create_collection(
            name="documents",
            dimensions=1536,
            distance_metric=DistanceMetric.COSINE,
        )

        await store.upsert("documents", [
            VectorDocument(
                id="doc1",
                vector=[0.1, 0.2, ...],
                content="Hello world",
                metadata={"source": "test"},
            )
        ])
    """

    def __init__(self, config: QdrantConfig | None = None):
        self.config = config or QdrantConfig()
        self._client: Any = None  # qdrant_client.QdrantClient

    async def connect(self) -> None:
        """
        Connect to Qdrant.

        Raises:
            VectorStoreError: If connection fails.
        """
        try:
            from qdrant_client import QdrantClient
        except ImportError as e:
            raise VectorStoreError(
                "qdrant-client package required. Install with: pip install forge-vectors[qdrant]",
                store="qdrant",
            ) from e

        try:
            if self.config.url:
                self._client = QdrantClient(
                    url=self.config.url,
                    api_key=self.config.api_key,
                    timeout=self.config.timeout,
                    prefer_grpc=self.config.prefer_grpc,
                )
            else:
                self._client = QdrantClient(
                    host=self.config.host,
                    port=self.config.port,
                    grpc_port=self.config.grpc_port,
                    api_key=self.config.api_key,
                    timeout=self.config.timeout,
                    prefer_grpc=self.config.prefer_grpc,
                )
        except Exception as e:
            raise VectorStoreError(f"Failed to connect: {e}", store="qdrant") from e

    async def create_collection(
        self,
        name: str,
        dimensions: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        index_config: IndexConfig | None = None,
    ) -> None:
        """Create a new vector collection."""
        if not self._client:
            raise VectorStoreError("Not connected. Call connect() first.", store="qdrant")

        try:
            from qdrant_client.models import Distance, VectorParams
        except ImportError as e:
            raise VectorStoreError(
                "qdrant-client package required",
                store="qdrant",
            ) from e

        # Map distance metric
        distance_map = {
            DistanceMetric.COSINE: Distance.COSINE,
            DistanceMetric.EUCLIDEAN: Distance.EUCLID,
            DistanceMetric.DOT_PRODUCT: Distance.DOT,
        }

        try:
            self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=dimensions,
                    distance=distance_map[distance_metric],
                ),
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to create collection: {e}", store="qdrant") from e

    async def delete_collection(self, name: str) -> bool:
        """Delete a vector collection."""
        if not self._client:
            raise VectorStoreError("Not connected", store="qdrant")

        try:
            self._client.delete_collection(collection_name=name)
            return True
        except Exception:
            return False

    async def list_collections(self) -> list[CollectionInfo]:
        """List all vector collections."""
        if not self._client:
            raise VectorStoreError("Not connected", store="qdrant")

        collections = self._client.get_collections().collections
        result = []

        for coll in collections:
            info = self._client.get_collection(coll.name)
            result.append(
                CollectionInfo(
                    name=coll.name,
                    dimensions=info.config.params.vectors.size,
                    distance_metric=DistanceMetric.COSINE,  # Would need to map back
                    document_count=info.points_count,
                )
            )

        return result

    async def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        if not self._client:
            raise VectorStoreError("Not connected", store="qdrant")

        try:
            self._client.get_collection(name)
            return True
        except Exception:
            return False

    async def upsert(
        self,
        collection: str,
        documents: list[VectorDocument],
    ) -> int:
        """Insert or update documents."""
        if not self._client:
            raise VectorStoreError("Not connected", store="qdrant")

        if not documents:
            return 0

        try:
            from qdrant_client.models import PointStruct
        except ImportError as e:
            raise VectorStoreError(
                "qdrant-client package required",
                store="qdrant",
            ) from e

        points = []
        for doc in documents:
            # Include content in metadata for retrieval
            payload = {
                **doc.metadata,
                "_content": doc.content,
                "_created_at": doc.created_at.isoformat(),
            }
            if doc.updated_at:
                payload["_updated_at"] = doc.updated_at.isoformat()

            points.append(
                PointStruct(
                    id=doc.id,
                    vector=doc.vector,
                    payload=payload,
                )
            )

        self._client.upsert(
            collection_name=collection,
            points=points,
        )

        return len(documents)

    async def delete(
        self,
        collection: str,
        ids: list[str],
    ) -> int:
        """Delete documents by ID."""
        if not self._client:
            raise VectorStoreError("Not connected", store="qdrant")

        if not ids:
            return 0

        self._client.delete(
            collection_name=collection,
            points_selector=ids,
        )

        return len(ids)  # Qdrant doesn't return actual delete count

    async def get(
        self,
        collection: str,
        ids: list[str],
    ) -> list[VectorDocument | None]:
        """Retrieve documents by ID."""
        if not self._client:
            raise VectorStoreError("Not connected", store="qdrant")

        if not ids:
            return []

        points = self._client.retrieve(
            collection_name=collection,
            ids=ids,
            with_vectors=True,
        )

        # Build lookup
        docs_by_id: dict[str, VectorDocument] = {}
        for point in points:
            payload = point.payload or {}
            docs_by_id[str(point.id)] = VectorDocument(
                id=str(point.id),
                vector=point.vector,
                content=payload.pop("_content", ""),
                metadata={k: v for k, v in payload.items() if not k.startswith("_")},
                created_at=datetime.fromisoformat(payload.get("_created_at", datetime.utcnow().isoformat())),
                updated_at=datetime.fromisoformat(payload["_updated_at"]) if payload.get("_updated_at") else None,
            )

        return [docs_by_id.get(id_) for id_ in ids]

    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 10,
        filter: dict[str, Any] | None = None,
        include_vectors: bool = False,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors."""
        if not self._client:
            raise VectorStoreError("Not connected", store="qdrant")

        # Build filter if specified
        query_filter = None
        if filter:
            try:
                from qdrant_client.models import FieldCondition, Filter, MatchValue
            except ImportError:
                pass
            else:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter.items()
                ]
                query_filter = Filter(must=conditions)

        results = self._client.search(
            collection_name=collection,
            query_vector=vector,
            limit=limit,
            query_filter=query_filter,
            with_vectors=include_vectors,
        )

        search_results = []
        for point in results:
            payload = point.payload or {}
            doc = VectorDocument(
                id=str(point.id),
                vector=point.vector if include_vectors else [],
                content=payload.pop("_content", ""),
                metadata={k: v for k, v in payload.items() if not k.startswith("_")},
            )
            search_results.append(
                VectorSearchResult(
                    document=doc,
                    score=point.score,
                )
            )

        return search_results

    async def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        if not self._client:
            return False

        try:
            self._client.get_collections()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the client connection."""
        if self._client:
            self._client.close()
            self._client = None

    async def __aenter__(self) -> "QdrantVectorStore":
        """Support async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up on context exit."""
        await self.close()
