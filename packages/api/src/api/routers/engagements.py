"""
Engagement CRUD endpoints.
"""
from typing import Optional
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from api.dependencies import DbSession, CurrentUser, EventBusDep
from api.schemas.common import PaginatedResponse, SuccessResponse
from api.schemas.engagement import (
    EngagementCreate,
    EngagementUpdate,
    EngagementResponse,
    EngagementSummary,
    EngagementStatus,
    EngagementStatusUpdate,
    EngagementExecutionResult,
)
from core.observability.tracing import traced, add_span_attribute

router = APIRouter(prefix="/engagements", tags=["Engagements"])


@router.post(
    "",
    response_model=EngagementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new engagement",
    description="Creates a new engagement with the specified configuration"
)
@traced("engagements.create")
async def create_engagement(
    engagement: EngagementCreate,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> EngagementResponse:
    """
    Create a new engagement.

    The engagement will be created in DRAFT status. If requires_approval is True,
    it must be approved before execution.
    """
    engagement_id = str(uuid4())
    now = datetime.utcnow()

    add_span_attribute("engagement.id", engagement_id)
    add_span_attribute("engagement.name", engagement.name)

    # TODO: Persist to database
    # For now, return a mock response
    response = EngagementResponse(
        id=engagement_id,
        name=engagement.name,
        description=engagement.description,
        objective=engagement.objective,
        status=EngagementStatus.DRAFT,
        priority=engagement.priority,
        data_sources=engagement.data_sources,
        agent_config=engagement.agent_config,
        tags=engagement.tags,
        metadata=engagement.metadata,
        requires_approval=engagement.requires_approval,
        created_by=user.id,
        created_at=now,
        updated_at=now,
    )

    # Publish creation event
    await event_bus.publish(
        "engagement.created",
        {
            "engagement_id": engagement_id,
            "name": engagement.name,
            "created_by": user.id,
        }
    )

    return response


@router.get(
    "",
    response_model=PaginatedResponse[EngagementSummary],
    summary="List engagements",
    description="Returns a paginated list of engagements"
)
@traced("engagements.list")
async def list_engagements(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[EngagementStatus] = Query(
        default=None,
        alias="status",
        description="Filter by status"
    ),
    search: Optional[str] = Query(default=None, description="Search in name/description"),
) -> PaginatedResponse[EngagementSummary]:
    """
    List engagements with pagination and filtering.

    Supports filtering by status and searching by name/description.
    """
    add_span_attribute("pagination.page", page)
    add_span_attribute("pagination.page_size", page_size)

    # TODO: Implement actual database query
    # For now, return empty paginated response
    return PaginatedResponse.create(
        items=[],
        total=0,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{engagement_id}",
    response_model=EngagementResponse,
    summary="Get engagement details",
    description="Returns detailed information about a specific engagement"
)
@traced("engagements.get")
async def get_engagement(
    engagement_id: str,
    db: DbSession,
    user: CurrentUser,
) -> EngagementResponse:
    """
    Get detailed information about a specific engagement.
    """
    add_span_attribute("engagement.id", engagement_id)

    # TODO: Fetch from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Engagement {engagement_id} not found"
    )


@router.put(
    "/{engagement_id}",
    response_model=EngagementResponse,
    summary="Update engagement",
    description="Updates an existing engagement"
)
@traced("engagements.update")
async def update_engagement(
    engagement_id: str,
    engagement: EngagementUpdate,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> EngagementResponse:
    """
    Update an existing engagement.

    Only engagements in DRAFT or PAUSED status can be updated.
    """
    add_span_attribute("engagement.id", engagement_id)

    # TODO: Implement actual update
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Engagement {engagement_id} not found"
    )


@router.delete(
    "/{engagement_id}",
    response_model=SuccessResponse,
    summary="Delete engagement",
    description="Deletes an engagement"
)
@traced("engagements.delete")
async def delete_engagement(
    engagement_id: str,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> SuccessResponse:
    """
    Delete an engagement.

    Only engagements in DRAFT, COMPLETED, CANCELLED, or FAILED status can be deleted.
    """
    add_span_attribute("engagement.id", engagement_id)

    # TODO: Implement actual deletion
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Engagement {engagement_id} not found"
    )


@router.post(
    "/{engagement_id}/status",
    response_model=EngagementResponse,
    summary="Update engagement status",
    description="Updates the status of an engagement"
)
@traced("engagements.update_status")
async def update_engagement_status(
    engagement_id: str,
    status_update: EngagementStatusUpdate,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> EngagementResponse:
    """
    Update the status of an engagement.

    Status transitions are validated to ensure they follow the engagement lifecycle.
    """
    add_span_attribute("engagement.id", engagement_id)
    add_span_attribute("engagement.new_status", status_update.status.value)

    # TODO: Implement status update with validation
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Engagement {engagement_id} not found"
    )


@router.post(
    "/{engagement_id}/execute",
    response_model=EngagementExecutionResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute engagement",
    description="Starts execution of an approved engagement"
)
@traced("engagements.execute")
async def execute_engagement(
    engagement_id: str,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> EngagementExecutionResult:
    """
    Start execution of an engagement.

    The engagement must be in APPROVED status to be executed.
    Returns immediately with IN_PROGRESS status; actual execution happens asynchronously.
    """
    add_span_attribute("engagement.id", engagement_id)

    # TODO: Implement execution trigger
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Engagement {engagement_id} not found"
    )


@router.post(
    "/{engagement_id}/cancel",
    response_model=EngagementResponse,
    summary="Cancel engagement",
    description="Cancels a running engagement"
)
@traced("engagements.cancel")
async def cancel_engagement(
    engagement_id: str,
    reason: Optional[str] = Query(default=None, description="Cancellation reason"),
    db: DbSession = None,
    user: CurrentUser = None,
    event_bus: EventBusDep = None,
) -> EngagementResponse:
    """
    Cancel a running engagement.

    Only engagements in IN_PROGRESS status can be cancelled.
    """
    add_span_attribute("engagement.id", engagement_id)

    # TODO: Implement cancellation
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Engagement {engagement_id} not found"
    )


@router.get(
    "/{engagement_id}/ontology",
    summary="Get engagement ontology",
    description="Returns the ontology schema for an engagement"
)
@traced("engagements.get_ontology")
async def get_engagement_ontology(engagement_id: str):
    """Get ontology schema for an engagement."""
    add_span_attribute("engagement.id", engagement_id)

    # TODO: Integrate with ontology package
    # Return structure that UI expects
    return {
        "entities": [
            {
                "name": "Customer",
                "description": "A customer entity",
                "attributes": [
                    {"name": "id", "type": "string", "required": True},
                    {"name": "name", "type": "string", "required": True},
                    {"name": "email", "type": "string", "required": False},
                ],
                "relationships": [
                    {"name": "orders", "target": "Order", "type": "one_to_many"}
                ]
            },
            {
                "name": "Order",
                "description": "A customer order",
                "attributes": [
                    {"name": "id", "type": "string", "required": True},
                    {"name": "total", "type": "decimal", "required": True},
                    {"name": "status", "type": "enum", "required": True},
                ],
                "relationships": []
            }
        ],
        "version": "1.0.0",
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get(
    "/{engagement_id}/activities",
    summary="Get engagement activities",
    description="Returns the activity log for an engagement"
)
@traced("engagements.get_activities")
async def get_engagement_activities(
    engagement_id: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of activities to return")
):
    """Get activity log for an engagement."""
    add_span_attribute("engagement.id", engagement_id)
    add_span_attribute("activities.limit", limit)

    # TODO: Integrate with event bus to fetch real activities
    return {
        "items": [
            {
                "id": "act-1",
                "type": "agent_task_started",
                "title": "Discovery agent started",
                "description": "Analyzing data sources",
                "timestamp": datetime.utcnow().isoformat(),
                "actor": "DiscoveryAgent"
            },
            {
                "id": "act-2",
                "type": "data_source_connected",
                "title": "PostgreSQL connected",
                "description": "Successfully connected to source database",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]
    }


@router.get(
    "/{engagement_id}/stats",
    summary="Get engagement statistics",
    description="Returns statistics for an engagement"
)
@traced("engagements.get_stats")
async def get_engagement_stats(engagement_id: str):
    """Get statistics for an engagement."""
    add_span_attribute("engagement.id", engagement_id)

    # TODO: Calculate real stats from agent tasks, data processed, etc.
    return {
        "runtime": {
            "hours": 24,
            "minutes": 15,
            "started_at": datetime.utcnow().isoformat()
        },
        "data_processed": {
            "bytes": 2500000000,  # 2.5 GB
            "records": 150000
        },
        "agent_tasks": {
            "total": 12,
            "running": 3,
            "completed": 9,
            "failed": 0
        },
        "pending_approvals": 1
    }
