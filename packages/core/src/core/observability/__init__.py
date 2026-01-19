"""
Observability module for Open Forge.
Provides OpenTelemetry tracing and metrics.
"""
from core.observability.tracing import setup_tracing, get_tracer, traced

__all__ = ["setup_tracing", "get_tracer", "traced"]
