"""
OpenTelemetry tracing setup.
"""
import asyncio
from functools import wraps
from typing import Callable, Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from core.config import get_settings

settings = get_settings()

_tracer_provider: TracerProvider | None = None


def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing."""
    global _tracer_provider

    if _tracer_provider is not None:
        return

    resource = Resource.create({
        "service.name": settings.observability.service_name,
        "deployment.environment": settings.environment
    })

    _tracer_provider = TracerProvider(resource=resource)

    # Add OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.observability.otlp_endpoint,
        insecure=True
    )
    _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    trace.set_tracer_provider(_tracer_provider)

    # Optional: Instrument common libraries
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        SQLAlchemyInstrumentor().instrument()
    except ImportError:
        pass

    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        RedisInstrumentor().instrument()
    except ImportError:
        pass

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().instrument()
    except ImportError:
        pass


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer for the given component."""
    return trace.get_tracer(name)


def traced(name: str | None = None):
    """Decorator to trace a function."""
    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__
        tracer = get_tracer(func.__module__)

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def add_span_attribute(key: str, value: Any) -> None:
    """Add an attribute to the current span."""
    span = trace.get_current_span()
    if span:
        span.set_attribute(key, value)


def add_span_event(name: str, attributes: dict | None = None) -> None:
    """Add an event to the current span."""
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})
