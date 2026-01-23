"""
Data source management endpoints.
"""
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import DbSession, CurrentUser, EventBusDep
from api.schemas.common import PaginatedResponse, SuccessResponse
from core.observability.tracing import traced, add_span_attribute

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])


class DataSourceType(str, Enum):
    """Supported data source types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    S3 = "s3"
    GCS = "gcs"
    AZURE_BLOB = "azure_blob"
    ICEBERG = "iceberg"
    DELTA = "delta"
    PARQUET = "parquet"
    CSV = "csv"
    API = "api"
    KAFKA = "kafka"


class DataSourceStatus(str, Enum):
    """Data source connection status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


class DataSourceCreate(BaseModel):
    """Schema for creating a data source."""
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    source_type: DataSourceType
    connection_config: Dict[str, Any] = Field(description="Type-specific connection config")
    schema_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Schema/table configuration"
    )
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class DataSourceUpdate(BaseModel):
    """Schema for updating a data source."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    connection_config: Optional[Dict[str, Any]] = None
    schema_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DataSourceResponse(BaseModel):
    """Schema for data source response."""
    id: str
    name: str
    description: Optional[str] = None
    source_type: DataSourceType
    status: DataSourceStatus
    connection_config: Dict[str, Any]  # Sensitive fields redacted
    schema_config: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_tested_at: Optional[datetime] = None
    last_error: Optional[str] = None

    model_config = {"from_attributes": True}


class DataSourceSummary(BaseModel):
    """Lightweight data source summary."""
    id: str
    name: str
    source_type: DataSourceType
    status: DataSourceStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ConnectionTestResult(BaseModel):
    """Result of a connection test."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None


class DataSourceSchema(BaseModel):
    """Schema information for a data source."""
    source_id: str
    tables: List[Dict[str, Any]]
    last_refreshed: datetime


@router.post(
    "",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create data source",
    description="Creates a new data source connection"
)
@traced("data_sources.create")
async def create_data_source(
    source: DataSourceCreate,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> DataSourceResponse:
    """
    Create a new data source.

    Connection credentials are stored securely and never returned in API responses.
    """
    source_id = str(uuid4())
    now = datetime.utcnow()

    add_span_attribute("data_source.id", source_id)
    add_span_attribute("data_source.type", source.source_type.value)

    # Redact sensitive fields from connection config
    redacted_config = _redact_connection_config(source.connection_config)

    # TODO: Store in database with encrypted credentials
    response = DataSourceResponse(
        id=source_id,
        name=source.name,
        description=source.description,
        source_type=source.source_type,
        status=DataSourceStatus.INACTIVE,
        connection_config=redacted_config,
        schema_config=source.schema_config,
        tags=source.tags,
        metadata=source.metadata,
        created_by=user.id,
        created_at=now,
        updated_at=now,
    )

    await event_bus.publish(
        "data_source.created",
        {
            "source_id": source_id,
            "name": source.name,
            "type": source.source_type.value,
            "created_by": user.id,
        }
    )

    return response


@router.get(
    "",
    response_model=PaginatedResponse[DataSourceSummary],
    summary="List data sources",
    description="Returns a paginated list of data sources"
)
@traced("data_sources.list")
async def list_data_sources(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    source_type: Optional[DataSourceType] = Query(default=None, alias="type"),
    status_filter: Optional[DataSourceStatus] = Query(default=None, alias="status"),
    search: Optional[str] = Query(default=None),
) -> PaginatedResponse[DataSourceSummary]:
    """
    List data sources with pagination and filtering.
    """
    add_span_attribute("pagination.page", page)

    # TODO: Implement database query
    return PaginatedResponse.create(
        items=[],
        total=0,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{source_id}",
    response_model=DataSourceResponse,
    summary="Get data source",
    description="Returns detailed information about a data source"
)
@traced("data_sources.get")
async def get_data_source(
    source_id: str,
    db: DbSession,
    user: CurrentUser,
) -> DataSourceResponse:
    """
    Get detailed information about a specific data source.

    Sensitive connection details are redacted.
    """
    add_span_attribute("data_source.id", source_id)

    # TODO: Fetch from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Data source {source_id} not found"
    )


@router.put(
    "/{source_id}",
    response_model=DataSourceResponse,
    summary="Update data source",
    description="Updates a data source configuration"
)
@traced("data_sources.update")
async def update_data_source(
    source_id: str,
    source: DataSourceUpdate,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> DataSourceResponse:
    """
    Update an existing data source.
    """
    add_span_attribute("data_source.id", source_id)

    # TODO: Implement update
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Data source {source_id} not found"
    )


@router.delete(
    "/{source_id}",
    response_model=SuccessResponse,
    summary="Delete data source",
    description="Deletes a data source"
)
@traced("data_sources.delete")
async def delete_data_source(
    source_id: str,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> SuccessResponse:
    """
    Delete a data source.

    The data source cannot be deleted if it is being used by active engagements.
    """
    add_span_attribute("data_source.id", source_id)

    # TODO: Check for active usages and delete
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Data source {source_id} not found"
    )


@router.post(
    "/{source_id}/test",
    response_model=ConnectionTestResult,
    summary="Test connection",
    description="Tests the connection to a data source"
)
@traced("data_sources.test")
async def test_connection(
    source_id: str,
    db: DbSession,
    user: CurrentUser,
) -> ConnectionTestResult:
    """
    Test the connection to a data source.

    Attempts to connect and perform a simple query to verify connectivity.
    """
    add_span_attribute("data_source.id", source_id)

    # TODO: Implement connection testing
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Data source {source_id} not found"
    )


@router.get(
    "/{source_id}/schema",
    response_model=DataSourceSchema,
    summary="Get schema",
    description="Returns the schema information for a data source"
)
@traced("data_sources.schema")
async def get_data_source_schema(
    source_id: str,
    db: DbSession,
    user: CurrentUser,
    refresh: bool = Query(default=False, description="Force refresh schema"),
) -> DataSourceSchema:
    """
    Get the schema information for a data source.

    Returns table/collection information including columns, types, and statistics.
    """
    add_span_attribute("data_source.id", source_id)
    add_span_attribute("schema.refresh", refresh)

    # TODO: Implement schema retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Data source {source_id} not found"
    )


@router.post(
    "/{source_id}/schema/refresh",
    response_model=DataSourceSchema,
    summary="Refresh schema",
    description="Refreshes the schema information for a data source"
)
@traced("data_sources.schema.refresh")
async def refresh_data_source_schema(
    source_id: str,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> DataSourceSchema:
    """
    Refresh the schema information for a data source.

    Connects to the source and re-fetches all schema metadata.
    """
    add_span_attribute("data_source.id", source_id)

    # TODO: Implement schema refresh
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Data source {source_id} not found"
    )


def _redact_connection_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive fields from connection configuration."""
    sensitive_fields = {
        "password", "secret", "api_key", "access_key", "secret_key",
        "token", "credentials", "private_key", "connection_string"
    }

    redacted = {}
    for key, value in config.items():
        if key.lower() in sensitive_fields:
            redacted[key] = "***REDACTED***"
        elif isinstance(value, dict):
            redacted[key] = _redact_connection_config(value)
        else:
            redacted[key] = value

    return redacted
