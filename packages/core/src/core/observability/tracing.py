"""
OpenTelemetry tracing setup.
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from functools import wraps
from typing import Callable, Any
from core.config import get_settings

settings = get_settings()

def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing."""
    resource = Resource.create({
        "service.name": settings.observability.service_name,
        "deployment.environment": settings.environment
    })
    
    provider = TracerProvider(resource=resource)
    
    # Add OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.observability.otlp_endpoint,
        insecure=True
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    trace.set_tracer_provider(provider)
    
    # Instrument libraries
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer for the given component."""
    return trace.get_tracer(name)

def traced(name: str = None):
    """Decorator to trace a function."""
    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__
        tracer = get_tracer(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

import asyncio