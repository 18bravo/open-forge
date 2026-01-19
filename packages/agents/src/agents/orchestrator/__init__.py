"""
Orchestrator Agent

Coordinates work across specialist agent clusters (Discovery, Data Architect,
App Builder) and manages the engagement lifecycle.
"""

from agents.orchestrator.orchestrator import (
    MainOrchestrator,
    OrchestratorState,
    ORCHESTRATOR_SYSTEM_PROMPT,
)

from agents.orchestrator.phase_manager import (
    EngagementPhase,
    PhaseManager,
    PhaseTransition,
    PhaseRequirements,
    PhaseStatus,
    QualityGate,
    PHASE_REQUIREMENTS,
    VALID_TRANSITIONS,
)

from agents.orchestrator.router import (
    TaskRouter,
    Task,
    TaskType,
    TaskPriority,
    TaskStatus,
    AgentCluster,
    AgentStatus,
    ClusterStatus,
    TASK_CLUSTER_MAPPING,
    PHASE_CLUSTER_MAPPING,
)

from agents.orchestrator.events import (
    OrchestratorEventHandler,
    OrchestratorEventType,
    EventDrivenOrchestration,
    EngagementCreatedPayload,
    PhaseChangedPayload,
    AgentStartedPayload,
    AgentCompletedPayload,
    AgentRequiresHumanPayload,
    ApprovalRequestedPayload,
    ApprovalDecidedPayload,
    TaskRoutedPayload,
    QualityGatePassedPayload,
    WorkflowCheckpointPayload,
)

from agents.orchestrator.workflow import (
    OrchestratorWorkflow,
    WorkflowStep,
    create_initial_orchestrator_state,
)


__all__ = [
    # Main orchestrator
    "MainOrchestrator",
    "OrchestratorState",
    "ORCHESTRATOR_SYSTEM_PROMPT",

    # Phase management
    "EngagementPhase",
    "PhaseManager",
    "PhaseTransition",
    "PhaseRequirements",
    "PhaseStatus",
    "QualityGate",
    "PHASE_REQUIREMENTS",
    "VALID_TRANSITIONS",

    # Task routing
    "TaskRouter",
    "Task",
    "TaskType",
    "TaskPriority",
    "TaskStatus",
    "AgentCluster",
    "AgentStatus",
    "ClusterStatus",
    "TASK_CLUSTER_MAPPING",
    "PHASE_CLUSTER_MAPPING",

    # Events
    "OrchestratorEventHandler",
    "OrchestratorEventType",
    "EventDrivenOrchestration",
    "EngagementCreatedPayload",
    "PhaseChangedPayload",
    "AgentStartedPayload",
    "AgentCompletedPayload",
    "AgentRequiresHumanPayload",
    "ApprovalRequestedPayload",
    "ApprovalDecidedPayload",
    "TaskRoutedPayload",
    "QualityGatePassedPayload",
    "WorkflowCheckpointPayload",

    # Workflow
    "OrchestratorWorkflow",
    "WorkflowStep",
    "create_initial_orchestrator_state",
]
