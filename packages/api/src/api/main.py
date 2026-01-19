"""
FastAPI application for Open Forge API.

This module initializes the FastAPI application with all routers,
middleware, and lifecycle events.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from api import __version__
from api.routers import (
    health_router,
    engagements_router,
    agents_router,
    data_sources_router,
    approvals_router,
    reviews_router,
    admin_router,
    codegen_router,
)
from api.graphql import graphql_app
from api.dependencies import init_event_bus, close_event_bus
from api.schemas.common import ErrorResponse, ErrorDetail

from core.config import get_settings
from core.database.connection import init_db, close_db
from core.observability.tracing import setup_tracing, get_tracer

settings = get_settings()
tracer = get_tracer("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.
    """
    # Startup
    with tracer.start_as_current_span("app.startup"):
        # Initialize tracing
        setup_tracing()

        # Initialize database
        await init_db()

        # Initialize event bus
        await init_event_bus()

    yield

    # Shutdown
    with tracer.start_as_current_span("app.shutdown"):
        # Close event bus
        await close_event_bus()

        # Close database connections
        await close_db()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Open Forge API",
        description="REST and GraphQL API for Open Forge - Open Source Data Platform",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add OpenTelemetry instrumentation
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        pass

    # Register exception handlers
    _register_exception_handlers(app)

    # Register REST routers
    app.include_router(health_router)
    app.include_router(engagements_router, prefix="/api/v1")
    app.include_router(agents_router, prefix="/api/v1")
    app.include_router(data_sources_router, prefix="/api/v1")
    app.include_router(approvals_router, prefix="/api/v1")
    app.include_router(reviews_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(codegen_router, prefix="/api/v1")

    # Register GraphQL router
    app.include_router(graphql_app, prefix="/graphql")

    return app


def _get_cors_origins() -> list[str]:
    """Get allowed CORS origins based on environment."""
    if settings.environment == "development":
        return ["*"]

    # In production, return specific allowed origins
    return [
        "https://forge.example.com",
        "https://app.forge.example.com",
    ]


def _register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle validation errors with detailed error response."""
        details = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            details.append(
                ErrorDetail(
                    field=field,
                    message=error["msg"],
                    code=error["type"]
                )
            )

        error_response = ErrorResponse(
            error="validation_error",
            message="Request validation failed",
            details=details,
            request_id=request.headers.get("x-request-id"),
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        # Log the exception
        import traceback
        traceback.print_exc()

        error_response = ErrorResponse(
            error="internal_error",
            message="An unexpected error occurred" if not settings.debug else str(exc),
            request_id=request.headers.get("x-request-id"),
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(mode="json"),
        )


# Create the application instance
app = create_app()


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Open Forge API",
        "version": __version__,
        "docs": "/docs",
        "graphql": "/graphql",
    }
