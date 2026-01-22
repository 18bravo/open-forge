"""Tests for embedding providers."""

import pytest

from forge_vectors.embeddings.base import (
    EmbeddingModel,
    EmbeddingModelType,
    EmbeddingRequest,
    EmbeddingResponse,
    TokenUsage,
)


class TestEmbeddingModels:
    """Tests for embedding data models."""

    def test_embedding_request(self):
        """EmbeddingRequest model validation."""
        request = EmbeddingRequest(
            texts=["Hello world", "Test text"],
            model="text-embedding-3-small",
        )
        assert len(request.texts) == 2
        assert request.model == "text-embedding-3-small"
        assert request.normalize is True  # Default

    def test_embedding_response(self):
        """EmbeddingResponse model validation."""
        response = EmbeddingResponse(
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            model="text-embedding-3-small",
            dimensions=3,
            usage=TokenUsage(prompt_tokens=10, total_tokens=10),
        )
        assert len(response.embeddings) == 2
        assert response.dimensions == 3
        assert response.usage.total_tokens == 10

    def test_embedding_response_to_numpy(self):
        """to_numpy converts embeddings to numpy array."""
        response = EmbeddingResponse(
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            model="test",
            dimensions=2,
        )
        arr = response.to_numpy()

        assert arr.shape == (2, 2)
        assert arr.dtype.name.startswith("float")

    def test_embedding_model(self):
        """EmbeddingModel stores model metadata."""
        model = EmbeddingModel(
            id="text-embedding-3-small",
            provider=EmbeddingModelType.OPENAI,
            dimensions=1536,
            max_tokens=8191,
            cost_per_1k_tokens=0.00002,
        )
        assert model.id == "text-embedding-3-small"
        assert model.dimensions == 1536
        assert model.supports_batching is True  # Default


class TestEmbeddingProviderProtocol:
    """Tests for EmbeddingProvider protocol compliance."""

    def test_protocol_is_runtime_checkable(self):
        """EmbeddingProvider can be checked at runtime."""
        from forge_vectors.embeddings.base import EmbeddingProvider

        # Protocol should be importable and runtime checkable
        assert hasattr(EmbeddingProvider, "__protocol_attrs__") or hasattr(
            EmbeddingProvider, "_is_protocol"
        )


# Integration tests would go here, requiring actual embedding providers
# These would be in tests/integration/ and marked with pytest.mark.integration
