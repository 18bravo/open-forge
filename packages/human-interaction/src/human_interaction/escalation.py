"""
Escalation workflows with timeout-based escalation and multi-level approval chains.

Provides EscalationPolicy and EscalationManager for automatic escalation
of pending approvals and reviews.
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4
import asyncio

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Boolean
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.connection import Base, get_async_db
from core.messaging.events import EventBus

from human_interaction.approvals import ApprovalManager, ApprovalRequest, ApprovalStatus
from human_interaction.notifications import NotificationService, NotificationChannel


class EscalationTrigger(str, Enum):
    """Events that can trigger escalation."""
    TIMEOUT = "timeout"
    DEADLINE_APPROACHING = "deadline_approaching"
    MULTIPLE_REJECTIONS = "multiple_rejections"
    MANUAL = "manual"
    PRIORITY_UPGRADE = "priority_upgrade"


class EscalationAction(str, Enum):
    """Actions to take on escalation."""
    NOTIFY_NEXT_LEVEL = "notify_next_level"
    REASSIGN = "reassign"
    AUTO_APPROVE = "auto_approve"
    AUTO_REJECT = "auto_reject"
    EXTEND_DEADLINE = "extend_deadline"


class EscalationLevel(BaseModel):
    """Definition of an escalation level."""
    level_id: str
    name: str
    approvers: List[str]  # User IDs or role names
    timeout_minutes: int = 60
    notification_channels: List[NotificationChannel] = Field(
        default_factory=lambda: [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    )
    can_escalate_further: bool = True
    auto_action: Optional[EscalationAction] = None
    auto_action_delay_minutes: Optional[int] = None


class EscalationPolicyModel(Base):
    """SQLAlchemy model for escalation policies."""
    __tablename__ = "escalation_policies"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    engagement_id = Column(String(36), nullable=True, index=True)
    approval_type = Column(String(50), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    levels = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class EscalationPolicy(BaseModel):
    """
    Escalation policy defining levels and triggers.

    Example:
        policy = EscalationPolicy(
            name="Standard Approval Escalation",
            levels=[
                EscalationLevel(
                    level_id="level_1",
                    name="Team Lead",
                    approvers=["team_lead_role"],
                    timeout_minutes=60,
                ),
                EscalationLevel(
                    level_id="level_2",
                    name="Manager",
                    approvers=["manager_role"],
                    timeout_minutes=120,
                ),
                EscalationLevel(
                    level_id="level_3",
                    name="Director",
                    approvers=["director_role"],
                    timeout_minutes=240,
                    can_escalate_further=False,
                    auto_action=EscalationAction.AUTO_REJECT,
                    auto_action_delay_minutes=60,
                ),
            ],
        )
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    engagement_id: Optional[str] = None
    approval_type: Optional[str] = None
    is_default: bool = False
    levels: List[EscalationLevel]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        from_attributes = True

    def get_level(self, level_id: str) -> Optional[EscalationLevel]:
        """Get a level by ID."""
        for level in self.levels:
            if level.level_id == level_id:
                return level
        return None

    def get_next_level(self, current_level_id: str) -> Optional[EscalationLevel]:
        """Get the next escalation level."""
        found_current = False
        for level in self.levels:
            if found_current:
                return level
            if level.level_id == current_level_id:
                found_current = True
        return None

    def get_initial_level(self) -> Optional[EscalationLevel]:
        """Get the first escalation level."""
        return self.levels[0] if self.levels else None


class EscalationHistoryModel(Base):
    """SQLAlchemy model for escalation history."""
    __tablename__ = "escalation_history"

    id = Column(String(36), primary_key=True)
    approval_id = Column(String(36), nullable=False, index=True)
    policy_id = Column(String(36), nullable=False)
    from_level = Column(String(50), nullable=True)
    to_level = Column(String(50), nullable=False)
    trigger = Column(String(50), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    triggered_by = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)


class EscalationHistory(BaseModel):
    """Record of an escalation event."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    approval_id: str
    policy_id: str
    from_level: Optional[str] = None
    to_level: str
    trigger: EscalationTrigger
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    triggered_by: Optional[str] = None
    reason: Optional[str] = None

    class Config:
        from_attributes = True


class EscalationManager:
    """
    Manages escalation workflows for approvals.

    Handles:
    - Policy management
    - Timeout-based automatic escalation
    - Multi-level approval chains
    - Escalation notifications
    """

    def __init__(
        self,
        approval_manager: ApprovalManager,
        notification_service: Optional[NotificationService] = None,
        event_bus: Optional[EventBus] = None,
    ):
        """
        Initialize the EscalationManager.

        Args:
            approval_manager: ApprovalManager for approval operations.
            notification_service: Optional NotificationService for notifications.
            event_bus: Optional EventBus for publishing events.
        """
        self.approval_manager = approval_manager
        self.notification_service = notification_service
        self.event_bus = event_bus
        self._policies: Dict[str, EscalationPolicy] = {}
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._role_resolvers: Dict[str, Callable[[str], List[str]]] = {}

    def register_policy(self, policy: EscalationPolicy) -> None:
        """
        Register an escalation policy.

        Args:
            policy: The policy to register.
        """
        self._policies[policy.id] = policy

    def register_role_resolver(
        self,
        role_name: str,
        resolver: Callable[[str], List[str]]
    ) -> None:
        """
        Register a function to resolve role names to user IDs.

        Args:
            role_name: The role name to resolve.
            resolver: Function that takes engagement_id and returns user IDs.
        """
        self._role_resolvers[role_name] = resolver

    async def save_policy(
        self,
        policy: EscalationPolicy,
        session: Optional[AsyncSession] = None,
    ) -> EscalationPolicy:
        """
        Save an escalation policy to the database.

        Args:
            policy: The policy to save.
            session: Optional database session.

        Returns:
            The saved policy.
        """
        model = EscalationPolicyModel(
            id=policy.id,
            name=policy.name,
            description=policy.description,
            engagement_id=policy.engagement_id,
            approval_type=policy.approval_type,
            is_default=policy.is_default,
            levels=[level.model_dump() for level in policy.levels],
            created_at=policy.created_at,
            updated_at=datetime.utcnow(),
            is_active=policy.is_active,
        )

        async def _save(s: AsyncSession) -> None:
            await s.merge(model)
            await s.flush()

        if session:
            await _save(session)
        else:
            async with get_async_db() as session:
                await _save(session)

        self.register_policy(policy)
        return policy

    async def get_policy(
        self,
        policy_id: str,
        session: Optional[AsyncSession] = None,
    ) -> Optional[EscalationPolicy]:
        """
        Get an escalation policy by ID.

        Args:
            policy_id: The policy ID.
            session: Optional database session.

        Returns:
            The EscalationPolicy if found.
        """
        # Check in-memory cache first
        if policy_id in self._policies:
            return self._policies[policy_id]

        from sqlalchemy import select

        async def _fetch(s: AsyncSession) -> Optional[EscalationPolicy]:
            result = await s.execute(
                select(EscalationPolicyModel).where(
                    EscalationPolicyModel.id == policy_id
                )
            )
            row = result.scalar_one_or_none()
            if row:
                policy = EscalationPolicy(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    engagement_id=row.engagement_id,
                    approval_type=row.approval_type,
                    is_default=row.is_default,
                    levels=[EscalationLevel(**level) for level in row.levels],
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    is_active=row.is_active,
                )
                self._policies[policy.id] = policy
                return policy
            return None

        if session:
            return await _fetch(session)

        async with get_async_db() as session:
            return await _fetch(session)

    async def get_policy_for_approval(
        self,
        approval: ApprovalRequest,
        session: Optional[AsyncSession] = None,
    ) -> Optional[EscalationPolicy]:
        """
        Find the appropriate escalation policy for an approval.

        Args:
            approval: The approval request.
            session: Optional database session.

        Returns:
            The matching EscalationPolicy if found.
        """
        from sqlalchemy import select, or_

        async def _fetch(s: AsyncSession) -> Optional[EscalationPolicy]:
            # Look for specific policy first, then default
            query = select(EscalationPolicyModel).where(
                EscalationPolicyModel.is_active == True,
                or_(
                    EscalationPolicyModel.engagement_id == approval.engagement_id,
                    EscalationPolicyModel.approval_type == approval.approval_type.value,
                    EscalationPolicyModel.is_default == True,
                )
            ).order_by(
                # Prefer specific over default
                EscalationPolicyModel.is_default.asc()
            )

            result = await s.execute(query)
            row = result.scalars().first()

            if row:
                policy = EscalationPolicy(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    engagement_id=row.engagement_id,
                    approval_type=row.approval_type,
                    is_default=row.is_default,
                    levels=[EscalationLevel(**level) for level in row.levels],
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    is_active=row.is_active,
                )
                return policy
            return None

        if session:
            return await _fetch(session)

        async with get_async_db() as session:
            return await _fetch(session)

    async def start_escalation_monitoring(
        self,
        approval_id: str,
        policy_id: Optional[str] = None,
    ) -> bool:
        """
        Start monitoring an approval for escalation.

        Args:
            approval_id: ID of the approval to monitor.
            policy_id: Optional specific policy ID to use.

        Returns:
            True if monitoring started, False if no policy found.
        """
        approval = await self.approval_manager.get_request(approval_id)
        if not approval:
            return False

        # Get policy
        if policy_id:
            policy = await self.get_policy(policy_id)
        else:
            policy = await self.get_policy_for_approval(approval)

        if not policy:
            return False

        # Get current level
        current_level = policy.get_level(approval.escalation_level)
        if not current_level:
            current_level = policy.get_initial_level()

        if not current_level:
            return False

        # Start monitoring task
        task = asyncio.create_task(
            self._monitor_approval(approval_id, policy, current_level)
        )
        self._monitoring_tasks[approval_id] = task

        return True

    async def stop_escalation_monitoring(self, approval_id: str) -> None:
        """
        Stop monitoring an approval for escalation.

        Args:
            approval_id: ID of the approval to stop monitoring.
        """
        task = self._monitoring_tasks.pop(approval_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def escalate(
        self,
        approval_id: str,
        trigger: EscalationTrigger,
        triggered_by: Optional[str] = None,
        reason: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[ApprovalRequest]:
        """
        Escalate an approval to the next level.

        Args:
            approval_id: ID of the approval.
            trigger: What triggered the escalation.
            triggered_by: Who/what triggered escalation.
            reason: Reason for escalation.
            session: Optional database session.

        Returns:
            The updated ApprovalRequest if escalated, None otherwise.
        """
        approval = await self.approval_manager.get_request(approval_id, session)
        if not approval:
            return None

        if approval.status not in [ApprovalStatus.PENDING, ApprovalStatus.ESCALATED]:
            return None

        policy = await self.get_policy_for_approval(approval, session)
        if not policy:
            return None

        current_level = policy.get_level(approval.escalation_level)
        if current_level and not current_level.can_escalate_further:
            return None

        next_level = policy.get_next_level(approval.escalation_level)
        if not next_level:
            return None

        # Record history
        history = EscalationHistory(
            approval_id=approval_id,
            policy_id=policy.id,
            from_level=approval.escalation_level,
            to_level=next_level.level_id,
            trigger=trigger,
            triggered_by=triggered_by,
            reason=reason,
        )
        await self._persist_history(history, session)

        # Update approval
        updated = await self.approval_manager.escalate(
            approval_id,
            next_level.level_id,
            reason,
            session,
        )

        # Send notifications
        if self.notification_service:
            approvers = await self._resolve_approvers(
                next_level.approvers,
                approval.engagement_id,
            )

            await self.notification_service.notify_escalation(
                approval_id=approval_id,
                engagement_id=approval.engagement_id,
                title=approval.title,
                escalated_to=approvers,
                escalation_level=next_level.name,
                reason=reason,
                channels=next_level.notification_channels,
            )

        await self._emit_event("escalation.triggered", {
            "approval_id": approval_id,
            "from_level": approval.escalation_level,
            "to_level": next_level.level_id,
            "trigger": trigger.value,
            "triggered_by": triggered_by,
            "reason": reason,
        })

        return updated

    async def get_escalation_history(
        self,
        approval_id: str,
        session: Optional[AsyncSession] = None,
    ) -> List[EscalationHistory]:
        """
        Get escalation history for an approval.

        Args:
            approval_id: ID of the approval.
            session: Optional database session.

        Returns:
            List of EscalationHistory entries.
        """
        from sqlalchemy import select, asc

        async def _fetch(s: AsyncSession) -> List[EscalationHistory]:
            query = select(EscalationHistoryModel).where(
                EscalationHistoryModel.approval_id == approval_id
            ).order_by(asc(EscalationHistoryModel.triggered_at))

            result = await s.execute(query)
            rows = result.scalars().all()
            return [
                EscalationHistory(
                    id=row.id,
                    approval_id=row.approval_id,
                    policy_id=row.policy_id,
                    from_level=row.from_level,
                    to_level=row.to_level,
                    trigger=EscalationTrigger(row.trigger),
                    triggered_at=row.triggered_at,
                    triggered_by=row.triggered_by,
                    reason=row.reason,
                )
                for row in rows
            ]

        if session:
            return await _fetch(session)

        async with get_async_db() as session:
            return await _fetch(session)

    async def _monitor_approval(
        self,
        approval_id: str,
        policy: EscalationPolicy,
        current_level: EscalationLevel,
    ) -> None:
        """Internal task to monitor an approval for escalation."""
        try:
            # Wait for timeout
            await asyncio.sleep(current_level.timeout_minutes * 60)

            # Check if approval is still pending
            approval = await self.approval_manager.get_request(approval_id)
            if not approval or approval.status not in [ApprovalStatus.PENDING, ApprovalStatus.ESCALATED]:
                return

            # Check if can escalate further
            if current_level.can_escalate_further:
                await self.escalate(
                    approval_id,
                    EscalationTrigger.TIMEOUT,
                    triggered_by="system",
                    reason=f"No response within {current_level.timeout_minutes} minutes",
                )

                # Continue monitoring at next level
                next_level = policy.get_next_level(current_level.level_id)
                if next_level:
                    await self._monitor_approval(approval_id, policy, next_level)

            # Handle auto-action if configured
            elif current_level.auto_action:
                if current_level.auto_action_delay_minutes:
                    await asyncio.sleep(current_level.auto_action_delay_minutes * 60)

                    # Re-check status
                    approval = await self.approval_manager.get_request(approval_id)
                    if not approval or approval.status not in [ApprovalStatus.PENDING, ApprovalStatus.ESCALATED]:
                        return

                await self._execute_auto_action(
                    approval_id,
                    current_level.auto_action,
                )

        except asyncio.CancelledError:
            pass
        except Exception as e:
            import logging
            logging.error(f"Error monitoring approval {approval_id}: {e}")
        finally:
            self._monitoring_tasks.pop(approval_id, None)

    async def _execute_auto_action(
        self,
        approval_id: str,
        action: EscalationAction,
    ) -> None:
        """Execute an automatic action on an approval."""
        from human_interaction.approvals import ApprovalDecision

        if action == EscalationAction.AUTO_APPROVE:
            decision = ApprovalDecision(
                approved=True,
                decided_by="system:auto_approval",
                comments="Automatically approved due to escalation policy",
            )
            await self.approval_manager.decide(approval_id, decision)

        elif action == EscalationAction.AUTO_REJECT:
            decision = ApprovalDecision(
                approved=False,
                decided_by="system:auto_rejection",
                comments="Automatically rejected due to escalation policy timeout",
            )
            await self.approval_manager.decide(approval_id, decision)

        elif action == EscalationAction.EXTEND_DEADLINE:
            approval = await self.approval_manager.get_request(approval_id)
            if approval and approval.deadline:
                new_deadline = approval.deadline + timedelta(hours=24)
                # Would need to add update_deadline method to ApprovalManager
                pass

        await self._emit_event("escalation.auto_action", {
            "approval_id": approval_id,
            "action": action.value,
        })

    async def _resolve_approvers(
        self,
        approvers: List[str],
        engagement_id: str,
    ) -> List[str]:
        """Resolve role names to user IDs."""
        resolved: List[str] = []

        for approver in approvers:
            if approver.endswith("_role"):
                # It's a role, resolve it
                resolver = self._role_resolvers.get(approver)
                if resolver:
                    users = resolver(engagement_id)
                    resolved.extend(users)
                else:
                    # No resolver, assume it's a user ID
                    resolved.append(approver)
            else:
                # It's a user ID
                resolved.append(approver)

        return list(set(resolved))  # Remove duplicates

    async def _persist_history(
        self,
        history: EscalationHistory,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Persist escalation history to database."""
        model = EscalationHistoryModel(
            id=history.id,
            approval_id=history.approval_id,
            policy_id=history.policy_id,
            from_level=history.from_level,
            to_level=history.to_level,
            trigger=history.trigger.value,
            triggered_at=history.triggered_at,
            triggered_by=history.triggered_by,
            reason=history.reason,
        )

        async def _save(s: AsyncSession) -> None:
            s.add(model)
            await s.flush()

        if session:
            await _save(session)
        else:
            async with get_async_db() as session:
                await _save(session)

    async def _emit_event(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> None:
        """Emit an event if event bus is configured."""
        if self.event_bus:
            await self.event_bus.publish(event_type, payload)


# Pre-built policies
DEFAULT_ESCALATION_POLICY = EscalationPolicy(
    id="default_escalation_policy",
    name="Default Escalation Policy",
    description="Standard three-level escalation policy",
    is_default=True,
    levels=[
        EscalationLevel(
            level_id="level_1",
            name="Initial Reviewer",
            approvers=["reviewer_role"],
            timeout_minutes=60,
            notification_channels=[NotificationChannel.IN_APP],
        ),
        EscalationLevel(
            level_id="level_2",
            name="Team Lead",
            approvers=["team_lead_role"],
            timeout_minutes=120,
            notification_channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
        ),
        EscalationLevel(
            level_id="level_3",
            name="Manager",
            approvers=["manager_role"],
            timeout_minutes=240,
            notification_channels=[
                NotificationChannel.IN_APP,
                NotificationChannel.EMAIL,
                NotificationChannel.SLACK,
            ],
            can_escalate_further=False,
            auto_action=EscalationAction.AUTO_REJECT,
            auto_action_delay_minutes=60,
        ),
    ],
)

URGENT_ESCALATION_POLICY = EscalationPolicy(
    id="urgent_escalation_policy",
    name="Urgent Escalation Policy",
    description="Fast escalation for urgent approvals",
    levels=[
        EscalationLevel(
            level_id="level_1",
            name="On-Call Reviewer",
            approvers=["on_call_role"],
            timeout_minutes=15,
            notification_channels=[
                NotificationChannel.IN_APP,
                NotificationChannel.SLACK,
            ],
        ),
        EscalationLevel(
            level_id="level_2",
            name="Manager",
            approvers=["manager_role"],
            timeout_minutes=30,
            notification_channels=[
                NotificationChannel.IN_APP,
                NotificationChannel.EMAIL,
                NotificationChannel.SLACK,
            ],
            can_escalate_further=False,
        ),
    ],
)
