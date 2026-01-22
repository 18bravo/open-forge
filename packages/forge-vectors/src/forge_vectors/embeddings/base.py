"""
Base embedding provider types and EmbeddingProvider protocol.

This module defines the core abstractions for generating embeddings.
All provider implementations must conform to the EmbeddingProvider protocol.
"""

from abc import abstractmethod
from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field


class EmbeddingModelType(str, Enum):
    """Types of embedding models by provider."""

    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    COHERE = "cohere"
    CUSTOM = "custom"


class EmbeddingModel(BaseModel):
    """Information about an available embedding model."""

    id: str = Field(..., description="Model identifier (e.g., 'text-embedding-3-small')")
    provider: EmbeddingModelType
    display_name: str | None = None
    dimensions: int = Field(..., description="Output vector dimensions")
    max_tokens: int = Field(..., description="Maximum input tokens")
    supports_batching: bool = True
    cost_per_1k_tokens: float | None = Field(
        default=None, description="USD per 1k tokens"
    )


class EmbeddingRequest(BaseModel):
    """Request for generating embeddings."""

    texts: list[str] = Field(..., description="Texts to embed")
    model: str = Field(..., description="Model identifier to use")
    dimensions: int | None = Field(
        default=None,
        description="Output dimensions (for models that support dimensionality reduction)",
    )
    normalize: bool = Field(
        default=True, description="Whether to normalize output vectors"
    )

    # Forge-specific context
    user_id: str | None = None
    request_id: str | None = None


class TokenUsage(BaseModel):
    """Token usage information from an embedding request."""

    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(BaseModel):
    """Response from an embedding request."""

    embeddings: list[list[float]] = Field(..., description="Generated embedding vectors")
    model: str
    dimensions: int
    usage: TokenUsage | None = None
    latency_ms: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True

    def to_numpy(self) -> NDArray[np.float32]:
        """Convert embeddings to numpy array."""
        return np.array(self.embeddings, dtype=np.float32)


@runtime_checkable
class EmbeddingProvider(Protocol):
    """
    Protocol for embedding providers.

    All embedding provider implementations must implement this protocol to ensure
    consistent behavior across different providers (OpenAI, Sentence Transformers, etc.).
    """

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings for the given texts.

        Args:
            request: The embedding request with texts and parameters.

        Returns:
            EmbeddingResponse with the generated vectors.

        Raises:
            EmbeddingError: If embedding generation fails.
            RateLimitError: If rate limited by the provider.
        """
        ...

    @abstractmethod
    async def embed_text(self, text: str, model: str | None = None) -> list[float]:
        """
        Generate embedding for a single text (convenience method).

        Args:
            text: Single text to embed.
            model: Optional model override.

        Returns:
            Embedding vector as a list of floats.
        """
        ...

    @abstractmethod
    def supported_models(self) -> list[EmbeddingModel]:
        """
        Get the list of models supported by this provider.

        Returns:
            List of EmbeddingModel describing available models.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and accessible.

        Returns:
            True if the provider is healthy, False otherwise.
        """
        ...


class EmbeddingError(Exception):
    """Base exception for embedding errors."""

    def __init__(self, message: str, provider: str, model: str | None = None):
        self.provider = provider
        self.model = model
        super().__init__(f"[{provider}] {message}")


class RateLimitError(EmbeddingError):
    """Raised when rate limited by a provider."""

    def __init__(
        self,
        message: str,
        provider: str,
        retry_after: float | None = None,
        model: str | None = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, provider, model)


class ModelNotAvailableError(EmbeddingError):
    """Raised when the requested model is not available."""

    pass
