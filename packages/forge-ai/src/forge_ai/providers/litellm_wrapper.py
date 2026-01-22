"""
LiteLLM wrapper for unified LLM access.

This module provides a LiteLLM-based implementation of the LLMProvider protocol,
enabling access to 100+ LLM providers through a unified interface.
"""

import time
from collections.abc import AsyncIterator
from typing import Any

import structlog

from forge_ai.providers.base import (
    CompletionRequest,
    CompletionResponse,
    LLMProvider,
    ModelCapability,
    ModelInfo,
    ProviderError,
    RateLimitError,
    StreamChunk,
    TokenUsage,
    ToolCall,
)

logger = structlog.get_logger(__name__)


class LiteLLMConfig:
    """Configuration for LiteLLM provider."""

    def __init__(
        self,
        *,
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None,
        google_api_key: str | None = None,
        azure_api_key: str | None = None,
        azure_api_base: str | None = None,
        azure_api_version: str | None = None,
        default_model: str = "gpt-4o",
        debug: bool = False,
        drop_params: bool = True,
        timeout: float = 60.0,
    ):
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.google_api_key = google_api_key
        self.azure_api_key = azure_api_key
        self.azure_api_base = azure_api_base
        self.azure_api_version = azure_api_version
        self.default_model = default_model
        self.debug = debug
        self.drop_params = drop_params
        self.timeout = timeout


class LiteLLMProvider(LLMProvider):
    """
    LiteLLM-based LLM provider.

    Provides access to 100+ LLM providers through LiteLLM's unified interface.
    Handles authentication, request formatting, and response parsing.
    """

    def __init__(self, config: LiteLLMConfig | None = None):
        """
        Initialize the LiteLLM provider.

        Args:
            config: Configuration for the provider. If None, will use environment variables.
        """
        self.config = config or LiteLLMConfig()
        self._setup_credentials()
        self._initialized = False

    def _setup_credentials(self) -> None:
        """Set up credentials from config or environment."""
        # Lazy import to avoid import errors if litellm is not installed
        try:
            import litellm

            litellm.set_verbose = self.config.debug
            litellm.drop_params = self.config.drop_params

            # Set API keys if provided
            if self.config.openai_api_key:
                litellm.openai_key = self.config.openai_api_key
            if self.config.anthropic_api_key:
                litellm.anthropic_key = self.config.anthropic_api_key

            self._litellm = litellm
            self._initialized = True
        except ImportError:
            logger.warning("litellm not installed, provider will not function")
            self._litellm = None
            self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure the provider is initialized."""
        if not self._initialized or self._litellm is None:
            raise ProviderError(
                "LiteLLM provider not initialized. Ensure litellm is installed.",
                provider="litellm",
            )

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """
        Execute a completion request via LiteLLM.

        Args:
            request: The completion request.

        Returns:
            CompletionResponse with the generated content.
        """
        self._ensure_initialized()

        start_time = time.perf_counter()

        try:
            # Convert messages to LiteLLM format
            messages = self._convert_messages(request.messages)

            # Build kwargs
            kwargs: dict[str, Any] = {
                "model": request.model,
                "messages": messages,
                "temperature": request.temperature,
                "stream": False,
                "timeout": self.config.timeout,
            }

            if request.max_tokens:
                kwargs["max_tokens"] = request.max_tokens
            if request.tools:
                kwargs["tools"] = self._convert_tools(request.tools)
            if request.response_format:
                kwargs["response_format"] = self._convert_response_format(request.response_format)
            if request.top_p is not None:
                kwargs["top_p"] = request.top_p
            if request.stop:
                kwargs["stop"] = request.stop

            # Execute completion
            response = await self._litellm.acompletion(**kwargs)

            latency_ms = (time.perf_counter() - start_time) * 1000

            return self._parse_response(response, latency_ms)

        except Exception as e:
            self._handle_error(e, request.model)
            raise  # Re-raise after handling (for type checker)

    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]:
        """
        Execute a streaming completion request.

        Args:
            request: The completion request.

        Yields:
            StreamChunk with partial content.
        """
        self._ensure_initialized()

        try:
            messages = self._convert_messages(request.messages)

            kwargs: dict[str, Any] = {
                "model": request.model,
                "messages": messages,
                "temperature": request.temperature,
                "stream": True,
                "timeout": self.config.timeout,
            }

            if request.max_tokens:
                kwargs["max_tokens"] = request.max_tokens
            if request.tools:
                kwargs["tools"] = self._convert_tools(request.tools)

            response = await self._litellm.acompletion(**kwargs)

            async for chunk in response:
                yield self._parse_stream_chunk(chunk)

        except Exception as e:
            self._handle_error(e, request.model)
            raise

    def supported_models(self) -> list[ModelInfo]:
        """Get the list of supported models."""
        return [
            ModelInfo(
                id="gpt-4o",
                provider="openai",
                display_name="GPT-4o",
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.VISION,
                    ModelCapability.TOOLS,
                    ModelCapability.JSON_MODE,
                    ModelCapability.STREAMING,
                ],
                context_window=128000,
                input_cost_per_1k=0.005,
                output_cost_per_1k=0.015,
            ),
            ModelInfo(
                id="gpt-4o-mini",
                provider="openai",
                display_name="GPT-4o Mini",
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.TOOLS,
                    ModelCapability.JSON_MODE,
                    ModelCapability.STREAMING,
                ],
                context_window=128000,
                input_cost_per_1k=0.00015,
                output_cost_per_1k=0.0006,
            ),
            ModelInfo(
                id="claude-3-5-sonnet-20241022",
                provider="anthropic",
                display_name="Claude 3.5 Sonnet",
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.VISION,
                    ModelCapability.TOOLS,
                    ModelCapability.STREAMING,
                ],
                context_window=200000,
                input_cost_per_1k=0.003,
                output_cost_per_1k=0.015,
            ),
            ModelInfo(
                id="claude-3-5-haiku-20241022",
                provider="anthropic",
                display_name="Claude 3.5 Haiku",
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.TOOLS,
                    ModelCapability.STREAMING,
                ],
                context_window=200000,
                input_cost_per_1k=0.001,
                output_cost_per_1k=0.005,
            ),
            ModelInfo(
                id="gemini-1.5-pro",
                provider="google",
                display_name="Gemini 1.5 Pro",
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.VISION,
                    ModelCapability.TOOLS,
                    ModelCapability.STREAMING,
                ],
                context_window=2000000,
                input_cost_per_1k=0.00125,
                output_cost_per_1k=0.005,
            ),
            ModelInfo(
                id="gemini-1.5-flash",
                provider="google",
                display_name="Gemini 1.5 Flash",
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.VISION,
                    ModelCapability.TOOLS,
                    ModelCapability.STREAMING,
                ],
                context_window=1000000,
                input_cost_per_1k=0.000075,
                output_cost_per_1k=0.0003,
            ),
        ]

    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        if not self._initialized:
            return False

        try:
            # Try a minimal completion
            response = await self.complete(
                CompletionRequest(
                    model=self.config.default_model,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=5,
                )
            )
            return response.finish_reason != "error"
        except Exception as e:
            logger.warning("Health check failed", error=str(e))
            return False

    def _convert_messages(self, messages: list) -> list[dict[str, Any]]:
        """Convert Forge messages to LiteLLM format."""
        result = []
        for msg in messages:
            if hasattr(msg, "model_dump"):
                msg_dict = msg.model_dump(exclude_none=True)
            else:
                msg_dict = dict(msg)

            # Handle content blocks
            if isinstance(msg_dict.get("content"), list):
                # Convert content blocks to LiteLLM format
                content_parts = []
                for block in msg_dict["content"]:
                    if block.get("type") == "text":
                        content_parts.append({"type": "text", "text": block.get("text", "")})
                    elif block.get("type") == "image":
                        content_parts.append(
                            {"type": "image_url", "image_url": {"url": block.get("image_url")}}
                        )
                msg_dict["content"] = content_parts

            result.append(msg_dict)
        return result

    def _convert_tools(self, tools: list) -> list[dict[str, Any]]:
        """Convert Forge tool definitions to LiteLLM format."""
        result = []
        for tool in tools:
            if hasattr(tool, "model_dump"):
                tool_dict = tool.model_dump(exclude_none=True)
            else:
                tool_dict = dict(tool)

            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool_dict["name"],
                        "description": tool_dict.get("description", ""),
                        "parameters": tool_dict.get("parameters", {}),
                    },
                }
            )
        return result

    def _convert_response_format(self, response_format) -> dict[str, Any]:
        """Convert response format to LiteLLM format."""
        if hasattr(response_format, "model_dump"):
            rf_dict = response_format.model_dump(exclude_none=True)
        else:
            rf_dict = dict(response_format)

        if rf_dict.get("type") == "json_schema":
            return {"type": "json_object", "schema": rf_dict.get("json_schema")}
        return {"type": rf_dict.get("type", "text")}

    def _parse_response(self, response, latency_ms: float) -> CompletionResponse:
        """Parse LiteLLM response to Forge format."""
        choice = response.choices[0]
        message = choice.message

        # Parse tool calls if present
        tool_calls = None
        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=tc.function.arguments
                    if isinstance(tc.function.arguments, dict)
                    else {},
                )
                for tc in message.tool_calls
            ]

        return CompletionResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            usage=TokenUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ),
            model=response.model,
            finish_reason=choice.finish_reason or "stop",
            latency_ms=latency_ms,
        )

    def _parse_stream_chunk(self, chunk) -> StreamChunk:
        """Parse a streaming chunk to Forge format."""
        choice = chunk.choices[0] if chunk.choices else None

        content = None
        tool_calls = None
        finish_reason = None
        usage = None

        if choice:
            delta = choice.delta
            content = getattr(delta, "content", None)
            finish_reason = getattr(choice, "finish_reason", None)

            if hasattr(delta, "tool_calls") and delta.tool_calls:
                tool_calls = [
                    ToolCall(
                        id=tc.id or "",
                        name=tc.function.name if tc.function else "",
                        arguments={},
                    )
                    for tc in delta.tool_calls
                ]

        if hasattr(chunk, "usage") and chunk.usage:
            usage = TokenUsage(
                input_tokens=chunk.usage.prompt_tokens,
                output_tokens=chunk.usage.completion_tokens,
                total_tokens=chunk.usage.total_tokens,
            )

        return StreamChunk(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
        )

    def _handle_error(self, error: Exception, model: str) -> None:
        """Handle and convert provider errors."""
        error_str = str(error).lower()

        if "rate limit" in error_str or "429" in error_str:
            raise RateLimitError(
                str(error),
                provider="litellm",
                model=model,
            )

        logger.error("LiteLLM error", error=str(error), model=model)
        raise ProviderError(str(error), provider="litellm", model=model)
