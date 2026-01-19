"""
Agent task management endpoints.
"""
from typing import Optional
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from api.dependencies import DbSession, CurrentUser, EventBusDep
from api.schemas.common import PaginatedResponse, SuccessResponse
from api.schemas.agent import (
    AgentTaskCreate,
    AgentTaskResponse,
    AgentTaskSummary,
    AgentTaskStatus,
    AgentTaskCancel,
    AgentMessage,
    ToolApprovalRequest,
)
from core.observability.tracing import traced, add_span_attribute

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post(
    "/tasks",
    response_model=AgentTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent task",
    description="Creates a new agent task for an engagement"
)
@traced("agents.tasks.create")
async def create_task(
    task: AgentTaskCreate,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> AgentTaskResponse:
    """
    Create a new agent task.

    The task will be queued for execution by an agent worker.
    """
    task_id = str(uuid4())
    now = datetime.utcnow()

    add_span_attribute("task.id", task_id)
    add_span_attribute("task.engagement_id", task.engagement_id)
    add_span_attribute("task.type", task.task_type)

    # TODO: Persist to database and queue for execution
    response = AgentTaskResponse(
        id=task_id,
        engagement_id=task.engagement_id,
        task_type=task.task_type,
        description=task.description,
        status=AgentTaskStatus.PENDING,
        input_data=task.input_data,
        tools=task.tools,
        max_iterations=task.max_iterations,
        timeout_seconds=task.timeout_seconds,
        created_at=now,
        metadata=task.metadata,
    )

    # Publish task created event
    await event_bus.publish(
        "agent.task.created",
        {
            "task_id": task_id,
            "engagement_id": task.engagement_id,
            "task_type": task.task_type,
        }
    )

    return response


@router.get(
    "/tasks",
    response_model=PaginatedResponse[AgentTaskSummary],
    summary="List agent tasks",
    description="Returns a paginated list of agent tasks"
)
@traced("agents.tasks.list")
async def list_tasks(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    engagement_id: Optional[str] = Query(default=None, description="Filter by engagement"),
    status_filter: Optional[AgentTaskStatus] = Query(
        default=None,
        alias="status",
        description="Filter by status"
    ),
) -> PaginatedResponse[AgentTaskSummary]:
    """
    List agent tasks with pagination and filtering.
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
    "/tasks/{task_id}",
    response_model=AgentTaskResponse,
    summary="Get task details",
    description="Returns detailed information about a specific task"
)
@traced("agents.tasks.get")
async def get_task(
    task_id: str,
    db: DbSession,
    user: CurrentUser,
) -> AgentTaskResponse:
    """
    Get detailed information about a specific agent task.

    Includes the full conversation history and any pending approvals.
    """
    add_span_attribute("task.id", task_id)

    # TODO: Fetch from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found"
    )


@router.get(
    "/tasks/{task_id}/messages",
    response_model=list[AgentMessage],
    summary="Get task messages",
    description="Returns the conversation history for a task"
)
@traced("agents.tasks.messages")
async def get_task_messages(
    task_id: str,
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AgentMessage]:
    """
    Get the conversation history for a task.

    Returns messages in chronological order.
    """
    add_span_attribute("task.id", task_id)

    # TODO: Fetch messages from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found"
    )


@router.get(
    "/tasks/{task_id}/stream",
    summary="Stream task events",
    description="Server-sent events stream for real-time task updates"
)
@traced("agents.tasks.stream")
async def stream_task_events(
    task_id: str,
    user: CurrentUser,
) -> StreamingResponse:
    """
    Stream real-time events for a task.

    Returns a server-sent events (SSE) stream with task progress updates.
    """
    add_span_attribute("task.id", task_id)

    async def event_generator():
        """Generate SSE events."""
        # TODO: Implement actual event streaming from Redis
        yield f"data: {{'event': 'connected', 'task_id': '{task_id}'}}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post(
    "/tasks/{task_id}/approve-tool",
    response_model=AgentTaskResponse,
    summary="Approve tool execution",
    description="Approves or rejects a pending tool call"
)
@traced("agents.tasks.approve_tool")
async def approve_tool_execution(
    task_id: str,
    approval: ToolApprovalRequest,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> AgentTaskResponse:
    """
    Approve or reject a pending tool call.

    Some tools require human approval before execution. This endpoint
    allows approving or rejecting those tool calls.
    """
    add_span_attribute("task.id", task_id)
    add_span_attribute("tool_call.id", approval.tool_call_id)
    add_span_attribute("tool_call.approved", approval.approved)

    # TODO: Implement approval logic
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found"
    )


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=AgentTaskResponse,
    summary="Cancel task",
    description="Cancels a running task"
)
@traced("agents.tasks.cancel")
async def cancel_task(
    task_id: str,
    cancel_request: AgentTaskCancel,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> AgentTaskResponse:
    """
    Cancel a running agent task.

    Only tasks in PENDING, QUEUED, RUNNING, or WAITING_APPROVAL status can be cancelled.
    """
    add_span_attribute("task.id", task_id)

    # TODO: Implement cancellation
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found"
    )


@router.post(
    "/tasks/{task_id}/retry",
    response_model=AgentTaskResponse,
    summary="Retry task",
    description="Retries a failed task"
)
@traced("agents.tasks.retry")
async def retry_task(
    task_id: str,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> AgentTaskResponse:
    """
    Retry a failed task.

    Creates a new task with the same configuration as the failed one.
    """
    add_span_attribute("task.id", task_id)

    # TODO: Implement retry logic
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found"
    )
