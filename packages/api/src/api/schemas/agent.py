"""
Agent-related Pydantic schemas.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AgentTaskStatus(str, Enum):
    """Agent task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentMessageRole(str, Enum):
    """Role of the message sender."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    """Representation of a tool call made by the agent."""
    id: str = Field(description="Unique tool call ID")
    name: str = Field(description="Tool name")
    arguments: Dict[str, Any] = Field(description="Tool arguments")
    result: Optional[Any] = Field(default=None, description="Tool execution result")
    error: Optional[str] = Field(default=None, description="Error if tool failed")
    executed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class AgentMessage(BaseModel):
    """A message in the agent conversation."""
    id: str = Field(description="Message ID")
    role: AgentMessageRole
    content: str = Field(description="Message content")
    tool_calls: Optional[List[ToolCall]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class AgentTaskCreate(BaseModel):
    """Schema for creating a new agent task."""
    engagement_id: str = Field(description="Parent engagement ID")
    task_type: str = Field(description="Type of task to execute")
    description: str = Field(description="Task description")
    input_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Input data for the task"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="List of tools the agent can use"
    )
    max_iterations: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of agent iterations"
    )
    timeout_seconds: int = Field(
        default=300,
        ge=10,
        le=3600,
        description="Task timeout in seconds"
    )
    requires_approval_for_tools: List[str] = Field(
        default_factory=list,
        description="Tools that require human approval before execution"
    )
    metadata: Optional[Dict[str, Any]] = None


class AgentTaskResponse(BaseModel):
    """Schema for agent task response."""
    id: str = Field(description="Task ID")
    engagement_id: str
    task_type: str
    description: str
    status: AgentTaskStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    tools: List[str] = Field(default_factory=list)
    max_iterations: int
    current_iteration: int = Field(default=0)
    timeout_seconds: int
    messages: List[AgentMessage] = Field(default_factory=list)
    pending_tool_approvals: List[ToolCall] = Field(
        default_factory=list,
        description="Tool calls waiting for approval"
    )
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class AgentTaskSummary(BaseModel):
    """Lightweight task summary for list views."""
    id: str
    engagement_id: str
    task_type: str
    status: AgentTaskStatus
    current_iteration: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ToolApprovalRequest(BaseModel):
    """Request to approve or reject a tool call."""
    tool_call_id: str = Field(description="ID of the tool call to approve/reject")
    approved: bool = Field(description="Whether to approve the tool call")
    reason: Optional[str] = Field(default=None, description="Reason for approval/rejection")
    modified_arguments: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Modified arguments if approved with changes"
    )


class AgentTaskCancel(BaseModel):
    """Request to cancel an agent task."""
    reason: Optional[str] = Field(default=None, description="Cancellation reason")


class AgentStreamEvent(BaseModel):
    """Event streamed during agent execution."""
    event_type: str = Field(description="Type of event")
    task_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(description="Event-specific data")
