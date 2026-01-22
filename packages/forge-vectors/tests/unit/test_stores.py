"""Tests for vector store interfaces."""

import pytest
from datetime import datetime

from forge_vectors.stores.base import (
    CollectionInfo,
    DistanceMetric,
    IndexConfig,
    VectorDocument,
    VectorSearchResult,
    VectorStoreConfig,
    VectorStoreError,
    CollectionNotFoundError,
)


class TestVectorStoreModels:
    """Tests for vector store data models."""

    def test_vector_document(self):
        """VectorDocument model validation."""
        doc = VectorDocument(
            id="doc-123",
            vector=[0.1, 0.2, 0.3],
            content="Test content",
            metadata={"source": "test"},
        )
        assert doc.id == "doc-123"
        assert len(doc.vector) == 3
        assert doc.content == "Test content"
        assert doc.metadata["source"] == "test"
        assert doc.created_at is not None

    def test_vector_search_result(self):
        """VectorSearchResult model validation."""
        doc = VectorDocument(
            id="doc-123",
            vector=[0.1, 0.2],
            content="Test",
        )
        result = VectorSearchResult(
            document=doc,
            score=0.95,
            distance=0.05,
        )
        assert result.score == 0.95
        assert result.distance == 0.05
        assert result.document.id == "doc-123"

    def test_collection_info(self):
        """CollectionInfo model validation."""
        info = CollectionInfo(
            name="test-collection",
            dimensions=1536,
            distance_metric=DistanceMetric.COSINE,
            document_count=1000,
        )
        assert info.name == "test-collection"
        assert info.dimensions == 1536
        assert info.document_count == 1000

    def test_index_config_defaults(self):
        """IndexConfig has sensible defaults."""
        config = IndexConfig()
        assert config.index_type == "ivfflat"
        assert config.lists == 100
        assert config.m == 16  # HNSW parameter
        assert config.ef_construction == 64

    def test_vector_store_config(self):
        """VectorStoreConfig model validation."""
        config = VectorStoreConfig(
            collection_name="documents",
            dimensions=768,
            distance_metric=DistanceMetric.EUCLIDEAN,
        )
        assert config.collection_name == "documents"
        assert config.dimensions == 768
        assert config.distance_metric == DistanceMetric.EUCLIDEAN


class TestDistanceMetrics:
    """Tests for distance metric enum."""

    def test_distance_metrics_defined(self):
        """All expected distance metrics are defined."""
        assert DistanceMetric.COSINE == "cosine"
        assert DistanceMetric.EUCLIDEAN == "euclidean"
        assert DistanceMetric.DOT_PRODUCT == "dot_product"

    def test_distance_metric_values(self):
        """Distance metric values are strings."""
        for metric in DistanceMetric:
            assert isinstance(metric.value, str)


class TestVectorStoreErrors:
    """Tests for vector store exceptions."""

    def test_vector_store_error(self):
        """VectorStoreError includes store name."""
        error = VectorStoreError("Connection failed", store="pgvector")
        assert "pgvector" in str(error)
        assert "Connection failed" in str(error)
        assert error.store == "pgvector"

    def test_collection_not_found_error(self):
        """CollectionNotFoundError includes collection name."""
        error = CollectionNotFoundError(collection="documents", store="pgvector")
        assert error.collection == "documents"
        assert "documents" in str(error)


class TestVectorStoreProtocol:
    """Tests for VectorStore protocol compliance."""

    def test_protocol_is_runtime_checkable(self):
        """VectorStore can be checked at runtime."""
        from forge_vectors.stores.base import VectorStore

        # Protocol should be importable and runtime checkable
        assert hasattr(VectorStore, "__protocol_attrs__") or hasattr(
            VectorStore, "_is_protocol"
        )
