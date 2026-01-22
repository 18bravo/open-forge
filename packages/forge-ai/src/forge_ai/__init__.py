"""
Forge AI - Unified AI Package for Open Forge

This package provides:
- providers/: LiteLLM wrapper, provider routing, fallback chains
- logic/: No-code LLM function definitions, visual builder support, execution engine
- context/: Ontology context injection, RAG retrieval integration
- security/: PII detection/masking, guardrails, multi-layer prompt injection detection, audit logging
"""

from forge_ai.providers.base import (
    LLMProvider,
    Message,
    CompletionRequest,
    CompletionResponse,
    TokenUsage,
    ModelInfo,
)
from forge_ai.providers.litellm_wrapper import LiteLLMProvider
from forge_ai.providers.routing import ModelRouter, RoutingConfig, FallbackChain
from forge_ai.security.injection import (
    InjectionDetector,
    InjectionResult,
    DetectionLayer,
    ThreatLevel,
)
from forge_ai.security.guardrails import (
    GuardrailConfig,
    GuardrailsEngine,
    OutputValidationRule,
)
from forge_ai.security.pii_filter import PIIFilter, PIIConfig, PIIMaskingStrategy
from forge_ai.security.audit import AuditLogger, AuditEntry

__version__ = "0.1.0"

__all__ = [
    # Providers
    "LLMProvider",
    "LiteLLMProvider",
    "Message",
    "CompletionRequest",
    "CompletionResponse",
    "TokenUsage",
    "ModelInfo",
    # Routing
    "ModelRouter",
    "RoutingConfig",
    "FallbackChain",
    # Security - Injection Detection
    "InjectionDetector",
    "InjectionResult",
    "DetectionLayer",
    "ThreatLevel",
    # Security - Guardrails
    "GuardrailConfig",
    "GuardrailsEngine",
    "OutputValidationRule",
    # Security - PII
    "PIIFilter",
    "PIIConfig",
    "PIIMaskingStrategy",
    # Security - Audit
    "AuditLogger",
    "AuditEntry",
]
