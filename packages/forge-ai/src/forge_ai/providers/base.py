"""
Base provider types and LLMProvider protocol.

This module defines the core abstractions for interacting with LLM providers.
All provider implementations must conform to the LLMProvider protocol.
"""

from abc import abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class ContentBlockType(str, Enum):
    """Types of content blocks in a message."""

    TEXT = "text"
    IMAGE = "image"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class ContentBlock(BaseModel):
    """A block of content within a message (text, image, tool use, etc.)."""

    type: ContentBlockType
    text: str | None = None
    image_url: str | None = None
    tool_use_id: str | None = None
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_result: str | None = None


class ToolCall(BaseModel):
    """A tool call made by the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


class ToolDefinition(BaseModel):
    """Definition of a tool that can be called by the LLM."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    required: list[str] = Field(default_factory=list)


class Message(BaseModel):
    """A message in a conversation."""

    role: str  # 'system', 'user', 'assistant', 'tool'
    content: str | list[ContentBlock]
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None  # For tool result messages
    name: str | None = None  # For tool result messages


class ResponseFormat(BaseModel):
    """Specification for structured output format."""

    type: str  # 'text', 'json_object', 'json_schema'
    json_schema: dict[str, Any] | None = None


class TokenUsage(BaseModel):
    """Token usage information from a completion."""

    input_tokens: int
    output_tokens: int
    total_tokens: int

    @property
    def cost_estimate(self) -> float:
        """Estimate cost in USD (rough approximation)."""
        # These are approximate costs, actual costs vary by model
        input_cost = self.input_tokens * 0.000003
        output_cost = self.output_tokens * 0.000015
        return input_cost + output_cost


class CompletionRequest(BaseModel):
    """Request for an LLM completion."""

    messages: list[Message]
    model: str
    temperature: float = 0.7
    max_tokens: int | None = None
    tools: list[ToolDefinition] | None = None
    response_format: ResponseFormat | None = None
    stream: bool = False
    top_p: float | None = None
    stop: list[str] | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None

    # Forge-specific context
    ontology_id: str | None = None
    user_id: str | None = None
    request_id: str | None = None


class CompletionResponse(BaseModel):
    """Response from an LLM completion."""

    content: str
    tool_calls: list[ToolCall] | None = None
    usage: TokenUsage
    model: str
    finish_reason: str  # 'stop', 'length', 'tool_calls', 'content_filter', 'error'
    latency_ms: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StreamChunk(BaseModel):
    """A chunk from a streaming completion."""

    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    finish_reason: str | None = None
    usage: TokenUsage | None = None  # Only present in final chunk


class ModelCapability(str, Enum):
    """Capabilities that a model may support."""

    CHAT = "chat"
    VISION = "vision"
    TOOLS = "tools"
    JSON_MODE = "json_mode"
    STREAMING = "streaming"


class ModelInfo(BaseModel):
    """Information about an available model."""

    id: str
    provider: str
    display_name: str | None = None
    capabilities: list[ModelCapability] = Field(default_factory=list)
    max_tokens: int | None = None
    context_window: int | None = None
    input_cost_per_1k: float | None = None  # USD per 1k tokens
    output_cost_per_1k: float | None = None  # USD per 1k tokens


@runtime_checkable
class LLMProvider(Protocol):
    """
    Protocol for LLM providers.

    All LLM provider implementations must implement this protocol to ensure
    consistent behavior across different providers (OpenAI, Anthropic, etc.).
    """

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """
        Execute a completion request.

        Args:
            request: The completion request with messages and parameters.

        Returns:
            CompletionResponse with the generated content.

        Raises:
            ProviderError: If the provider encounters an error.
            RateLimitError: If rate limited by the provider.
            AuthenticationError: If authentication fails.
        """
        ...

    @abstractmethod
    async def stream(self, request: CompletionRequest) -> AsyncIterator[StreamChunk]:
        """
        Execute a streaming completion request.

        Args:
            request: The completion request with messages and parameters.

        Yields:
            StreamChunk with partial content as it's generated.

        Raises:
            ProviderError: If the provider encounters an error.
        """
        ...

    @abstractmethod
    def supported_models(self) -> list[ModelInfo]:
        """
        Get the list of models supported by this provider.

        Returns:
            List of ModelInfo describing available models.
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


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, message: str, provider: str, model: str | None = None):
        self.provider = provider
        self.model = model
        super().__init__(f"[{provider}] {message}")


class RateLimitError(ProviderError):
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


class AuthenticationError(ProviderError):
    """Raised when authentication fails."""

    pass


class ModelNotAvailableError(ProviderError):
    """Raised when the requested model is not available."""

    pass


class ContentFilterError(ProviderError):
    """Raised when content is blocked by the provider's content filter."""

    pass
