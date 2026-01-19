"""
Event Handlers for Orchestrator

Handles events from event-catalog.yaml and publishes orchestration events.
Integrates with core.messaging.events for event-driven coordination.
"""
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
import uuid
from enum import Enum
from pydantic import BaseModel, Field

from core.messaging.events import Event, EventBus
from agents.orchestrator.phase_manager import EngagementPhase, PhaseTransition


class OrchestratorEventType(str, Enum):
    """Event types published by the orchestrator."""
    # Engagement lifecycle
    ENGAGEMENT_CREATED = "engagement.created"
    ENGAGEMENT_PHASE_CHANGED = "engagement.phase_changed"

    # Agent coordination
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_REQUIRES_HUMAN = "agent.requires_human"

    # Approval workflow
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_DECIDED = "approval.decided"

    # Data events
    ONTOLOGY_COMPILED = "ontology.compiled"
    PIPELINE_EXECUTED = "pipeline.executed"

    # Orchestrator-specific events
    TASK_ROUTED = "orchestrator.task_routed"
    TASK_COMPLETED = "orchestrator.task_completed"
    QUALITY_GATE_PASSED = "orchestrator.quality_gate_passed"
    WORKFLOW_CHECKPOINT = "orchestrator.workflow_checkpoint"
    HUMAN_INPUT_REQUIRED = "orchestrator.human_input_required"
    HUMAN_INPUT_RECEIVED = "orchestrator.human_input_received"


class EngagementCreatedPayload(BaseModel):
    """Payload for engagement.created event."""
    engagement_id: str
    customer_name: str
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    initial_context: Optional[Dict[str, Any]] = None


class PhaseChangedPayload(BaseModel):
    """Payload for engagement.phase_changed event."""
    engagement_id: str
    previous_phase: str
    new_phase: str
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    changed_by: str
    transition_notes: Optional[str] = None


class AgentStartedPayload(BaseModel):
    """Payload for agent.started event."""
    engagement_id: str
    agent_name: str
    run_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    task_context: Optional[Dict[str, Any]] = None


class AgentCompletedPayload(BaseModel):
    """Payload for agent.completed event."""
    engagement_id: str
    agent_name: str
    run_id: str
    success: bool
    outputs: Dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class AgentRequiresHumanPayload(BaseModel):
    """Payload for agent.requires_human event."""
    engagement_id: str
    agent_name: str
    reason: str
    required_input: Dict[str, Any]
    deadline: Optional[datetime] = None
    priority: str = "medium"


class ApprovalRequestedPayload(BaseModel):
    """Payload for approval.requested event."""
    approval_id: str
    engagement_id: str
    approval_type: str
    title: str
    description: Optional[str] = None
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    items_to_review: List[Dict[str, Any]] = Field(default_factory=list)


class ApprovalDecidedPayload(BaseModel):
    """Payload for approval.decided event."""
    approval_id: str
    decision: str  # approved, rejected, modified
    decided_by: str
    decided_at: datetime = Field(default_factory=datetime.utcnow)
    comments: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None


class TaskRoutedPayload(BaseModel):
    """Payload for orchestrator.task_routed event."""
    engagement_id: str
    task_id: str
    task_type: str
    target_cluster: str
    target_agent: Optional[str] = None
    priority: str
    routed_at: datetime = Field(default_factory=datetime.utcnow)


class QualityGatePassedPayload(BaseModel):
    """Payload for orchestrator.quality_gate_passed event."""
    engagement_id: str
    phase: str
    gate_id: str
    gate_name: str
    passed_at: datetime = Field(default_factory=datetime.utcnow)
    validator: str
    evidence: Optional[Dict[str, Any]] = None


class WorkflowCheckpointPayload(BaseModel):
    """Payload for orchestrator.workflow_checkpoint event."""
    engagement_id: str
    checkpoint_id: str
    checkpoint_name: str
    phase: str
    state_snapshot: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    requires_resume: bool = False


class OrchestratorEventHandler:
    """
    Handles incoming events and publishes orchestration events.

    Integrates with the EventBus for event-driven coordination
    between the orchestrator and specialist agents.
    """

    def __init__(self, event_bus: EventBus, engagement_id: str):
        self.event_bus = event_bus
        self.engagement_id = engagement_id
        self._handlers: Dict[str, List[Callable]] = {}

    async def setup(self) -> None:
        """Set up event subscriptions."""
        # Subscribe to relevant events
        self.event_bus.subscribe(
            OrchestratorEventType.AGENT_COMPLETED.value,
            self._on_agent_completed
        )
        self.event_bus.subscribe(
            OrchestratorEventType.AGENT_REQUIRES_HUMAN.value,
            self._on_agent_requires_human
        )
        self.event_bus.subscribe(
            OrchestratorEventType.APPROVAL_DECIDED.value,
            self._on_approval_decided
        )
        self.event_bus.subscribe(
            OrchestratorEventType.ONTOLOGY_COMPILED.value,
            self._on_ontology_compiled
        )
        self.event_bus.subscribe(
            OrchestratorEventType.PIPELINE_EXECUTED.value,
            self._on_pipeline_executed
        )

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """Register a custom handler for an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def _invoke_handlers(self, event_type: str, event: Event) -> None:
        """Invoke registered handlers for an event type."""
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    if hasattr(handler, "__call__"):
                        import asyncio
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event)
                        else:
                            handler(event)
                except Exception as e:
                    print(f"Handler error for {event_type}: {e}")

    # -------------------------------------------------------------------------
    # Event Publishers
    # -------------------------------------------------------------------------

    async def publish_engagement_created(
        self,
        customer_name: str,
        created_by: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish engagement.created event."""
        payload = EngagementCreatedPayload(
            engagement_id=self.engagement_id,
            customer_name=customer_name,
            created_by=created_by,
            initial_context=initial_context
        )
        return await self.event_bus.publish(
            OrchestratorEventType.ENGAGEMENT_CREATED.value,
            payload.model_dump()
        )

    async def publish_phase_changed(
        self,
        previous_phase: EngagementPhase,
        new_phase: EngagementPhase,
        changed_by: str,
        notes: Optional[str] = None
    ) -> str:
        """Publish engagement.phase_changed event."""
        payload = PhaseChangedPayload(
            engagement_id=self.engagement_id,
            previous_phase=previous_phase.value,
            new_phase=new_phase.value,
            changed_by=changed_by,
            transition_notes=notes
        )
        return await self.event_bus.publish(
            OrchestratorEventType.ENGAGEMENT_PHASE_CHANGED.value,
            payload.model_dump()
        )

    async def publish_agent_started(
        self,
        agent_name: str,
        run_id: str,
        task_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish agent.started event."""
        payload = AgentStartedPayload(
            engagement_id=self.engagement_id,
            agent_name=agent_name,
            run_id=run_id,
            task_context=task_context
        )
        return await self.event_bus.publish(
            OrchestratorEventType.AGENT_STARTED.value,
            payload.model_dump()
        )

    async def publish_agent_completed(
        self,
        agent_name: str,
        run_id: str,
        success: bool,
        outputs: Dict[str, Any],
        error: Optional[str] = None
    ) -> str:
        """Publish agent.completed event."""
        payload = AgentCompletedPayload(
            engagement_id=self.engagement_id,
            agent_name=agent_name,
            run_id=run_id,
            success=success,
            outputs=outputs,
            error=error
        )
        return await self.event_bus.publish(
            OrchestratorEventType.AGENT_COMPLETED.value,
            payload.model_dump()
        )

    async def publish_agent_requires_human(
        self,
        agent_name: str,
        reason: str,
        required_input: Dict[str, Any],
        deadline: Optional[datetime] = None,
        priority: str = "medium"
    ) -> str:
        """Publish agent.requires_human event."""
        payload = AgentRequiresHumanPayload(
            engagement_id=self.engagement_id,
            agent_name=agent_name,
            reason=reason,
            required_input=required_input,
            deadline=deadline,
            priority=priority
        )
        return await self.event_bus.publish(
            OrchestratorEventType.AGENT_REQUIRES_HUMAN.value,
            payload.model_dump()
        )

    async def publish_approval_requested(
        self,
        approval_type: str,
        title: str,
        requested_by: str,
        description: Optional[str] = None,
        deadline: Optional[datetime] = None,
        items_to_review: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Publish approval.requested event."""
        approval_id = f"approval_{self.engagement_id}_{uuid.uuid4().hex[:8]}"
        payload = ApprovalRequestedPayload(
            approval_id=approval_id,
            engagement_id=self.engagement_id,
            approval_type=approval_type,
            title=title,
            description=description,
            requested_by=requested_by,
            deadline=deadline,
            items_to_review=items_to_review or []
        )
        await self.event_bus.publish(
            OrchestratorEventType.APPROVAL_REQUESTED.value,
            payload.model_dump()
        )
        return approval_id

    async def publish_approval_decided(
        self,
        approval_id: str,
        decision: str,
        decided_by: str,
        comments: Optional[str] = None,
        modifications: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish approval.decided event."""
        payload = ApprovalDecidedPayload(
            approval_id=approval_id,
            decision=decision,
            decided_by=decided_by,
            comments=comments,
            modifications=modifications
        )
        return await self.event_bus.publish(
            OrchestratorEventType.APPROVAL_DECIDED.value,
            payload.model_dump()
        )

    async def publish_task_routed(
        self,
        task_id: str,
        task_type: str,
        target_cluster: str,
        priority: str,
        target_agent: Optional[str] = None
    ) -> str:
        """Publish orchestrator.task_routed event."""
        payload = TaskRoutedPayload(
            engagement_id=self.engagement_id,
            task_id=task_id,
            task_type=task_type,
            target_cluster=target_cluster,
            target_agent=target_agent,
            priority=priority
        )
        return await self.event_bus.publish(
            OrchestratorEventType.TASK_ROUTED.value,
            payload.model_dump()
        )

    async def publish_quality_gate_passed(
        self,
        phase: EngagementPhase,
        gate_id: str,
        gate_name: str,
        validator: str,
        evidence: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish orchestrator.quality_gate_passed event."""
        payload = QualityGatePassedPayload(
            engagement_id=self.engagement_id,
            phase=phase.value,
            gate_id=gate_id,
            gate_name=gate_name,
            validator=validator,
            evidence=evidence
        )
        return await self.event_bus.publish(
            OrchestratorEventType.QUALITY_GATE_PASSED.value,
            payload.model_dump()
        )

    async def publish_workflow_checkpoint(
        self,
        checkpoint_id: str,
        checkpoint_name: str,
        phase: EngagementPhase,
        state_snapshot: Dict[str, Any],
        requires_resume: bool = False
    ) -> str:
        """Publish orchestrator.workflow_checkpoint event."""
        payload = WorkflowCheckpointPayload(
            engagement_id=self.engagement_id,
            checkpoint_id=checkpoint_id,
            checkpoint_name=checkpoint_name,
            phase=phase.value,
            state_snapshot=state_snapshot,
            requires_resume=requires_resume
        )
        return await self.event_bus.publish(
            OrchestratorEventType.WORKFLOW_CHECKPOINT.value,
            payload.model_dump()
        )

    # -------------------------------------------------------------------------
    # Event Handlers
    # -------------------------------------------------------------------------

    async def _on_agent_completed(self, event: Event) -> None:
        """Handle agent.completed events."""
        payload = event.payload

        # Only handle events for this engagement
        if payload.get("engagement_id") != self.engagement_id:
            return

        # Invoke registered handlers
        await self._invoke_handlers(
            OrchestratorEventType.AGENT_COMPLETED.value,
            event
        )

    async def _on_agent_requires_human(self, event: Event) -> None:
        """Handle agent.requires_human events."""
        payload = event.payload

        if payload.get("engagement_id") != self.engagement_id:
            return

        # Invoke registered handlers
        await self._invoke_handlers(
            OrchestratorEventType.AGENT_REQUIRES_HUMAN.value,
            event
        )

    async def _on_approval_decided(self, event: Event) -> None:
        """Handle approval.decided events."""
        # Invoke registered handlers
        await self._invoke_handlers(
            OrchestratorEventType.APPROVAL_DECIDED.value,
            event
        )

    async def _on_ontology_compiled(self, event: Event) -> None:
        """Handle ontology.compiled events."""
        payload = event.payload

        if payload.get("engagement_id") != self.engagement_id:
            return

        # Invoke registered handlers
        await self._invoke_handlers(
            OrchestratorEventType.ONTOLOGY_COMPILED.value,
            event
        )

    async def _on_pipeline_executed(self, event: Event) -> None:
        """Handle pipeline.executed events."""
        payload = event.payload

        if payload.get("engagement_id") != self.engagement_id:
            return

        # Invoke registered handlers
        await self._invoke_handlers(
            OrchestratorEventType.PIPELINE_EXECUTED.value,
            event
        )


class EventDrivenOrchestration:
    """
    High-level event-driven orchestration coordination.

    Provides patterns for common orchestration scenarios:
    - Sequential agent execution
    - Parallel task coordination
    - Human-in-the-loop workflows
    - Quality gate enforcement
    """

    def __init__(
        self,
        event_handler: OrchestratorEventHandler,
        engagement_id: str
    ):
        self.event_handler = event_handler
        self.engagement_id = engagement_id
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}
        self._agent_results: Dict[str, Dict[str, Any]] = {}

    async def coordinate_sequential_agents(
        self,
        agents: List[str],
        initial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate sequential agent execution, passing outputs forward.

        Args:
            agents: List of agent names to execute in order
            initial_context: Initial context for first agent

        Returns:
            Combined results from all agents
        """
        context = initial_context.copy()
        results = {}

        for agent_name in agents:
            run_id = f"{agent_name}_{uuid.uuid4().hex[:8]}"

            # Publish start event
            await self.event_handler.publish_agent_started(
                agent_name=agent_name,
                run_id=run_id,
                task_context=context
            )

            # Execute agent (actual execution happens elsewhere)
            # This pattern assumes events will be published when complete
            results[agent_name] = {
                "run_id": run_id,
                "status": "started",
                "context": context
            }

            # Next agent gets previous outputs as context
            context = {**context, "previous_agent": agent_name}

        return results

    async def request_and_wait_approval(
        self,
        approval_type: str,
        title: str,
        requested_by: str,
        description: Optional[str] = None,
        items_to_review: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Request approval and set up waiting for decision.

        Note: Actual waiting is handled by the workflow; this sets up
        the approval request and returns immediately.

        Returns:
            Approval request details including approval_id
        """
        approval_id = await self.event_handler.publish_approval_requested(
            approval_type=approval_type,
            title=title,
            requested_by=requested_by,
            description=description,
            items_to_review=items_to_review
        )

        self._pending_approvals[approval_id] = {
            "approval_type": approval_type,
            "title": title,
            "requested_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }

        return {
            "approval_id": approval_id,
            "status": "pending"
        }

    def record_approval_decision(
        self,
        approval_id: str,
        decision: str,
        decided_by: str,
        comments: Optional[str] = None
    ) -> None:
        """Record an approval decision."""
        if approval_id in self._pending_approvals:
            self._pending_approvals[approval_id].update({
                "status": decision,
                "decided_by": decided_by,
                "decided_at": datetime.utcnow().isoformat(),
                "comments": comments
            })

    def get_pending_approvals(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending approvals."""
        return {
            k: v for k, v in self._pending_approvals.items()
            if v.get("status") == "pending"
        }

    async def create_checkpoint(
        self,
        checkpoint_name: str,
        phase: EngagementPhase,
        state_snapshot: Dict[str, Any]
    ) -> str:
        """Create a workflow checkpoint for recovery."""
        checkpoint_id = f"checkpoint_{uuid.uuid4().hex[:8]}"

        await self.event_handler.publish_workflow_checkpoint(
            checkpoint_id=checkpoint_id,
            checkpoint_name=checkpoint_name,
            phase=phase,
            state_snapshot=state_snapshot
        )

        return checkpoint_id
