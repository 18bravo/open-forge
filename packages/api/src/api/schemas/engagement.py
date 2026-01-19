"""
Engagement-related Pydantic schemas.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class EngagementStatus(str, Enum):
    """Engagement lifecycle status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class EngagementPriority(str, Enum):
    """Engagement priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataSourceReference(BaseModel):
    """Reference to a data source used in an engagement."""
    source_id: str = Field(description="Data source ID")
    source_type: str = Field(description="Type of data source")
    access_mode: str = Field(default="read", description="Access mode: read, write, or readwrite")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Source-specific config")


class EngagementCreate(BaseModel):
    """Schema for creating a new engagement."""
    name: str = Field(min_length=1, max_length=255, description="Engagement name")
    description: Optional[str] = Field(default=None, max_length=2000, description="Description")
    objective: str = Field(min_length=1, description="Main objective of the engagement")
    priority: EngagementPriority = Field(default=EngagementPriority.MEDIUM)
    data_sources: List[DataSourceReference] = Field(
        default_factory=list,
        description="Data sources to use"
    )
    agent_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for the AI agent"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    requires_approval: bool = Field(
        default=True,
        description="Whether this engagement requires approval before execution"
    )


class EngagementUpdate(BaseModel):
    """Schema for updating an existing engagement."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    objective: Optional[str] = Field(default=None, min_length=1)
    priority: Optional[EngagementPriority] = None
    data_sources: Optional[List[DataSourceReference]] = None
    agent_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EngagementResponse(BaseModel):
    """Schema for engagement response."""
    id: str = Field(description="Unique engagement ID")
    name: str
    description: Optional[str] = None
    objective: str
    status: EngagementStatus
    priority: EngagementPriority
    data_sources: List[DataSourceReference] = Field(default_factory=list)
    agent_config: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    requires_approval: bool
    created_by: str = Field(description="User ID of creator")
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class EngagementSummary(BaseModel):
    """Lightweight engagement summary for list views."""
    id: str
    name: str
    status: EngagementStatus
    priority: EngagementPriority
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EngagementStatusUpdate(BaseModel):
    """Schema for updating engagement status."""
    status: EngagementStatus = Field(description="New status")
    reason: Optional[str] = Field(default=None, description="Reason for status change")


class EngagementExecutionResult(BaseModel):
    """Result of an engagement execution."""
    engagement_id: str
    status: EngagementStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    outputs: Optional[Dict[str, Any]] = None
    artifacts: List[str] = Field(default_factory=list, description="Generated artifact IDs")
    error_message: Optional[str] = None
    execution_time_seconds: Optional[float] = None
