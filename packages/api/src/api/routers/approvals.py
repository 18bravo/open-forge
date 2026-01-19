"""
Approval workflow endpoints.
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

router = APIRouter(prefix="/approvals", tags=["Approvals"])


class ApprovalType(str, Enum):
    """Types of items requiring approval."""
    ENGAGEMENT = "engagement"
    TOOL_EXECUTION = "tool_execution"
    DATA_ACCESS = "data_access"
    SCHEMA_CHANGE = "schema_change"
    DEPLOYMENT = "deployment"


class ApprovalStatus(str, Enum):
    """Approval request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalRequest(BaseModel):
    """An approval request."""
    id: str
    approval_type: ApprovalType
    status: ApprovalStatus
    title: str
    description: str
    resource_id: str = Field(description="ID of the resource requiring approval")
    resource_type: str = Field(description="Type of resource")
    requested_by: str
    requested_at: datetime
    details: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class ApprovalRequestSummary(BaseModel):
    """Lightweight approval request summary."""
    id: str
    approval_type: ApprovalType
    status: ApprovalStatus
    title: str
    resource_id: str
    requested_by: str
    requested_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    """Decision on an approval request."""
    approved: bool = Field(description="Whether to approve or reject")
    reason: Optional[str] = Field(default=None, description="Reason for decision")
    conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Conditions attached to approval"
    )


class ApprovalPolicy(BaseModel):
    """Approval policy configuration."""
    id: str
    name: str
    description: Optional[str] = None
    approval_type: ApprovalType
    rules: Dict[str, Any] = Field(description="Policy rules")
    required_approvers: int = Field(default=1, ge=1)
    auto_approve_conditions: Optional[Dict[str, Any]] = None
    expiration_hours: int = Field(default=24, ge=1)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateApprovalRequest(BaseModel):
    """Schema for creating an approval request."""
    approval_type: ApprovalType
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=2000)
    resource_id: str
    resource_type: str
    details: Dict[str, Any] = Field(default_factory=dict)
    expiration_hours: Optional[int] = Field(default=None, ge=1, le=168)


@router.get(
    "",
    response_model=PaginatedResponse[ApprovalRequestSummary],
    summary="List approval requests",
    description="Returns a paginated list of approval requests"
)
@traced("approvals.list")
async def list_approvals(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    approval_type: Optional[ApprovalType] = Query(default=None, alias="type"),
    status_filter: Optional[ApprovalStatus] = Query(default=None, alias="status"),
    pending_only: bool = Query(default=False, description="Show only pending requests"),
) -> PaginatedResponse[ApprovalRequestSummary]:
    """
    List approval requests with pagination and filtering.

    By default, shows approvals the user can act on.
    """
    add_span_attribute("pagination.page", page)
    add_span_attribute("filter.pending_only", pending_only)

    # TODO: Implement database query
    return PaginatedResponse.create(
        items=[],
        total=0,
        page=page,
        page_size=page_size
    )


@router.get(
    "/my-requests",
    response_model=PaginatedResponse[ApprovalRequestSummary],
    summary="List my approval requests",
    description="Returns approval requests created by the current user"
)
@traced("approvals.my_requests")
async def list_my_requests(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[ApprovalStatus] = Query(default=None, alias="status"),
) -> PaginatedResponse[ApprovalRequestSummary]:
    """
    List approval requests created by the current user.
    """
    add_span_attribute("pagination.page", page)
    add_span_attribute("user.id", user.user_id)

    # TODO: Implement database query
    return PaginatedResponse.create(
        items=[],
        total=0,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{approval_id}",
    response_model=ApprovalRequest,
    summary="Get approval request",
    description="Returns detailed information about an approval request"
)
@traced("approvals.get")
async def get_approval(
    approval_id: str,
    db: DbSession,
    user: CurrentUser,
) -> ApprovalRequest:
    """
    Get detailed information about an approval request.
    """
    add_span_attribute("approval.id", approval_id)

    # TODO: Fetch from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Approval request {approval_id} not found"
    )


@router.post(
    "",
    response_model=ApprovalRequest,
    status_code=status.HTTP_201_CREATED,
    summary="Create approval request",
    description="Creates a new approval request"
)
@traced("approvals.create")
async def create_approval(
    request: CreateApprovalRequest,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> ApprovalRequest:
    """
    Create a new approval request.

    The request will be routed to appropriate approvers based on the approval type.
    """
    approval_id = str(uuid4())
    now = datetime.utcnow()

    add_span_attribute("approval.id", approval_id)
    add_span_attribute("approval.type", request.approval_type.value)

    expires_at = None
    if request.expiration_hours:
        from datetime import timedelta
        expires_at = now + timedelta(hours=request.expiration_hours)

    # TODO: Persist to database
    response = ApprovalRequest(
        id=approval_id,
        approval_type=request.approval_type,
        status=ApprovalStatus.PENDING,
        title=request.title,
        description=request.description,
        resource_id=request.resource_id,
        resource_type=request.resource_type,
        requested_by=user.user_id,
        requested_at=now,
        details=request.details,
        expires_at=expires_at,
    )

    await event_bus.publish(
        "approval.requested",
        {
            "approval_id": approval_id,
            "type": request.approval_type.value,
            "resource_id": request.resource_id,
            "requested_by": user.user_id,
        }
    )

    return response


@router.post(
    "/{approval_id}/decide",
    response_model=ApprovalRequest,
    summary="Decide on approval",
    description="Approves or rejects an approval request"
)
@traced("approvals.decide")
async def decide_approval(
    approval_id: str,
    decision: ApprovalDecision,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> ApprovalRequest:
    """
    Make a decision on an approval request.

    Only users with appropriate permissions can make approval decisions.
    """
    add_span_attribute("approval.id", approval_id)
    add_span_attribute("decision.approved", decision.approved)

    # TODO: Implement decision logic
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Approval request {approval_id} not found"
    )


@router.post(
    "/{approval_id}/cancel",
    response_model=ApprovalRequest,
    summary="Cancel approval request",
    description="Cancels a pending approval request"
)
@traced("approvals.cancel")
async def cancel_approval(
    approval_id: str,
    reason: Optional[str] = Query(default=None, description="Cancellation reason"),
    db: DbSession = None,
    user: CurrentUser = None,
    event_bus: EventBusDep = None,
) -> ApprovalRequest:
    """
    Cancel a pending approval request.

    Only the requester can cancel their own requests.
    """
    add_span_attribute("approval.id", approval_id)

    # TODO: Implement cancellation
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Approval request {approval_id} not found"
    )


# Approval Policies

@router.get(
    "/policies",
    response_model=List[ApprovalPolicy],
    summary="List approval policies",
    description="Returns all approval policies"
)
@traced("approvals.policies.list")
async def list_policies(
    db: DbSession,
    user: CurrentUser,
    approval_type: Optional[ApprovalType] = Query(default=None, alias="type"),
    active_only: bool = Query(default=True),
) -> List[ApprovalPolicy]:
    """
    List approval policies.
    """
    # TODO: Fetch from database
    return []


@router.get(
    "/policies/{policy_id}",
    response_model=ApprovalPolicy,
    summary="Get approval policy",
    description="Returns a specific approval policy"
)
@traced("approvals.policies.get")
async def get_policy(
    policy_id: str,
    db: DbSession,
    user: CurrentUser,
) -> ApprovalPolicy:
    """
    Get a specific approval policy.
    """
    add_span_attribute("policy.id", policy_id)

    # TODO: Fetch from database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Approval policy {policy_id} not found"
    )
