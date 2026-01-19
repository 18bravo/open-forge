"""
Review workflow endpoints.

Handles items requiring human review for data quality checks,
agent outputs, configuration changes, mappings, etc.
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

router = APIRouter(prefix="/reviews", tags=["Reviews"])


class ReviewStatus(str, Enum):
    """Review item states."""
    QUEUED = "queued"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    SKIPPED = "skipped"


class ReviewCategory(str, Enum):
    """Categories of review items."""
    DATA_QUALITY = "data_quality"
    AGENT_OUTPUT = "agent_output"
    CONFIGURATION = "configuration"
    MAPPING = "mapping"


class ReviewPriority(int, Enum):
    """Priority levels for review items (lower value = higher priority)."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


# Response Models

class ReviewItemSummary(BaseModel):
    """Lightweight review item summary for list endpoints."""
    id: str
    title: str
    category: ReviewCategory
    priority: ReviewPriority
    status: ReviewStatus
    created_at: datetime
    assigned_to: Optional[str] = None

    model_config = {"from_attributes": True}


class ReviewItem(ReviewItemSummary):
    """Full review item with details."""
    description: str
    context_data: Dict[str, Any] = Field(default_factory=dict)
    engagement_id: Optional[str] = None
    created_by: str
    assigned_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    review_result: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ReviewStats(BaseModel):
    """Review queue statistics."""
    queued: int = Field(description="Number of items in queue")
    in_review: int = Field(description="Number of items currently being reviewed")
    completed_today: int = Field(description="Number of items completed today")
    avg_review_time_minutes: float = Field(description="Average review time in minutes")


class CompleteReviewRequest(BaseModel):
    """Request to complete a review."""
    result: Dict[str, Any] = Field(description="Review result data")
    comments: Optional[str] = Field(default=None, description="Reviewer comments")
    flags: Optional[List[str]] = Field(default=None, description="Optional flags")


class DeferReviewRequest(BaseModel):
    """Request to defer a review."""
    reason: str = Field(min_length=1, max_length=500, description="Reason for deferring")


class SkipReviewRequest(BaseModel):
    """Request to skip a review."""
    reason: str = Field(min_length=1, max_length=500, description="Reason for skipping")


class AssignReviewRequest(BaseModel):
    """Request to assign a review."""
    user_id: str = Field(min_length=1, description="User ID to assign to")


# Endpoints

@router.get(
    "",
    response_model=PaginatedResponse[ReviewItemSummary],
    summary="List review items",
    description="Returns a paginated list of review items with filtering"
)
@traced("reviews.list")
async def list_reviews(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[ReviewStatus] = Query(default=None, alias="status"),
    category: Optional[ReviewCategory] = Query(default=None),
    priority: Optional[ReviewPriority] = Query(default=None),
    assigned_to_me: bool = Query(default=False, description="Show only items assigned to me"),
) -> PaginatedResponse[ReviewItemSummary]:
    """
    List review items with pagination and filtering.

    Supports filtering by status, category, priority, and assignment.
    """
    add_span_attribute("pagination.page", page)
    add_span_attribute("filter.status", status_filter.value if status_filter else None)
    add_span_attribute("filter.category", category.value if category else None)
    add_span_attribute("filter.assigned_to_me", assigned_to_me)

    # TODO: Integrate with ReviewQueue from human-interaction package
    # Currently returns mock data
    mock_items = [
        ReviewItemSummary(
            id=str(uuid4()),
            title="Data quality check - Customer records",
            category=ReviewCategory.DATA_QUALITY,
            priority=ReviewPriority.HIGH,
            status=ReviewStatus.QUEUED,
            created_at=datetime.utcnow(),
            assigned_to=None
        ),
        ReviewItemSummary(
            id=str(uuid4()),
            title="Agent output verification",
            category=ReviewCategory.AGENT_OUTPUT,
            priority=ReviewPriority.MEDIUM,
            status=ReviewStatus.IN_REVIEW,
            created_at=datetime.utcnow(),
            assigned_to=user.user_id
        ),
    ]

    return PaginatedResponse.create(
        items=mock_items,
        total=2,
        page=page,
        page_size=page_size
    )


@router.get(
    "/stats",
    response_model=ReviewStats,
    summary="Get review statistics",
    description="Returns statistics about the review queue"
)
@traced("reviews.stats")
async def get_review_stats(
    db: DbSession,
    user: CurrentUser,
) -> ReviewStats:
    """
    Get review queue statistics.

    Returns counts of items by status and average review time.
    """
    # TODO: Integrate with ReviewQueue.get_queue_stats() from human-interaction package
    # Currently returns mock data
    return ReviewStats(
        queued=5,
        in_review=2,
        completed_today=12,
        avg_review_time_minutes=8.5
    )


@router.get(
    "/{review_id}",
    response_model=ReviewItem,
    summary="Get review item",
    description="Returns detailed information about a review item"
)
@traced("reviews.get")
async def get_review(
    review_id: str,
    db: DbSession,
    user: CurrentUser,
) -> ReviewItem:
    """
    Get detailed information about a review item.
    """
    add_span_attribute("review.id", review_id)

    # TODO: Fetch from database via ReviewQueue.get_item()
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Review item {review_id} not found"
    )


@router.post(
    "/{review_id}/complete",
    response_model=ReviewItem,
    summary="Complete review",
    description="Complete a review with the provided result"
)
@traced("reviews.complete")
async def complete_review(
    review_id: str,
    request: CompleteReviewRequest,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> ReviewItem:
    """
    Complete a review with the provided result.

    The review item must be in QUEUED or IN_REVIEW status.
    """
    add_span_attribute("review.id", review_id)

    # TODO: Implement via ReviewQueue.complete_review()
    # 1. Fetch the review item
    # 2. Validate status is QUEUED or IN_REVIEW
    # 3. Update status to COMPLETED
    # 4. Store result and comments
    # 5. Emit review.item_completed event

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Review item {review_id} not found"
    )


@router.post(
    "/{review_id}/defer",
    response_model=ReviewItem,
    summary="Defer review",
    description="Defer a review item for later"
)
@traced("reviews.defer")
async def defer_review(
    review_id: str,
    request: DeferReviewRequest,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> ReviewItem:
    """
    Defer a review item for later processing.

    The review item must be in QUEUED or IN_REVIEW status.
    """
    add_span_attribute("review.id", review_id)

    # TODO: Implement via ReviewQueue.defer_item()
    # 1. Fetch the review item
    # 2. Validate status is QUEUED or IN_REVIEW
    # 3. Update status to DEFERRED
    # 4. Store deferral reason
    # 5. Emit review.item_deferred event

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Review item {review_id} not found"
    )


@router.post(
    "/{review_id}/skip",
    response_model=ReviewItem,
    summary="Skip review",
    description="Skip a review item"
)
@traced("reviews.skip")
async def skip_review(
    review_id: str,
    request: SkipReviewRequest,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> ReviewItem:
    """
    Skip a review item.

    The review item must be in QUEUED or IN_REVIEW status.
    Skipped items are marked as SKIPPED and won't appear in the active queue.
    """
    add_span_attribute("review.id", review_id)

    # TODO: Implement similar to defer but with SKIPPED status
    # 1. Fetch the review item
    # 2. Validate status is QUEUED or IN_REVIEW
    # 3. Update status to SKIPPED
    # 4. Store skip reason
    # 5. Emit review.item_skipped event

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Review item {review_id} not found"
    )


@router.post(
    "/{review_id}/assign",
    response_model=ReviewItem,
    summary="Assign review",
    description="Assign a review item to a user"
)
@traced("reviews.assign")
async def assign_review(
    review_id: str,
    request: AssignReviewRequest,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> ReviewItem:
    """
    Assign a review item to a specific user.

    The review item must be in QUEUED status.
    Assigning moves the item to IN_REVIEW status.
    """
    add_span_attribute("review.id", review_id)
    add_span_attribute("assign.user_id", request.user_id)

    # TODO: Implement via ReviewQueue.reassign_item()
    # 1. Fetch the review item
    # 2. Validate status is QUEUED or IN_REVIEW
    # 3. Update assigned_to and assigned_at
    # 4. Set status to IN_REVIEW
    # 5. Emit review.item_assigned event

    await event_bus.publish(
        "review.item_assigned",
        {
            "review_id": review_id,
            "assigned_to": request.user_id,
            "assigned_by": user.user_id,
        }
    )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Review item {review_id} not found"
    )


@router.post(
    "/{review_id}/claim",
    response_model=ReviewItem,
    summary="Claim review",
    description="Claim a review item for yourself"
)
@traced("reviews.claim")
async def claim_review(
    review_id: str,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> ReviewItem:
    """
    Claim a review item for the current user.

    Convenience endpoint that assigns the item to the current user.
    """
    add_span_attribute("review.id", review_id)

    # TODO: Implement by calling assign with current user
    # Equivalent to assign_review with user.user_id

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Review item {review_id} not found"
    )


@router.post(
    "/{review_id}/release",
    response_model=ReviewItem,
    summary="Release review",
    description="Release a claimed review item back to the queue"
)
@traced("reviews.release")
async def release_review(
    review_id: str,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> ReviewItem:
    """
    Release a review item back to the queue.

    Only the assigned user or an admin can release an item.
    The item returns to QUEUED status.
    """
    add_span_attribute("review.id", review_id)

    # TODO: Implement release logic
    # 1. Fetch the review item
    # 2. Validate user is assigned or is admin
    # 3. Clear assigned_to and assigned_at
    # 4. Set status to QUEUED
    # 5. Emit review.item_released event

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Review item {review_id} not found"
    )
