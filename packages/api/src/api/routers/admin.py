"""
Admin API endpoints for Open Forge dashboard.
"""
from typing import Optional, List
from uuid import uuid4
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import DbSession, CurrentUser
from api.schemas.common import PaginatedResponse, SuccessResponse
from core.observability.tracing import traced, add_span_attribute

router = APIRouter(prefix="/admin", tags=["Admin"])


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class ServiceStatus(str, Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class PipelineStatus(str, Enum):
    """Pipeline run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AuditAction(str, Enum):
    """Audit log action types."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXECUTE = "execute"
    APPROVE = "approve"
    REJECT = "reject"


class ConnectorType(str, Enum):
    """Connector types."""
    DATABASE = "database"
    API = "api"
    FILE_STORAGE = "file_storage"
    MESSAGE_QUEUE = "message_queue"
    CLOUD_SERVICE = "cloud_service"


# -----------------------------------------------------------------------------
# Pydantic Models - System Health
# -----------------------------------------------------------------------------

class ServiceHealth(BaseModel):
    """Health status for an individual service."""
    service: str = Field(description="Service name")
    status: ServiceStatus = Field(description="Service status")
    latency: Optional[float] = Field(default=None, description="Latency in milliseconds")
    uptime: Optional[float] = Field(default=None, description="Uptime percentage")
    last_check: Optional[datetime] = Field(default=None, description="Last health check time")
    error: Optional[str] = Field(default=None, description="Error message if unhealthy")


class SystemHealthResponse(BaseModel):
    """System health check response."""
    services: List[ServiceHealth] = Field(description="Individual service health statuses")
    overall_status: ServiceStatus = Field(description="Overall system status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# -----------------------------------------------------------------------------
# Pydantic Models - Agent Clusters
# -----------------------------------------------------------------------------

class AgentClusterSummary(BaseModel):
    """Summary of an agent cluster."""
    slug: str = Field(description="Unique slug identifier")
    name: str = Field(description="Display name")
    description: Optional[str] = Field(default=None, description="Cluster description")
    agent_count: int = Field(description="Number of agents in cluster")
    active_tasks: int = Field(description="Number of active tasks")
    status: ServiceStatus = Field(description="Cluster health status")
    created_at: datetime = Field(description="Creation timestamp")


class AgentClusterDetail(BaseModel):
    """Detailed agent cluster information."""
    slug: str = Field(description="Unique slug identifier")
    name: str = Field(description="Display name")
    description: Optional[str] = Field(default=None, description="Cluster description")
    agent_count: int = Field(description="Number of agents in cluster")
    active_tasks: int = Field(description="Number of active tasks")
    completed_tasks: int = Field(description="Number of completed tasks")
    failed_tasks: int = Field(description="Number of failed tasks")
    status: ServiceStatus = Field(description="Cluster health status")
    agents: List[str] = Field(default_factory=list, description="List of agent IDs")
    config: dict = Field(default_factory=dict, description="Cluster configuration")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class AgentTypeSummary(BaseModel):
    """Summary of an agent type."""
    type_id: str = Field(description="Unique type identifier")
    name: str = Field(description="Display name")
    description: Optional[str] = Field(default=None, description="Type description")
    instance_count: int = Field(description="Number of active instances")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")


# -----------------------------------------------------------------------------
# Pydantic Models - Pipelines
# -----------------------------------------------------------------------------

class PipelineSummary(BaseModel):
    """Summary of a pipeline."""
    id: str = Field(description="Pipeline ID")
    name: str = Field(description="Pipeline name")
    description: Optional[str] = Field(default=None, description="Pipeline description")
    schedule: Optional[str] = Field(default=None, description="Cron schedule expression")
    last_run_status: Optional[PipelineStatus] = Field(default=None, description="Last run status")
    last_run_at: Optional[datetime] = Field(default=None, description="Last run timestamp")
    next_run_at: Optional[datetime] = Field(default=None, description="Next scheduled run")
    is_active: bool = Field(description="Whether pipeline is active")


class PipelineDetail(BaseModel):
    """Detailed pipeline information."""
    id: str = Field(description="Pipeline ID")
    name: str = Field(description="Pipeline name")
    description: Optional[str] = Field(default=None, description="Pipeline description")
    schedule: Optional[str] = Field(default=None, description="Cron schedule expression")
    last_run_status: Optional[PipelineStatus] = Field(default=None, description="Last run status")
    last_run_at: Optional[datetime] = Field(default=None, description="Last run timestamp")
    next_run_at: Optional[datetime] = Field(default=None, description="Next scheduled run")
    is_active: bool = Field(description="Whether pipeline is active")
    steps: List[dict] = Field(default_factory=list, description="Pipeline steps")
    config: dict = Field(default_factory=dict, description="Pipeline configuration")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class PipelineRunSummary(BaseModel):
    """Summary of a pipeline run."""
    run_id: str = Field(description="Run ID")
    pipeline_id: str = Field(description="Pipeline ID")
    pipeline_name: str = Field(description="Pipeline name")
    status: PipelineStatus = Field(description="Run status")
    started_at: datetime = Field(description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    duration_seconds: Optional[float] = Field(default=None, description="Run duration in seconds")
    triggered_by: Optional[str] = Field(default=None, description="User or trigger source")


# -----------------------------------------------------------------------------
# Pydantic Models - Settings
# -----------------------------------------------------------------------------

class SystemSettings(BaseModel):
    """System settings configuration."""
    site_name: str = Field(default="Open Forge", description="Site display name")
    default_timezone: str = Field(default="UTC", description="Default timezone")
    max_concurrent_tasks: int = Field(default=10, description="Max concurrent agent tasks")
    task_timeout_seconds: int = Field(default=3600, description="Default task timeout")
    enable_telemetry: bool = Field(default=True, description="Enable telemetry")
    enable_audit_log: bool = Field(default=True, description="Enable audit logging")
    retention_days: int = Field(default=90, description="Data retention period in days")
    features: dict = Field(default_factory=dict, description="Feature flags")


class SettingsUpdate(BaseModel):
    """Settings update request."""
    site_name: Optional[str] = Field(default=None, description="Site display name")
    default_timezone: Optional[str] = Field(default=None, description="Default timezone")
    max_concurrent_tasks: Optional[int] = Field(default=None, ge=1, le=100, description="Max concurrent tasks")
    task_timeout_seconds: Optional[int] = Field(default=None, ge=60, le=86400, description="Task timeout")
    enable_telemetry: Optional[bool] = Field(default=None, description="Enable telemetry")
    enable_audit_log: Optional[bool] = Field(default=None, description="Enable audit logging")
    retention_days: Optional[int] = Field(default=None, ge=7, le=365, description="Data retention days")
    features: Optional[dict] = Field(default=None, description="Feature flags to update")


# -----------------------------------------------------------------------------
# Pydantic Models - Connectors
# -----------------------------------------------------------------------------

class ConnectorSummary(BaseModel):
    """Summary of a configured connector."""
    id: str = Field(description="Connector ID")
    name: str = Field(description="Connector name")
    type: ConnectorType = Field(description="Connector type")
    status: ServiceStatus = Field(description="Connection status")
    last_sync_at: Optional[datetime] = Field(default=None, description="Last sync timestamp")
    created_at: datetime = Field(description="Creation timestamp")


# -----------------------------------------------------------------------------
# Pydantic Models - Users
# -----------------------------------------------------------------------------

class UserSummary(BaseModel):
    """Summary of a system user."""
    id: str = Field(description="User ID")
    username: str = Field(description="Username")
    email: Optional[str] = Field(default=None, description="User email")
    roles: List[str] = Field(default_factory=list, description="User roles")
    is_active: bool = Field(description="Whether user is active")
    last_login_at: Optional[datetime] = Field(default=None, description="Last login timestamp")
    created_at: datetime = Field(description="Account creation timestamp")


# -----------------------------------------------------------------------------
# Pydantic Models - Audit Log
# -----------------------------------------------------------------------------

class AuditLogEntry(BaseModel):
    """Audit log entry."""
    id: str = Field(description="Log entry ID")
    action: AuditAction = Field(description="Action performed")
    resource_type: str = Field(description="Type of resource affected")
    resource_id: str = Field(description="ID of affected resource")
    user_id: str = Field(description="User who performed the action")
    username: str = Field(description="Username")
    details: Optional[dict] = Field(default=None, description="Additional details")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    timestamp: datetime = Field(description="Action timestamp")


# -----------------------------------------------------------------------------
# Pydantic Models - Dashboard
# -----------------------------------------------------------------------------

class DashboardStats(BaseModel):
    """Aggregated dashboard statistics."""
    total_engagements: int = Field(description="Total number of engagements")
    active_engagements: int = Field(description="Currently active engagements")
    total_tasks: int = Field(description="Total agent tasks")
    running_tasks: int = Field(description="Currently running tasks")
    completed_tasks_today: int = Field(description="Tasks completed today")
    failed_tasks_today: int = Field(description="Tasks failed today")
    total_agents: int = Field(description="Total registered agents")
    active_agents: int = Field(description="Currently active agents")
    system_health: ServiceStatus = Field(description="Overall system health")
    pipeline_runs_today: int = Field(description="Pipeline runs today")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# -----------------------------------------------------------------------------
# Endpoints - System Health
# -----------------------------------------------------------------------------

@router.get(
    "/health",
    response_model=SystemHealthResponse,
    summary="Get system health",
    description="Returns health status of all services"
)
@traced("admin.health")
async def get_system_health(
    user: CurrentUser,
) -> SystemHealthResponse:
    """
    Get health status of all services.

    Returns detailed health information for database, cache, storage,
    and other system components.
    """
    add_span_attribute("user.id", user.user_id)

    # Return mock data for now - will integrate with actual health checks
    now = datetime.utcnow()
    services = [
        ServiceHealth(
            service="database",
            status=ServiceStatus.HEALTHY,
            latency=5.2,
            uptime=99.9,
            last_check=now
        ),
        ServiceHealth(
            service="redis",
            status=ServiceStatus.HEALTHY,
            latency=1.8,
            uptime=99.95,
            last_check=now
        ),
        ServiceHealth(
            service="minio",
            status=ServiceStatus.HEALTHY,
            latency=12.5,
            uptime=99.8,
            last_check=now
        ),
        ServiceHealth(
            service="dagster",
            status=ServiceStatus.HEALTHY,
            latency=45.0,
            uptime=99.5,
            last_check=now
        ),
    ]

    return SystemHealthResponse(
        services=services,
        overall_status=ServiceStatus.HEALTHY,
        timestamp=now
    )


# -----------------------------------------------------------------------------
# Endpoints - Agent Clusters
# -----------------------------------------------------------------------------

@router.get(
    "/agents/clusters",
    response_model=PaginatedResponse[AgentClusterSummary],
    summary="List agent clusters",
    description="Returns a paginated list of agent clusters"
)
@traced("admin.agents.clusters.list")
async def list_agent_clusters(
    user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[AgentClusterSummary]:
    """
    List all agent clusters with pagination.
    """
    add_span_attribute("user.id", user.user_id)
    add_span_attribute("pagination.page", page)

    # Mock data - will integrate with agent registry
    now = datetime.utcnow()
    clusters = [
        AgentClusterSummary(
            slug="research-cluster",
            name="Research Cluster",
            description="Agents for research and analysis tasks",
            agent_count=5,
            active_tasks=3,
            status=ServiceStatus.HEALTHY,
            created_at=now
        ),
        AgentClusterSummary(
            slug="processing-cluster",
            name="Processing Cluster",
            description="Agents for data processing tasks",
            agent_count=8,
            active_tasks=12,
            status=ServiceStatus.HEALTHY,
            created_at=now
        ),
    ]

    return PaginatedResponse.create(
        items=clusters,
        total=len(clusters),
        page=page,
        page_size=page_size
    )


@router.get(
    "/agents/clusters/{slug}",
    response_model=AgentClusterDetail,
    summary="Get agent cluster",
    description="Returns detailed information about a specific agent cluster"
)
@traced("admin.agents.clusters.get")
async def get_agent_cluster(
    slug: str,
    user: CurrentUser,
) -> AgentClusterDetail:
    """
    Get detailed information about a specific agent cluster.
    """
    add_span_attribute("user.id", user.user_id)
    add_span_attribute("cluster.slug", slug)

    # Mock data - will integrate with agent registry
    now = datetime.utcnow()

    if slug == "research-cluster":
        return AgentClusterDetail(
            slug="research-cluster",
            name="Research Cluster",
            description="Agents for research and analysis tasks",
            agent_count=5,
            active_tasks=3,
            completed_tasks=150,
            failed_tasks=5,
            status=ServiceStatus.HEALTHY,
            agents=["agent-001", "agent-002", "agent-003", "agent-004", "agent-005"],
            config={"max_concurrent": 10, "timeout": 3600},
            created_at=now,
            updated_at=now
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Agent cluster '{slug}' not found"
    )


@router.get(
    "/agents/types",
    response_model=List[AgentTypeSummary],
    summary="List agent types",
    description="Returns a list of all available agent types"
)
@traced("admin.agents.types.list")
async def list_agent_types(
    user: CurrentUser,
) -> List[AgentTypeSummary]:
    """
    List all available agent types.
    """
    add_span_attribute("user.id", user.user_id)

    # Mock data - will integrate with agent registry
    return [
        AgentTypeSummary(
            type_id="research-agent",
            name="Research Agent",
            description="Agent specialized for research and information gathering",
            instance_count=5,
            capabilities=["web_search", "document_analysis", "summarization"]
        ),
        AgentTypeSummary(
            type_id="processing-agent",
            name="Processing Agent",
            description="Agent specialized for data processing and transformation",
            instance_count=8,
            capabilities=["data_extraction", "transformation", "validation"]
        ),
        AgentTypeSummary(
            type_id="coding-agent",
            name="Coding Agent",
            description="Agent specialized for code generation and analysis",
            instance_count=3,
            capabilities=["code_generation", "code_review", "testing"]
        ),
    ]


# -----------------------------------------------------------------------------
# Endpoints - Pipelines
# -----------------------------------------------------------------------------

@router.get(
    "/pipelines",
    response_model=PaginatedResponse[PipelineSummary],
    summary="List pipelines",
    description="Returns a paginated list of pipelines"
)
@traced("admin.pipelines.list")
async def list_pipelines(
    user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
) -> PaginatedResponse[PipelineSummary]:
    """
    List all pipelines with pagination.
    """
    add_span_attribute("user.id", user.user_id)
    add_span_attribute("pagination.page", page)

    # Mock data - will integrate with Dagster
    now = datetime.utcnow()
    pipelines = [
        PipelineSummary(
            id="pipeline-001",
            name="Daily Data Sync",
            description="Syncs data from external sources daily",
            schedule="0 2 * * *",
            last_run_status=PipelineStatus.COMPLETED,
            last_run_at=now,
            next_run_at=now,
            is_active=True
        ),
        PipelineSummary(
            id="pipeline-002",
            name="Weekly Report Generation",
            description="Generates weekly analytics reports",
            schedule="0 6 * * 1",
            last_run_status=PipelineStatus.COMPLETED,
            last_run_at=now,
            next_run_at=now,
            is_active=True
        ),
    ]

    if is_active is not None:
        pipelines = [p for p in pipelines if p.is_active == is_active]

    return PaginatedResponse.create(
        items=pipelines,
        total=len(pipelines),
        page=page,
        page_size=page_size
    )


@router.get(
    "/pipelines/{pipeline_id}",
    response_model=PipelineDetail,
    summary="Get pipeline details",
    description="Returns detailed information about a specific pipeline"
)
@traced("admin.pipelines.get")
async def get_pipeline(
    pipeline_id: str,
    user: CurrentUser,
) -> PipelineDetail:
    """
    Get detailed information about a specific pipeline.
    """
    add_span_attribute("user.id", user.user_id)
    add_span_attribute("pipeline.id", pipeline_id)

    # Mock data - will integrate with Dagster
    now = datetime.utcnow()

    if pipeline_id == "pipeline-001":
        return PipelineDetail(
            id="pipeline-001",
            name="Daily Data Sync",
            description="Syncs data from external sources daily",
            schedule="0 2 * * *",
            last_run_status=PipelineStatus.COMPLETED,
            last_run_at=now,
            next_run_at=now,
            is_active=True,
            steps=[
                {"name": "extract", "type": "extract", "source": "api"},
                {"name": "transform", "type": "transform", "rules": ["clean", "normalize"]},
                {"name": "load", "type": "load", "destination": "database"},
            ],
            config={"retry_count": 3, "timeout": 7200},
            created_at=now,
            updated_at=now
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Pipeline '{pipeline_id}' not found"
    )


@router.get(
    "/pipelines/runs",
    response_model=PaginatedResponse[PipelineRunSummary],
    summary="List pipeline runs",
    description="Returns a paginated list of pipeline runs"
)
@traced("admin.pipelines.runs.list")
async def list_pipeline_runs(
    user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    pipeline_id: Optional[str] = Query(default=None, description="Filter by pipeline ID"),
    status_filter: Optional[PipelineStatus] = Query(
        default=None,
        alias="status",
        description="Filter by status"
    ),
) -> PaginatedResponse[PipelineRunSummary]:
    """
    List pipeline runs with pagination and filtering.
    """
    add_span_attribute("user.id", user.user_id)
    add_span_attribute("pagination.page", page)

    # Mock data - will integrate with Dagster
    now = datetime.utcnow()
    runs = [
        PipelineRunSummary(
            run_id="run-001",
            pipeline_id="pipeline-001",
            pipeline_name="Daily Data Sync",
            status=PipelineStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            duration_seconds=125.5,
            triggered_by="scheduler"
        ),
        PipelineRunSummary(
            run_id="run-002",
            pipeline_id="pipeline-001",
            pipeline_name="Daily Data Sync",
            status=PipelineStatus.RUNNING,
            started_at=now,
            completed_at=None,
            duration_seconds=None,
            triggered_by="manual"
        ),
    ]

    if pipeline_id:
        runs = [r for r in runs if r.pipeline_id == pipeline_id]
    if status_filter:
        runs = [r for r in runs if r.status == status_filter]

    return PaginatedResponse.create(
        items=runs,
        total=len(runs),
        page=page,
        page_size=page_size
    )


# -----------------------------------------------------------------------------
# Endpoints - Settings
# -----------------------------------------------------------------------------

@router.get(
    "/settings",
    response_model=SystemSettings,
    summary="Get system settings",
    description="Returns current system settings"
)
@traced("admin.settings.get")
async def get_settings(
    user: CurrentUser,
) -> SystemSettings:
    """
    Get current system settings.
    """
    add_span_attribute("user.id", user.user_id)

    # Mock data - will integrate with settings storage
    return SystemSettings(
        site_name="Open Forge",
        default_timezone="UTC",
        max_concurrent_tasks=10,
        task_timeout_seconds=3600,
        enable_telemetry=True,
        enable_audit_log=True,
        retention_days=90,
        features={
            "dark_mode": True,
            "beta_features": False,
            "experimental_agents": False,
        }
    )


@router.put(
    "/settings",
    response_model=SystemSettings,
    summary="Update system settings",
    description="Updates system settings"
)
@traced("admin.settings.update")
async def update_settings(
    settings_update: SettingsUpdate,
    user: CurrentUser,
    db: DbSession,
) -> SystemSettings:
    """
    Update system settings.

    Only provided fields will be updated.
    """
    add_span_attribute("user.id", user.user_id)

    # TODO: Implement actual settings update
    # For now, return mock updated settings
    current = await get_settings(user)

    # Apply updates
    if settings_update.site_name is not None:
        current.site_name = settings_update.site_name
    if settings_update.default_timezone is not None:
        current.default_timezone = settings_update.default_timezone
    if settings_update.max_concurrent_tasks is not None:
        current.max_concurrent_tasks = settings_update.max_concurrent_tasks
    if settings_update.task_timeout_seconds is not None:
        current.task_timeout_seconds = settings_update.task_timeout_seconds
    if settings_update.enable_telemetry is not None:
        current.enable_telemetry = settings_update.enable_telemetry
    if settings_update.enable_audit_log is not None:
        current.enable_audit_log = settings_update.enable_audit_log
    if settings_update.retention_days is not None:
        current.retention_days = settings_update.retention_days
    if settings_update.features is not None:
        current.features.update(settings_update.features)

    return current


# -----------------------------------------------------------------------------
# Endpoints - Connectors
# -----------------------------------------------------------------------------

@router.get(
    "/settings/connectors",
    response_model=PaginatedResponse[ConnectorSummary],
    summary="List connectors",
    description="Returns a paginated list of configured connectors"
)
@traced("admin.connectors.list")
async def list_connectors(
    user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    type_filter: Optional[ConnectorType] = Query(
        default=None,
        alias="type",
        description="Filter by connector type"
    ),
) -> PaginatedResponse[ConnectorSummary]:
    """
    List all configured connectors.
    """
    add_span_attribute("user.id", user.user_id)
    add_span_attribute("pagination.page", page)

    # Mock data - will integrate with connector registry
    now = datetime.utcnow()
    connectors = [
        ConnectorSummary(
            id="conn-001",
            name="PostgreSQL Main",
            type=ConnectorType.DATABASE,
            status=ServiceStatus.HEALTHY,
            last_sync_at=now,
            created_at=now
        ),
        ConnectorSummary(
            id="conn-002",
            name="MinIO Storage",
            type=ConnectorType.FILE_STORAGE,
            status=ServiceStatus.HEALTHY,
            last_sync_at=now,
            created_at=now
        ),
        ConnectorSummary(
            id="conn-003",
            name="External API",
            type=ConnectorType.API,
            status=ServiceStatus.DEGRADED,
            last_sync_at=now,
            created_at=now
        ),
    ]

    if type_filter:
        connectors = [c for c in connectors if c.type == type_filter]

    return PaginatedResponse.create(
        items=connectors,
        total=len(connectors),
        page=page,
        page_size=page_size
    )


# -----------------------------------------------------------------------------
# Endpoints - Users
# -----------------------------------------------------------------------------

@router.get(
    "/settings/users",
    response_model=PaginatedResponse[UserSummary],
    summary="List users",
    description="Returns a paginated list of system users"
)
@traced("admin.users.list")
async def list_users(
    user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    role: Optional[str] = Query(default=None, description="Filter by role"),
) -> PaginatedResponse[UserSummary]:
    """
    List all system users.
    """
    add_span_attribute("user.id", user.user_id)
    add_span_attribute("pagination.page", page)

    # Mock data - will integrate with user management
    now = datetime.utcnow()
    users = [
        UserSummary(
            id="user-001",
            username="admin",
            email="admin@example.com",
            roles=["admin"],
            is_active=True,
            last_login_at=now,
            created_at=now
        ),
        UserSummary(
            id="user-002",
            username="analyst",
            email="analyst@example.com",
            roles=["analyst", "viewer"],
            is_active=True,
            last_login_at=now,
            created_at=now
        ),
        UserSummary(
            id="user-003",
            username="viewer",
            email="viewer@example.com",
            roles=["viewer"],
            is_active=False,
            last_login_at=None,
            created_at=now
        ),
    ]

    if is_active is not None:
        users = [u for u in users if u.is_active == is_active]
    if role:
        users = [u for u in users if role in u.roles]

    return PaginatedResponse.create(
        items=users,
        total=len(users),
        page=page,
        page_size=page_size
    )


# -----------------------------------------------------------------------------
# Endpoints - Audit Log
# -----------------------------------------------------------------------------

@router.get(
    "/settings/audit",
    response_model=PaginatedResponse[AuditLogEntry],
    summary="List audit logs",
    description="Returns a paginated list of audit log entries"
)
@traced("admin.audit.list")
async def list_audit_logs(
    user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    action: Optional[AuditAction] = Query(default=None, description="Filter by action"),
    resource_type: Optional[str] = Query(default=None, description="Filter by resource type"),
    user_id_filter: Optional[str] = Query(
        default=None,
        alias="user_id",
        description="Filter by user ID"
    ),
) -> PaginatedResponse[AuditLogEntry]:
    """
    List audit log entries with filtering.
    """
    add_span_attribute("user.id", user.user_id)
    add_span_attribute("pagination.page", page)

    # Mock data - will integrate with audit log storage
    now = datetime.utcnow()
    logs = [
        AuditLogEntry(
            id="log-001",
            action=AuditAction.CREATE,
            resource_type="engagement",
            resource_id="eng-001",
            user_id="user-001",
            username="admin",
            details={"name": "New Engagement"},
            ip_address="192.168.1.100",
            timestamp=now
        ),
        AuditLogEntry(
            id="log-002",
            action=AuditAction.EXECUTE,
            resource_type="task",
            resource_id="task-001",
            user_id="user-002",
            username="analyst",
            details={"task_type": "research"},
            ip_address="192.168.1.101",
            timestamp=now
        ),
        AuditLogEntry(
            id="log-003",
            action=AuditAction.LOGIN,
            resource_type="session",
            resource_id="session-001",
            user_id="user-001",
            username="admin",
            details=None,
            ip_address="192.168.1.100",
            timestamp=now
        ),
    ]

    if action:
        logs = [l for l in logs if l.action == action]
    if resource_type:
        logs = [l for l in logs if l.resource_type == resource_type]
    if user_id_filter:
        logs = [l for l in logs if l.user_id == user_id_filter]

    return PaginatedResponse.create(
        items=logs,
        total=len(logs),
        page=page,
        page_size=page_size
    )


# -----------------------------------------------------------------------------
# Endpoints - Dashboard
# -----------------------------------------------------------------------------

@router.get(
    "/dashboard/stats",
    response_model=DashboardStats,
    summary="Get dashboard statistics",
    description="Returns aggregated dashboard statistics"
)
@traced("admin.dashboard.stats")
async def get_dashboard_stats(
    user: CurrentUser,
) -> DashboardStats:
    """
    Get aggregated dashboard statistics.

    Returns summary metrics for the admin dashboard including
    engagement counts, task metrics, agent status, and system health.
    """
    add_span_attribute("user.id", user.user_id)

    # Mock data - will integrate with actual data sources
    return DashboardStats(
        total_engagements=42,
        active_engagements=8,
        total_tasks=1250,
        running_tasks=15,
        completed_tasks_today=45,
        failed_tasks_today=2,
        total_agents=16,
        active_agents=13,
        system_health=ServiceStatus.HEALTHY,
        pipeline_runs_today=12,
        last_updated=datetime.utcnow()
    )
