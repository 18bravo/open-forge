"""
Health check endpoints.
"""
from fastapi import APIRouter, status
from datetime import datetime

from api.schemas.common import HealthStatus
from api import __version__
from core.observability.tracing import traced

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Returns basic health status of the API"
)
@traced("health.check")
async def health_check() -> HealthStatus:
    """
    Basic health check endpoint.

    Returns the current health status and API version.
    """
    return HealthStatus(
        status="healthy",
        version=__version__,
        timestamp=datetime.utcnow(),
        components={}
    )


@router.get(
    "/ready",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Checks if the API and all dependencies are ready"
)
@traced("health.ready")
async def readiness_check() -> HealthStatus:
    """
    Readiness check endpoint.

    Verifies that all dependencies (database, redis, etc.) are available.
    """
    components: dict[str, str] = {}

    # Check database connectivity
    try:
        from core.database.connection import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        components["database"] = "healthy"
    except Exception as e:
        components["database"] = f"unhealthy: {str(e)}"

    # Check Redis connectivity
    try:
        from api.dependencies import get_event_bus
        event_bus = get_event_bus()
        if event_bus.redis:
            await event_bus.redis.ping()
            components["redis"] = "healthy"
        else:
            components["redis"] = "not connected"
    except Exception as e:
        components["redis"] = f"unhealthy: {str(e)}"

    # Determine overall status
    all_healthy = all(
        status == "healthy" for status in components.values()
    )

    return HealthStatus(
        status="healthy" if all_healthy else "degraded",
        version=__version__,
        timestamp=datetime.utcnow(),
        components=components
    )


@router.get(
    "/live",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Simple liveness probe for Kubernetes"
)
async def liveness_check() -> HealthStatus:
    """
    Liveness check endpoint.

    Simple check that the API process is alive and responding.
    Used by Kubernetes liveness probes.
    """
    return HealthStatus(
        status="alive",
        version=__version__,
        timestamp=datetime.utcnow(),
        components={}
    )
