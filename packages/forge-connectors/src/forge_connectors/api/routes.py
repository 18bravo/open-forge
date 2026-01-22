"""
FastAPI routes for connector management API.

Endpoints:
- GET  /types                      - List available connector types
- GET  /types/{type}               - Get connector type details
- POST /connections                - Create new connection
- GET  /connections                - List connections
- GET  /connections/{id}           - Get connection details
- POST /connections/{id}/test      - Test connection
- GET  /connections/{id}/schema    - Discover schema
- POST /sync/jobs                  - Create sync job
- POST /sync/jobs/{id}/run         - Trigger sync
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

# Note: FastAPI is optional. Import conditionally.
try:
    from fastapi import APIRouter, HTTPException, Query
except ImportError:
    # Create stub if FastAPI not installed
    class APIRouter:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def get(self, *args: Any, **kwargs: Any) -> Any:
            def decorator(func: Any) -> Any:
                return func

            return decorator

        def post(self, *args: Any, **kwargs: Any) -> Any:
            def decorator(func: Any) -> Any:
                return func

            return decorator

    class HTTPException(Exception):  # type: ignore
        def __init__(self, status_code: int, detail: str) -> None:
            self.status_code = status_code
            self.detail = detail

    def Query(*args: Any, **kwargs: Any) -> Any:  # type: ignore
        return None


from forge_connectors.core.registry import ConnectorRegistry, ConnectorNotFoundError


# Request/Response models


class ConnectorTypeInfo(BaseModel):
    """Information about a connector type."""

    connector_type: str
    category: str
    capabilities: list[str]
    description: str


class ConnectionCreate(BaseModel):
    """Request to create a new connection."""

    name: str
    connector_type: str
    config: dict[str, Any]
    secrets_ref: Optional[str] = None


class ConnectionResponse(BaseModel):
    """Response for a connection."""

    id: str
    name: str
    connector_type: str
    category: str
    capabilities: list[str]
    status: str
    created_at: str


class ConnectionTestResponse(BaseModel):
    """Response for connection test."""

    success: bool
    error: Optional[str] = None
    latency_ms: Optional[float] = None
    server_version: Optional[str] = None


class SchemaObjectResponse(BaseModel):
    """Response for a discovered schema object."""

    name: str
    schema_name: Optional[str] = None
    object_type: str
    column_count: int
    supports_cdc: bool
    supports_incremental: bool


class SyncJobCreate(BaseModel):
    """Request to create a sync job."""

    connection_id: str
    name: str
    objects: list[dict[str, Any]]
    schedule: Optional[str] = None


class SyncJobResponse(BaseModel):
    """Response for a sync job."""

    id: str
    name: str
    connection_id: str
    status: str
    created_at: str


# Router

router = APIRouter(prefix="/api/v1/connectors", tags=["connectors"])


@router.get("/types", response_model=list[ConnectorTypeInfo])
async def list_connector_types() -> list[ConnectorTypeInfo]:
    """List all available connector types."""
    connectors = ConnectorRegistry.list_all()
    return [
        ConnectorTypeInfo(
            connector_type=c.connector_type,
            category=c.category,
            capabilities=[cap.value for cap in c.capabilities],
            description=c.description,
        )
        for c in connectors
    ]


@router.get("/types/{connector_type}", response_model=ConnectorTypeInfo)
async def get_connector_type(connector_type: str) -> ConnectorTypeInfo:
    """Get details for a specific connector type."""
    try:
        cls = ConnectorRegistry.get(connector_type)
        return ConnectorTypeInfo(
            connector_type=cls.connector_type,
            category=cls.category,
            capabilities=[cap.value for cap in cls.get_capabilities()],
            description=cls.__doc__.split("\n")[0] if cls.__doc__ else "",
        )
    except ConnectorNotFoundError:
        raise HTTPException(status_code=404, detail=f"Connector type not found: {connector_type}")


@router.post("/connections", response_model=ConnectionResponse)
async def create_connection(request: ConnectionCreate) -> ConnectionResponse:
    """
    Create a new connection.

    Note: This is a stub. Full implementation requires:
    - Connection storage (database)
    - Secrets integration
    - Background health monitoring
    """
    # Validate connector type exists
    try:
        cls = ConnectorRegistry.get(request.connector_type)
    except ConnectorNotFoundError:
        raise HTTPException(
            status_code=400, detail=f"Unknown connector type: {request.connector_type}"
        )

    # Stub response
    return ConnectionResponse(
        id="conn_stub_123",
        name=request.name,
        connector_type=request.connector_type,
        category=cls.category,
        capabilities=[cap.value for cap in cls.get_capabilities()],
        status="pending_test",
        created_at="2026-01-22T00:00:00Z",
    )


@router.get("/connections", response_model=list[ConnectionResponse])
async def list_connections(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ConnectionResponse]:
    """
    List all connections.

    Note: Stub implementation.
    """
    return []


@router.get("/connections/{connection_id}", response_model=ConnectionResponse)
async def get_connection(connection_id: str) -> ConnectionResponse:
    """
    Get connection details.

    Note: Stub implementation.
    """
    raise HTTPException(status_code=404, detail=f"Connection not found: {connection_id}")


@router.post("/connections/{connection_id}/test", response_model=ConnectionTestResponse)
async def test_connection(connection_id: str) -> ConnectionTestResponse:
    """
    Test a connection.

    Note: Stub implementation.
    """
    raise HTTPException(status_code=404, detail=f"Connection not found: {connection_id}")


@router.get(
    "/connections/{connection_id}/schema", response_model=list[SchemaObjectResponse]
)
async def discover_schema(connection_id: str) -> list[SchemaObjectResponse]:
    """
    Discover schema for a connection.

    Note: Stub implementation.
    """
    raise HTTPException(status_code=404, detail=f"Connection not found: {connection_id}")


@router.post("/sync/jobs", response_model=SyncJobResponse)
async def create_sync_job(request: SyncJobCreate) -> SyncJobResponse:
    """
    Create a new sync job.

    Note: Stub implementation.
    """
    return SyncJobResponse(
        id="job_stub_123",
        name=request.name,
        connection_id=request.connection_id,
        status="created",
        created_at="2026-01-22T00:00:00Z",
    )


@router.post("/sync/jobs/{job_id}/run")
async def run_sync_job(job_id: str) -> dict[str, str]:
    """
    Trigger a sync job run.

    Note: Stub implementation.
    """
    return {"status": "started", "run_id": "run_stub_123"}
