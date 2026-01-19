"""
Approval system with state machine and persistence.

Provides ApprovalRequest model and ApprovalManager for managing
human approval workflows.
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
import asyncio

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.connection import Base, get_async_db
from core.messaging.events import EventBus


class ApprovalStatus(str, Enum):
    """Approval state machine states."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class ApprovalType(str, Enum):
    """Types of approval requests."""
    AGENT_ACTION = "agent_action"
    DATA_CHANGE = "data_change"
    CONFIGURATION = "configuration"
    DEPLOYMENT = "deployment"
    ACCESS_GRANT = "access_grant"


class ApprovalRequestModel(Base):
    """SQLAlchemy model for approval requests."""
    __tablename__ = "approval_requests"

    id = Column(String(36), primary_key=True)
    engagement_id = Column(String(36), nullable=False, index=True)
    approval_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        SQLEnum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
        nullable=False,
        index=True
    )
    requested_by = Column(String(255), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deadline = Column(DateTime, nullable=True)
    decided_by = Column(String(255), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decision_comments = Column(Text, nullable=True)
    context_data = Column(JSON, nullable=True)
    escalation_level = Column(String(50), default="level_1", nullable=False)


class ApprovalRequest(BaseModel):
    """Pydantic model for approval requests."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str
    approval_type: ApprovalType
    title: str
    description: Optional[str] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    decision_comments: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    escalation_level: str = "level_1"

    class Config:
        from_attributes = True


class ApprovalDecision(BaseModel):
    """Decision on an approval request."""
    approved: bool
    decided_by: str
    comments: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None


class ApprovalManager:
    """
    Manages approval workflows with state machine transitions.

    Handles creation, decisions, expiration, and escalation of
    approval requests with database persistence and event emission.
    """

    # Valid state transitions
    VALID_TRANSITIONS: Dict[ApprovalStatus, List[ApprovalStatus]] = {
        ApprovalStatus.PENDING: [
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.EXPIRED,
            ApprovalStatus.ESCALATED,
        ],
        ApprovalStatus.ESCALATED: [
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.EXPIRED,
        ],
        ApprovalStatus.APPROVED: [],
        ApprovalStatus.REJECTED: [],
        ApprovalStatus.EXPIRED: [],
    }

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize the ApprovalManager.

        Args:
            event_bus: Optional EventBus for publishing approval events.
        """
        self.event_bus = event_bus
        self._expiration_tasks: Dict[str, asyncio.Task] = {}

    async def create_request(
        self,
        engagement_id: str,
        approval_type: ApprovalType,
        title: str,
        requested_by: str,
        description: Optional[str] = None,
        deadline: Optional[datetime] = None,
        timeout_minutes: Optional[int] = None,
        context_data: Optional[Dict[str, Any]] = None,
        session: Optional[AsyncSession] = None,
    ) -> ApprovalRequest:
        """
        Create a new approval request.

        Args:
            engagement_id: ID of the associated engagement.
            approval_type: Type of approval being requested.
            title: Brief title for the approval.
            requested_by: User or agent requesting approval.
            description: Detailed description of what needs approval.
            deadline: Optional deadline for the approval.
            timeout_minutes: Minutes until auto-expiration.
            context_data: Additional context for the approver.
            session: Optional database session.

        Returns:
            The created ApprovalRequest.
        """
        if timeout_minutes and not deadline:
            deadline = datetime.utcnow() + timedelta(minutes=timeout_minutes)

        request = ApprovalRequest(
            engagement_id=engagement_id,
            approval_type=approval_type,
            title=title,
            description=description,
            requested_by=requested_by,
            deadline=deadline,
            context_data=context_data,
        )

        # Persist to database
        await self._persist_request(request, session)

        # Emit event
        await self._emit_event("approval.requested", {
            "approval_id": request.id,
            "engagement_id": request.engagement_id,
            "type": request.approval_type.value,
            "title": request.title,
            "description": request.description,
            "requested_by": request.requested_by,
            "requested_at": request.requested_at.isoformat(),
            "deadline": request.deadline.isoformat() if request.deadline else None,
        })

        # Schedule expiration if deadline is set
        if request.deadline:
            self._schedule_expiration(request)

        return request

    async def decide(
        self,
        approval_id: str,
        decision: ApprovalDecision,
        session: Optional[AsyncSession] = None,
    ) -> ApprovalRequest:
        """
        Record a decision on an approval request.

        Args:
            approval_id: ID of the approval request.
            decision: The decision being made.
            session: Optional database session.

        Returns:
            The updated ApprovalRequest.

        Raises:
            ValueError: If the approval is not in a decidable state.
        """
        request = await self.get_request(approval_id, session)
        if not request:
            raise ValueError(f"Approval request {approval_id} not found")

        new_status = ApprovalStatus.APPROVED if decision.approved else ApprovalStatus.REJECTED

        if not self._can_transition(request.status, new_status):
            raise ValueError(
                f"Cannot transition from {request.status} to {new_status}"
            )

        # Update request
        request.status = new_status
        request.decided_by = decision.decided_by
        request.decided_at = datetime.utcnow()
        request.decision_comments = decision.comments

        # Cancel expiration task
        self._cancel_expiration(approval_id)

        # Persist update
        await self._update_request(request, session)

        # Emit event
        await self._emit_event("approval.decided", {
            "approval_id": request.id,
            "decision": "approved" if decision.approved else "rejected",
            "decided_by": decision.decided_by,
            "decided_at": request.decided_at.isoformat(),
            "comments": decision.comments,
        })

        return request

    async def expire(
        self,
        approval_id: str,
        session: Optional[AsyncSession] = None,
    ) -> ApprovalRequest:
        """
        Mark an approval request as expired.

        Args:
            approval_id: ID of the approval request.
            session: Optional database session.

        Returns:
            The updated ApprovalRequest.
        """
        request = await self.get_request(approval_id, session)
        if not request:
            raise ValueError(f"Approval request {approval_id} not found")

        if not self._can_transition(request.status, ApprovalStatus.EXPIRED):
            # Already decided, ignore
            return request

        request.status = ApprovalStatus.EXPIRED

        await self._update_request(request, session)

        await self._emit_event("approval.expired", {
            "approval_id": request.id,
            "expired_at": datetime.utcnow().isoformat(),
        })

        return request

    async def escalate(
        self,
        approval_id: str,
        new_level: str,
        reason: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> ApprovalRequest:
        """
        Escalate an approval request to a higher level.

        Args:
            approval_id: ID of the approval request.
            new_level: The escalation level to move to.
            reason: Reason for escalation.
            session: Optional database session.

        Returns:
            The updated ApprovalRequest.
        """
        request = await self.get_request(approval_id, session)
        if not request:
            raise ValueError(f"Approval request {approval_id} not found")

        if not self._can_transition(request.status, ApprovalStatus.ESCALATED):
            raise ValueError(
                f"Cannot escalate from {request.status}"
            )

        previous_level = request.escalation_level
        request.status = ApprovalStatus.ESCALATED
        request.escalation_level = new_level

        await self._update_request(request, session)

        await self._emit_event("approval.escalated", {
            "approval_id": request.id,
            "previous_level": previous_level,
            "new_level": new_level,
            "reason": reason,
            "escalated_at": datetime.utcnow().isoformat(),
        })

        return request

    async def get_request(
        self,
        approval_id: str,
        session: Optional[AsyncSession] = None,
    ) -> Optional[ApprovalRequest]:
        """
        Retrieve an approval request by ID.

        Args:
            approval_id: ID of the approval request.
            session: Optional database session.

        Returns:
            The ApprovalRequest if found, None otherwise.
        """
        if session:
            return await self._fetch_request(approval_id, session)

        async with get_async_db() as session:
            return await self._fetch_request(approval_id, session)

    async def get_pending_requests(
        self,
        engagement_id: Optional[str] = None,
        approval_type: Optional[ApprovalType] = None,
        session: Optional[AsyncSession] = None,
    ) -> List[ApprovalRequest]:
        """
        Get all pending approval requests.

        Args:
            engagement_id: Optional filter by engagement.
            approval_type: Optional filter by type.
            session: Optional database session.

        Returns:
            List of pending ApprovalRequests.
        """
        from sqlalchemy import select

        async def _fetch(s: AsyncSession) -> List[ApprovalRequest]:
            query = select(ApprovalRequestModel).where(
                ApprovalRequestModel.status.in_([
                    ApprovalStatus.PENDING,
                    ApprovalStatus.ESCALATED,
                ])
            )

            if engagement_id:
                query = query.where(
                    ApprovalRequestModel.engagement_id == engagement_id
                )

            if approval_type:
                query = query.where(
                    ApprovalRequestModel.approval_type == approval_type.value
                )

            query = query.order_by(ApprovalRequestModel.requested_at.asc())

            result = await s.execute(query)
            rows = result.scalars().all()
            return [ApprovalRequest.model_validate(row) for row in rows]

        if session:
            return await _fetch(session)

        async with get_async_db() as session:
            return await _fetch(session)

    def _can_transition(
        self,
        current: ApprovalStatus,
        target: ApprovalStatus
    ) -> bool:
        """Check if a state transition is valid."""
        return target in self.VALID_TRANSITIONS.get(current, [])

    async def _persist_request(
        self,
        request: ApprovalRequest,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Persist a new approval request to the database."""
        model = ApprovalRequestModel(
            id=request.id,
            engagement_id=request.engagement_id,
            approval_type=request.approval_type.value,
            title=request.title,
            description=request.description,
            status=request.status,
            requested_by=request.requested_by,
            requested_at=request.requested_at,
            deadline=request.deadline,
            context_data=request.context_data,
            escalation_level=request.escalation_level,
        )

        async def _save(s: AsyncSession) -> None:
            s.add(model)
            await s.flush()

        if session:
            await _save(session)
        else:
            async with get_async_db() as session:
                await _save(session)

    async def _update_request(
        self,
        request: ApprovalRequest,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Update an existing approval request in the database."""
        from sqlalchemy import update

        async def _do_update(s: AsyncSession) -> None:
            await s.execute(
                update(ApprovalRequestModel)
                .where(ApprovalRequestModel.id == request.id)
                .values(
                    status=request.status,
                    decided_by=request.decided_by,
                    decided_at=request.decided_at,
                    decision_comments=request.decision_comments,
                    escalation_level=request.escalation_level,
                )
            )
            await s.flush()

        if session:
            await _do_update(session)
        else:
            async with get_async_db() as session:
                await _do_update(session)

    async def _fetch_request(
        self,
        approval_id: str,
        session: AsyncSession,
    ) -> Optional[ApprovalRequest]:
        """Fetch an approval request from the database."""
        from sqlalchemy import select

        result = await session.execute(
            select(ApprovalRequestModel).where(
                ApprovalRequestModel.id == approval_id
            )
        )
        row = result.scalar_one_or_none()
        if row:
            return ApprovalRequest.model_validate(row)
        return None

    async def _emit_event(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> None:
        """Emit an event if event bus is configured."""
        if self.event_bus:
            await self.event_bus.publish(event_type, payload)

    def _schedule_expiration(self, request: ApprovalRequest) -> None:
        """Schedule automatic expiration of an approval request."""
        if not request.deadline:
            return

        delay = (request.deadline - datetime.utcnow()).total_seconds()
        if delay <= 0:
            # Already expired
            asyncio.create_task(self.expire(request.id))
            return

        async def _expire_after_delay():
            await asyncio.sleep(delay)
            await self.expire(request.id)

        task = asyncio.create_task(_expire_after_delay())
        self._expiration_tasks[request.id] = task

    def _cancel_expiration(self, approval_id: str) -> None:
        """Cancel a scheduled expiration task."""
        task = self._expiration_tasks.pop(approval_id, None)
        if task and not task.done():
            task.cancel()


# Factory function for agent framework integration
async def create_approval_for_agent(
    manager: ApprovalManager,
    engagement_id: str,
    agent_name: str,
    action_description: str,
    context: Optional[Dict[str, Any]] = None,
    timeout_minutes: int = 60,
) -> ApprovalRequest:
    """
    Create an approval request for an agent action.

    This is a convenience function for integration with the
    agent framework's approval subgraph.

    Args:
        manager: The ApprovalManager instance.
        engagement_id: ID of the engagement.
        agent_name: Name of the requesting agent.
        action_description: Description of the action needing approval.
        context: Additional context data.
        timeout_minutes: Minutes until the request expires.

    Returns:
        The created ApprovalRequest.
    """
    return await manager.create_request(
        engagement_id=engagement_id,
        approval_type=ApprovalType.AGENT_ACTION,
        title=f"Agent Action: {agent_name}",
        description=action_description,
        requested_by=f"agent:{agent_name}",
        timeout_minutes=timeout_minutes,
        context_data=context,
    )
