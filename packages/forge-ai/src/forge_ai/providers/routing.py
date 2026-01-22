"""
Model routing and fallback chains.

This module provides intelligent model selection, routing, and fallback
strategies for resilient LLM operations.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import structlog

from forge_ai.providers.base import (
    CompletionRequest,
    CompletionResponse,
    LLMProvider,
    ModelCapability,
    ModelNotAvailableError,
    ProviderError,
    RateLimitError,
)

logger = structlog.get_logger(__name__)


@dataclass
class RoutingConfig:
    """Configuration for model routing."""

    default_model: str = "gpt-4o"
    fallback_chain: list[str] = field(default_factory=lambda: ["claude-3-5-sonnet-20241022"])
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    cost_limit_usd: float | None = None
    prefer_provider: str | None = None  # Prefer specific provider when available


@dataclass
class FallbackChain:
    """
    A chain of models to try in sequence.

    Used when the primary model fails due to rate limiting or unavailability.
    """

    models: list[str]
    max_retries_per_model: int = 2

    @classmethod
    def default(cls) -> "FallbackChain":
        """Create the default fallback chain."""
        return cls(
            models=[
                "gpt-4o",
                "claude-3-5-sonnet-20241022",
                "gemini-1.5-pro",
                "gpt-4o-mini",
                "claude-3-5-haiku-20241022",
            ]
        )

    @classmethod
    def fast(cls) -> "FallbackChain":
        """Create a fallback chain optimized for speed."""
        return cls(
            models=[
                "gpt-4o-mini",
                "claude-3-5-haiku-20241022",
                "gemini-1.5-flash",
            ]
        )

    @classmethod
    def vision(cls) -> "FallbackChain":
        """Create a fallback chain for vision tasks."""
        return cls(
            models=[
                "gpt-4o",
                "claude-3-5-sonnet-20241022",
                "gemini-1.5-pro",
            ]
        )


class AllModelsFailedError(ProviderError):
    """Raised when all models in the fallback chain have failed."""

    def __init__(self, attempted_models: list[str], last_error: Exception | None = None):
        self.attempted_models = attempted_models
        self.last_error = last_error
        super().__init__(
            f"All models failed: {', '.join(attempted_models)}",
            provider="router",
        )


class ModelRouter:
    """
    Intelligent model router with fallback capabilities.

    Handles model selection based on:
    - Required capabilities (vision, tools, etc.)
    - Cost constraints
    - Provider preferences
    - Fallback on failure
    """

    def __init__(
        self,
        provider: LLMProvider,
        config: RoutingConfig | None = None,
    ):
        """
        Initialize the model router.

        Args:
            provider: The LLM provider to use for completions.
            config: Routing configuration.
        """
        self.provider = provider
        self.config = config or RoutingConfig()
        self._model_capabilities: dict[str, set[ModelCapability]] = {}
        self._initialize_capabilities()

    def _initialize_capabilities(self) -> None:
        """Initialize model capability mapping."""
        for model_info in self.provider.supported_models():
            self._model_capabilities[model_info.id] = set(model_info.capabilities)

    def select_model(
        self,
        request: CompletionRequest,
        required_capabilities: list[ModelCapability] | None = None,
    ) -> str:
        """
        Select the best model for a request.

        Args:
            request: The completion request.
            required_capabilities: Capabilities the model must have.

        Returns:
            The selected model ID.
        """
        # If model is explicitly specified, use it
        if request.model:
            return request.model

        required = set(required_capabilities or [])

        # Infer required capabilities from request
        if request.tools:
            required.add(ModelCapability.TOOLS)
        if self._has_images(request):
            required.add(ModelCapability.VISION)
        if request.response_format and request.response_format.type == "json_schema":
            required.add(ModelCapability.JSON_MODE)
        if request.stream:
            required.add(ModelCapability.STREAMING)

        # Find models with required capabilities
        suitable_models = [
            model_id
            for model_id, caps in self._model_capabilities.items()
            if required.issubset(caps)
        ]

        if not suitable_models:
            logger.warning(
                "No model found with required capabilities, using default",
                required=list(required),
            )
            return self.config.default_model

        # Prefer configured provider
        if self.config.prefer_provider:
            for model_info in self.provider.supported_models():
                if (
                    model_info.provider == self.config.prefer_provider
                    and model_info.id in suitable_models
                ):
                    return model_info.id

        # Use default if suitable, otherwise first suitable
        if self.config.default_model in suitable_models:
            return self.config.default_model

        return suitable_models[0]

    async def complete_with_fallback(
        self,
        request: CompletionRequest,
        fallback_chain: FallbackChain | None = None,
    ) -> CompletionResponse:
        """
        Execute completion with automatic fallback.

        Args:
            request: The completion request.
            fallback_chain: Custom fallback chain (uses default if not specified).

        Returns:
            CompletionResponse from the first successful model.

        Raises:
            AllModelsFailedError: If all models in the chain fail.
        """
        chain = fallback_chain or FallbackChain(
            models=[request.model or self.config.default_model] + self.config.fallback_chain
        )

        attempted_models: list[str] = []
        last_error: Exception | None = None

        for model in chain.models:
            for attempt in range(chain.max_retries_per_model):
                try:
                    request_copy = request.model_copy()
                    request_copy.model = model

                    logger.debug(
                        "Attempting completion",
                        model=model,
                        attempt=attempt + 1,
                    )

                    response = await self.provider.complete(request_copy)
                    return response

                except RateLimitError as e:
                    last_error = e
                    logger.warning(
                        "Rate limited, trying fallback",
                        model=model,
                        attempt=attempt + 1,
                        retry_after=e.retry_after,
                    )
                    # Move to next model immediately on rate limit
                    break

                except ModelNotAvailableError as e:
                    last_error = e
                    logger.warning("Model not available", model=model)
                    break

                except ProviderError as e:
                    last_error = e
                    logger.warning(
                        "Provider error, retrying",
                        model=model,
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    continue

            attempted_models.append(model)

        raise AllModelsFailedError(attempted_models, last_error)

    async def execute_with_routing(
        self,
        fn: Callable[[CompletionRequest], Awaitable[CompletionResponse]],
        request: CompletionRequest,
    ) -> CompletionResponse:
        """
        Execute a function with automatic model routing and fallback.

        This is a lower-level API that allows custom completion functions
        while still benefiting from routing and fallback.

        Args:
            fn: The async function to execute.
            request: The completion request.

        Returns:
            CompletionResponse from the execution.
        """
        models_to_try = [request.model or self.config.default_model] + self.config.fallback_chain
        attempted_models: list[str] = []
        last_error: Exception | None = None

        for model in models_to_try:
            try:
                request_copy = request.model_copy()
                request_copy.model = model
                return await fn(request_copy)

            except (RateLimitError, ModelNotAvailableError) as e:
                last_error = e
                attempted_models.append(model)
                continue

        raise AllModelsFailedError(attempted_models, last_error)

    def _has_images(self, request: CompletionRequest) -> bool:
        """Check if the request contains images."""
        for message in request.messages:
            content = message.content if hasattr(message, "content") else message.get("content")
            if isinstance(content, list):
                for block in content:
                    block_type = block.type if hasattr(block, "type") else block.get("type")
                    if block_type == "image":
                        return True
        return False

    def get_model_info(self, model_id: str) -> dict[str, Any] | None:
        """Get information about a specific model."""
        for model_info in self.provider.supported_models():
            if model_info.id == model_id:
                return model_info.model_dump()
        return None

    def list_models_with_capability(
        self, capability: ModelCapability
    ) -> list[str]:
        """List all models that have a specific capability."""
        return [
            model_id
            for model_id, caps in self._model_capabilities.items()
            if capability in caps
        ]
