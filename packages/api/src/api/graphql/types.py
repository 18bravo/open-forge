"""
GraphQL types for Open Forge.
"""
from typing import Any, List, Optional
from datetime import datetime
from enum import Enum

import strawberry


@strawberry.enum
class EngagementStatusGQL(Enum):
    """Engagement lifecycle status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@strawberry.enum
class EngagementPriorityGQL(Enum):
    """Engagement priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@strawberry.enum
class AgentTaskStatusGQL(Enum):
    """Agent task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@strawberry.enum
class DataSourceTypeGQL(Enum):
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


@strawberry.enum
class ApprovalStatusGQL(Enum):
    """Approval request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@strawberry.type
class DataSourceReference:
    """Reference to a data source used in an engagement."""
    source_id: str
    source_type: str
    access_mode: str


@strawberry.type
class Engagement:
    """An engagement represents a unit of analytical work."""
    id: str
    name: str
    description: Optional[str]
    objective: str
    status: EngagementStatusGQL
    priority: EngagementPriorityGQL
    data_sources: List[DataSourceReference]
    tags: List[str]
    requires_approval: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    @strawberry.field
    async def tasks(self, limit: int = 10) -> List["AgentTask"]:
        """Get tasks associated with this engagement."""
        # TODO: Implement task fetching
        return []


@strawberry.type
class EngagementConnection:
    """Paginated engagement list."""
    items: List[Engagement]
    total: int
    page: int
    page_size: int
    total_pages: int


@strawberry.type
class ToolCall:
    """A tool call made by an agent."""
    id: str
    name: str
    arguments: strawberry.scalars.JSON
    result: Optional[strawberry.scalars.JSON]
    error: Optional[str]
    executed_at: Optional[datetime]
    duration_ms: Optional[int]


@strawberry.type
class AgentMessage:
    """A message in the agent conversation."""
    id: str
    role: str
    content: str
    tool_calls: Optional[List[ToolCall]]
    timestamp: datetime


@strawberry.type
class AgentTask:
    """An agent task represents a specific AI-powered operation."""
    id: str
    engagement_id: str
    task_type: str
    description: str
    status: AgentTaskStatusGQL
    input_data: Optional[strawberry.scalars.JSON]
    output_data: Optional[strawberry.scalars.JSON]
    tools: List[str]
    max_iterations: int
    current_iteration: int
    timeout_seconds: int
    messages: List[AgentMessage]
    pending_tool_approvals: List[ToolCall]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    @strawberry.field
    async def engagement(self) -> Optional[Engagement]:
        """Get the parent engagement."""
        # TODO: Implement engagement fetching
        return None


@strawberry.type
class AgentTaskConnection:
    """Paginated agent task list."""
    items: List[AgentTask]
    total: int
    page: int
    page_size: int
    total_pages: int


@strawberry.type
class DataSource:
    """A data source connection."""
    id: str
    name: str
    description: Optional[str]
    source_type: DataSourceTypeGQL
    status: str
    tags: List[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_tested_at: Optional[datetime]
    last_error: Optional[str]


@strawberry.type
class DataSourceConnection:
    """Paginated data source list."""
    items: List[DataSource]
    total: int
    page: int
    page_size: int
    total_pages: int


@strawberry.type
class ApprovalRequest:
    """An approval request."""
    id: str
    approval_type: str
    status: ApprovalStatusGQL
    title: str
    description: str
    resource_id: str
    resource_type: str
    requested_by: str
    requested_at: datetime
    details: strawberry.scalars.JSON
    expires_at: Optional[datetime]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]


@strawberry.type
class ApprovalRequestConnection:
    """Paginated approval request list."""
    items: List[ApprovalRequest]
    total: int
    page: int
    page_size: int
    total_pages: int


# Input types

@strawberry.input
class DataSourceReferenceInput:
    """Input for data source reference."""
    source_id: str
    source_type: str
    access_mode: str = "read"


@strawberry.input
class EngagementCreateInput:
    """Input for creating an engagement."""
    name: str
    description: Optional[str] = None
    objective: str
    priority: EngagementPriorityGQL = EngagementPriorityGQL.MEDIUM
    data_sources: List[DataSourceReferenceInput] = strawberry.field(default_factory=list)
    tags: List[str] = strawberry.field(default_factory=list)
    requires_approval: bool = True


@strawberry.input
class EngagementUpdateInput:
    """Input for updating an engagement."""
    name: Optional[str] = None
    description: Optional[str] = None
    objective: Optional[str] = None
    priority: Optional[EngagementPriorityGQL] = None
    data_sources: Optional[List[DataSourceReferenceInput]] = None
    tags: Optional[List[str]] = None


@strawberry.input
class AgentTaskCreateInput:
    """Input for creating an agent task."""
    engagement_id: str
    task_type: str
    description: str
    input_data: Optional[strawberry.scalars.JSON] = None
    tools: List[str] = strawberry.field(default_factory=list)
    max_iterations: int = 10
    timeout_seconds: int = 300
    requires_approval_for_tools: List[str] = strawberry.field(default_factory=list)


@strawberry.input
class ToolApprovalInput:
    """Input for approving/rejecting a tool call."""
    tool_call_id: str
    approved: bool
    reason: Optional[str] = None
    modified_arguments: Optional[strawberry.scalars.JSON] = None


@strawberry.input
class ApprovalDecisionInput:
    """Input for making an approval decision."""
    approved: bool
    reason: Optional[str] = None
    conditions: Optional[strawberry.scalars.JSON] = None


# Result types

@strawberry.type
class MutationResult:
    """Generic mutation result."""
    success: bool
    message: str
    id: Optional[str] = None


@strawberry.type
class EngagementMutationResult:
    """Result of an engagement mutation."""
    success: bool
    message: str
    engagement: Optional[Engagement] = None


@strawberry.type
class AgentTaskMutationResult:
    """Result of an agent task mutation."""
    success: bool
    message: str
    task: Optional[AgentTask] = None


@strawberry.type
class ApprovalMutationResult:
    """Result of an approval mutation."""
    success: bool
    message: str
    approval: Optional[ApprovalRequest] = None
