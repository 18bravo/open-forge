"""
Providers module - LLM provider abstraction and routing.

This module provides:
- LLMProvider: Protocol for LLM providers
- LiteLLMProvider: LiteLLM wrapper implementation
- ModelRouter: Intelligent model selection and fallback
"""

from forge_ai.providers.base import (
    LLMProvider,
    Message,
    ContentBlock,
    ToolCall,
    ToolDefinition,
    CompletionRequest,
    CompletionResponse,
    StreamChunk,
    TokenUsage,
    ModelInfo,
    ResponseFormat,
)
from forge_ai.providers.litellm_wrapper import LiteLLMProvider
from forge_ai.providers.routing import ModelRouter, RoutingConfig, FallbackChain

__all__ = [
    "LLMProvider",
    "LiteLLMProvider",
    "Message",
    "ContentBlock",
    "ToolCall",
    "ToolDefinition",
    "CompletionRequest",
    "CompletionResponse",
    "StreamChunk",
    "TokenUsage",
    "ModelInfo",
    "ResponseFormat",
    "ModelRouter",
    "RoutingConfig",
    "FallbackChain",
]
