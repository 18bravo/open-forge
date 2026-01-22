"""
Embedding provider implementations.

This module provides concrete implementations of the EmbeddingProvider protocol:
- OpenAIEmbeddings: OpenAI's text-embedding models
- SentenceTransformerEmbeddings: Local Sentence Transformers models (optional)
"""

from datetime import datetime
import time
from typing import Any

from pydantic import BaseModel, Field

from forge_vectors.embeddings.base import (
    EmbeddingModel,
    EmbeddingModelType,
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingError,
    RateLimitError,
    TokenUsage,
)


class OpenAIEmbeddingsConfig(BaseModel):
    """Configuration for OpenAI embeddings provider."""

    api_key: str | None = Field(default=None, description="OpenAI API key (or use env var)")
    default_model: str = Field(
        default="text-embedding-3-small",
        description="Default model to use",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")


class OpenAIEmbeddings:
    """
    OpenAI embeddings provider.

    Supports text-embedding-3-small, text-embedding-3-large, and ada-002 models.

    Example:
        provider = OpenAIEmbeddings(config=OpenAIEmbeddingsConfig())
        response = await provider.embed(EmbeddingRequest(
            texts=["Hello world"],
            model="text-embedding-3-small"
        ))
    """

    def __init__(self, config: OpenAIEmbeddingsConfig | None = None):
        self.config = config or OpenAIEmbeddingsConfig()
        self._client: Any = None  # Lazy-loaded openai.AsyncOpenAI

    async def _get_client(self) -> Any:
        """Get or create the OpenAI async client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as e:
                raise EmbeddingError(
                    "openai package required. Install with: pip install openai",
                    provider="openai",
                ) from e

            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        return self._client

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings using OpenAI's API.

        Args:
            request: The embedding request.

        Returns:
            EmbeddingResponse with generated vectors.
        """
        client = await self._get_client()
        model = request.model or self.config.default_model
        start_time = time.monotonic()

        try:
            # Build API request
            api_kwargs: dict[str, Any] = {
                "input": request.texts,
                "model": model,
            }
            if request.dimensions is not None:
                api_kwargs["dimensions"] = request.dimensions

            response = await client.embeddings.create(**api_kwargs)

            latency_ms = (time.monotonic() - start_time) * 1000

            # Extract embeddings
            embeddings = [item.embedding for item in response.data]

            return EmbeddingResponse(
                embeddings=embeddings,
                model=response.model,
                dimensions=len(embeddings[0]) if embeddings else 0,
                usage=TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    total_tokens=response.usage.total_tokens,
                ),
                latency_ms=latency_ms,
            )

        except Exception as e:
            # TODO: Implement proper error handling for rate limits, auth errors, etc.
            raise EmbeddingError(str(e), provider="openai", model=model) from e

    async def embed_text(self, text: str, model: str | None = None) -> list[float]:
        """Generate embedding for a single text."""
        response = await self.embed(
            EmbeddingRequest(
                texts=[text],
                model=model or self.config.default_model,
            )
        )
        return response.embeddings[0]

    def supported_models(self) -> list[EmbeddingModel]:
        """Return list of supported OpenAI embedding models."""
        return [
            EmbeddingModel(
                id="text-embedding-3-small",
                provider=EmbeddingModelType.OPENAI,
                display_name="Text Embedding 3 Small",
                dimensions=1536,
                max_tokens=8191,
                cost_per_1k_tokens=0.00002,
            ),
            EmbeddingModel(
                id="text-embedding-3-large",
                provider=EmbeddingModelType.OPENAI,
                display_name="Text Embedding 3 Large",
                dimensions=3072,
                max_tokens=8191,
                cost_per_1k_tokens=0.00013,
            ),
            EmbeddingModel(
                id="text-embedding-ada-002",
                provider=EmbeddingModelType.OPENAI,
                display_name="Ada 002",
                dimensions=1536,
                max_tokens=8191,
                cost_per_1k_tokens=0.0001,
            ),
        ]

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            await self.embed_text("health check", model="text-embedding-3-small")
            return True
        except Exception:
            return False


class SentenceTransformerConfig(BaseModel):
    """Configuration for Sentence Transformers provider."""

    model_name: str = Field(
        default="all-MiniLM-L6-v2",
        description="Hugging Face model name",
    )
    device: str | None = Field(
        default=None,
        description="Device to use (cuda, cpu, mps). Auto-detected if None.",
    )
    normalize_embeddings: bool = Field(
        default=True,
        description="Whether to normalize output embeddings",
    )


class SentenceTransformerEmbeddings:
    """
    Local Sentence Transformers embeddings provider.

    Requires the 'local' optional dependency:
        pip install forge-vectors[local]

    Example:
        provider = SentenceTransformerEmbeddings(
            config=SentenceTransformerConfig(model_name="all-MiniLM-L6-v2")
        )
        response = await provider.embed(EmbeddingRequest(
            texts=["Hello world"],
            model="all-MiniLM-L6-v2"
        ))
    """

    def __init__(self, config: SentenceTransformerConfig | None = None):
        self.config = config or SentenceTransformerConfig()
        self._model: Any = None  # Lazy-loaded SentenceTransformer

    def _get_model(self) -> Any:
        """Get or create the Sentence Transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise EmbeddingError(
                    "sentence-transformers package required. "
                    "Install with: pip install forge-vectors[local]",
                    provider="sentence_transformers",
                ) from e

            self._model = SentenceTransformer(
                self.config.model_name,
                device=self.config.device,
            )
        return self._model

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings using Sentence Transformers.

        Note: This runs synchronously but is wrapped for async interface consistency.
        """
        model = self._get_model()
        start_time = time.monotonic()

        try:
            # Encode texts
            embeddings = model.encode(
                request.texts,
                normalize_embeddings=request.normalize,
                convert_to_numpy=True,
            )

            latency_ms = (time.monotonic() - start_time) * 1000

            return EmbeddingResponse(
                embeddings=embeddings.tolist(),
                model=self.config.model_name,
                dimensions=embeddings.shape[1],
                latency_ms=latency_ms,
            )

        except Exception as e:
            raise EmbeddingError(
                str(e),
                provider="sentence_transformers",
                model=self.config.model_name,
            ) from e

    async def embed_text(self, text: str, model: str | None = None) -> list[float]:
        """Generate embedding for a single text."""
        response = await self.embed(
            EmbeddingRequest(
                texts=[text],
                model=model or self.config.model_name,
            )
        )
        return response.embeddings[0]

    def supported_models(self) -> list[EmbeddingModel]:
        """Return common Sentence Transformer models."""
        return [
            EmbeddingModel(
                id="all-MiniLM-L6-v2",
                provider=EmbeddingModelType.SENTENCE_TRANSFORMERS,
                display_name="MiniLM L6 v2",
                dimensions=384,
                max_tokens=512,
            ),
            EmbeddingModel(
                id="all-mpnet-base-v2",
                provider=EmbeddingModelType.SENTENCE_TRANSFORMERS,
                display_name="MPNet Base v2",
                dimensions=768,
                max_tokens=512,
            ),
            EmbeddingModel(
                id="multi-qa-MiniLM-L6-cos-v1",
                provider=EmbeddingModelType.SENTENCE_TRANSFORMERS,
                display_name="Multi-QA MiniLM",
                dimensions=384,
                max_tokens=512,
            ),
        ]

    async def health_check(self) -> bool:
        """Check if model is loaded and working."""
        try:
            self._get_model()
            return True
        except Exception:
            return False
