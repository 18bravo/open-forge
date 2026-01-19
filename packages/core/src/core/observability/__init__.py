"""
Observability module for Open Forge.
Provides OpenTelemetry tracing, metrics, and LangSmith integration.
"""
from core.observability.tracing import setup_tracing, get_tracer, traced, add_span_attribute
from core.observability.langsmith import (
    LangSmithObservability,
    LangSmithConfig,
    TraceInfo,
    FeedbackRecord,
    ObservabilityStats,
    get_langsmith,
    setup_langsmith,
    trace_engagement,
    trace_agent,
)

__all__ = [
    # OpenTelemetry tracing
    "setup_tracing",
    "get_tracer",
    "traced",
    "add_span_attribute",
    # LangSmith integration
    "LangSmithObservability",
    "LangSmithConfig",
    "TraceInfo",
    "FeedbackRecord",
    "ObservabilityStats",
    "get_langsmith",
    "setup_langsmith",
    "trace_engagement",
    "trace_agent",
]
