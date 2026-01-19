"""
Orchestrator Workflow using LangGraph

Main LangGraph workflow for the orchestrator that defines the
high-level engagement flow and integrates human-in-the-loop checkpoints.
"""
from typing import Any, Annotated, Dict, List, Optional, Set, Sequence
from datetime import datetime
from enum import Enum
import uuid
import operator

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.state_management import Message, Decision
from agent_framework.graph_builder import WorkflowBuilder
from agents.orchestrator.phase_manager import (
    EngagementPhase,
    PhaseManager,
    PHASE_REQUIREMENTS
)
from agents.orchestrator.router import (
    TaskRouter,
    TaskType,
    TaskPriority,
    AgentCluster,
    Task
)


class WorkflowStep(str, Enum):
    """Steps in the orchestrator workflow."""
    # Entry and initialization
    INITIALIZE = "initialize"

    # Discovery phase steps
    RUN_STAKEHOLDER_ANALYSIS = "run_stakeholder_analysis"
    RUN_SOURCE_DISCOVERY = "run_source_discovery"
    REVIEW_DISCOVERY_OUTPUTS = "review_discovery_outputs"
    DISCOVERY_APPROVAL = "discovery_approval"

    # Design phase steps
    RUN_ONTOLOGY_DESIGN = "run_ontology_design"
    RUN_SCHEMA_VALIDATION = "run_schema_validation"
    REVIEW_DESIGN_OUTPUTS = "review_design_outputs"
    DESIGN_APPROVAL = "design_approval"

    # Build phase steps
    RUN_DATA_TRANSFORMATION = "run_data_transformation"
    RUN_UI_GENERATION = "run_ui_generation"
    RUN_WORKFLOW_AUTOMATION = "run_workflow_automation"
    REVIEW_BUILD_OUTPUTS = "review_build_outputs"
    BUILD_APPROVAL = "build_approval"

    # Deploy phase steps
    RUN_DEPLOYMENT_CONFIG = "run_deployment_config"
    RUN_INTEGRATION_SETUP = "run_integration_setup"
    REVIEW_DEPLOYMENT = "review_deployment"
    DEPLOYMENT_APPROVAL = "deployment_approval"

    # Completion
    FINALIZE = "finalize"

    # Special states
    AWAIT_HUMAN_INPUT = "await_human_input"
    HANDLE_ERROR = "handle_error"


class OrchestratorState(Dict):
    """
    State for the orchestrator workflow.

    Uses TypedDict-style annotations for LangGraph compatibility.
    """
    # Engagement identification
    engagement_id: str
    customer_name: str

    # Current workflow state
    current_step: WorkflowStep
    current_phase: EngagementPhase

    # Phase management
    phase_outputs: Annotated[Dict[str, Dict[str, Any]], lambda x, y: {**x, **y}]
    phase_history: Annotated[List[Dict[str, Any]], operator.add]

    # Task tracking
    pending_tasks: List[str]
    completed_tasks: Annotated[Set[str], lambda x, y: x | y]
    failed_tasks: Annotated[List[Dict[str, Any]], operator.add]

    # Agent outputs accumulator
    agent_outputs: Annotated[Dict[str, Any], lambda x, y: {**x, **y}]

    # Decisions made during workflow
    decisions: Annotated[List[Decision], operator.add]

    # Human interaction
    requires_human_input: bool
    human_input_request: Optional[Dict[str, Any]]
    human_inputs: Annotated[List[Dict[str, Any]], operator.add]

    # Approval tracking
    pending_approvals: Dict[str, Dict[str, Any]]
    approval_history: Annotated[List[Dict[str, Any]], operator.add]

    # Quality gates
    quality_gates_status: Dict[str, Dict[str, bool]]

    # Error handling
    errors: Annotated[List[str], operator.add]
    recoverable: bool

    # Workflow metadata
    started_at: datetime
    updated_at: datetime
    checkpoints: Annotated[List[Dict[str, Any]], operator.add]


def create_initial_orchestrator_state(
    engagement_id: str,
    customer_name: str,
    initial_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create initial state for orchestrator workflow."""
    return {
        "engagement_id": engagement_id,
        "customer_name": customer_name,
        "current_step": WorkflowStep.INITIALIZE.value,
        "current_phase": EngagementPhase.DISCOVERY.value,
        "phase_outputs": {},
        "phase_history": [],
        "pending_tasks": [],
        "completed_tasks": set(),
        "failed_tasks": [],
        "agent_outputs": initial_context or {},
        "decisions": [],
        "requires_human_input": False,
        "human_input_request": None,
        "human_inputs": [],
        "pending_approvals": {},
        "approval_history": [],
        "quality_gates_status": {
            phase.value: {} for phase in EngagementPhase
        },
        "errors": [],
        "recoverable": True,
        "started_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "checkpoints": []
    }


class OrchestratorWorkflow:
    """
    Main LangGraph workflow for orchestrating engagement lifecycle.

    This workflow:
    - Coordinates Discovery, Data Architect, and App Builder clusters
    - Manages phase transitions with quality gates
    - Integrates human-in-the-loop checkpoints
    - Handles errors and recovery
    """

    def __init__(
        self,
        engagement_id: str,
        phase_manager: PhaseManager,
        task_router: TaskRouter,
        memory: Optional[MemorySaver] = None
    ):
        self.engagement_id = engagement_id
        self.phase_manager = phase_manager
        self.task_router = task_router
        self.memory = memory or MemorySaver()
        self._graph: Optional[StateGraph] = None
        self._compiled = None

    def build(self) -> StateGraph:
        """Build the orchestrator workflow graph."""
        if self._graph is not None:
            return self._graph

        # Create workflow builder
        # Note: We use a dict-based state for flexibility
        workflow = StateGraph(dict)

        # -------------------------------------------------------------------------
        # Node Definitions
        # -------------------------------------------------------------------------

        async def initialize(state: Dict[str, Any]) -> Dict[str, Any]:
            """Initialize the engagement workflow."""
            return {
                "current_step": WorkflowStep.RUN_STAKEHOLDER_ANALYSIS.value,
                "updated_at": datetime.utcnow(),
                "checkpoints": [{
                    "checkpoint_id": f"init_{uuid.uuid4().hex[:8]}",
                    "name": "workflow_initialized",
                    "phase": state.get("current_phase"),
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }

        # Discovery Phase Nodes
        async def run_stakeholder_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
            """Dispatch stakeholder analysis task to Discovery cluster."""
            task_id = f"stakeholder_{uuid.uuid4().hex[:8]}"

            await self.task_router.submit_task(
                task_id=task_id,
                task_type=TaskType.STAKEHOLDER_ANALYSIS,
                context=state.get("agent_outputs", {}),
                priority=TaskPriority.HIGH
            )

            return {
                "pending_tasks": [task_id],
                "current_step": WorkflowStep.RUN_SOURCE_DISCOVERY.value,
                "updated_at": datetime.utcnow()
            }

        async def run_source_discovery(state: Dict[str, Any]) -> Dict[str, Any]:
            """Dispatch source discovery task to Discovery cluster."""
            task_id = f"source_discovery_{uuid.uuid4().hex[:8]}"

            # This can run in parallel with stakeholder analysis completion
            await self.task_router.submit_task(
                task_id=task_id,
                task_type=TaskType.SOURCE_DISCOVERY,
                context=state.get("agent_outputs", {}),
                priority=TaskPriority.HIGH,
                dependencies=[]  # Can start independently
            )

            pending = state.get("pending_tasks", [])
            pending.append(task_id)

            return {
                "pending_tasks": pending,
                "current_step": WorkflowStep.REVIEW_DISCOVERY_OUTPUTS.value,
                "updated_at": datetime.utcnow()
            }

        async def review_discovery_outputs(state: Dict[str, Any]) -> Dict[str, Any]:
            """Review discovery outputs and prepare for approval."""
            outputs = state.get("agent_outputs", {})

            # Check if we have required outputs
            required = PHASE_REQUIREMENTS[EngagementPhase.DISCOVERY].required_outputs
            completed_outputs = set(outputs.keys())
            missing = set(required) - completed_outputs

            if missing:
                return {
                    "requires_human_input": True,
                    "human_input_request": {
                        "type": "missing_outputs",
                        "message": f"Discovery phase missing outputs: {missing}",
                        "required_outputs": list(missing),
                        "phase": EngagementPhase.DISCOVERY.value
                    },
                    "current_step": WorkflowStep.AWAIT_HUMAN_INPUT.value,
                    "updated_at": datetime.utcnow()
                }

            # Prepare approval request
            return {
                "requires_human_input": True,
                "human_input_request": {
                    "type": "phase_approval",
                    "approval_type": "discovery_sign_off",
                    "title": "Discovery Phase Review",
                    "message": "Please review discovery outputs and approve to proceed to Design phase",
                    "items_to_review": [
                        {"type": "stakeholder_map", "summary": outputs.get("stakeholder_map", {})},
                        {"type": "discovered_sources", "count": len(outputs.get("discovered_sources", []))},
                        {"type": "requirements", "count": len(outputs.get("requirements", []))}
                    ]
                },
                "current_step": WorkflowStep.DISCOVERY_APPROVAL.value,
                "updated_at": datetime.utcnow()
            }

        async def discovery_approval(state: Dict[str, Any]) -> Dict[str, Any]:
            """Handle discovery phase approval."""
            human_inputs = state.get("human_inputs", [])

            # Find approval decision
            for inp in reversed(human_inputs):
                if inp.get("type") == "approval_response":
                    if inp.get("approved"):
                        # Record phase completion
                        self.phase_manager.receive_approval(
                            "discovery_sign_off",
                            inp.get("approved_by", "unknown")
                        )

                        # Transition to design phase
                        transition = self.phase_manager.transition_to(
                            EngagementPhase.DESIGN,
                            approved_by=inp.get("approved_by"),
                            notes="Discovery phase completed"
                        )

                        return {
                            "current_phase": EngagementPhase.DESIGN.value,
                            "current_step": WorkflowStep.RUN_ONTOLOGY_DESIGN.value,
                            "phase_history": [{
                                "from_phase": EngagementPhase.DISCOVERY.value,
                                "to_phase": EngagementPhase.DESIGN.value,
                                "timestamp": datetime.utcnow().isoformat(),
                                "approved_by": inp.get("approved_by")
                            }],
                            "requires_human_input": False,
                            "human_input_request": None,
                            "approval_history": [{
                                "phase": EngagementPhase.DISCOVERY.value,
                                "approved": True,
                                "approved_by": inp.get("approved_by"),
                                "timestamp": datetime.utcnow().isoformat()
                            }],
                            "updated_at": datetime.utcnow()
                        }
                    else:
                        # Rejection - need revisions
                        return {
                            "current_step": WorkflowStep.RUN_STAKEHOLDER_ANALYSIS.value,
                            "requires_human_input": False,
                            "errors": [f"Discovery approval rejected: {inp.get('comments', 'No comments')}"],
                            "approval_history": [{
                                "phase": EngagementPhase.DISCOVERY.value,
                                "approved": False,
                                "rejected_by": inp.get("approved_by"),
                                "comments": inp.get("comments"),
                                "timestamp": datetime.utcnow().isoformat()
                            }],
                            "updated_at": datetime.utcnow()
                        }

            # Still waiting
            return {"requires_human_input": True}

        # Design Phase Nodes
        async def run_ontology_design(state: Dict[str, Any]) -> Dict[str, Any]:
            """Dispatch ontology design task to Data Architect cluster."""
            task_id = f"ontology_{uuid.uuid4().hex[:8]}"

            await self.task_router.submit_task(
                task_id=task_id,
                task_type=TaskType.ONTOLOGY_DESIGN,
                context={
                    **state.get("agent_outputs", {}),
                    "discovery_outputs": state.get("phase_outputs", {}).get("discovery", {})
                },
                priority=TaskPriority.HIGH
            )

            return {
                "pending_tasks": [task_id],
                "current_step": WorkflowStep.RUN_SCHEMA_VALIDATION.value,
                "updated_at": datetime.utcnow()
            }

        async def run_schema_validation(state: Dict[str, Any]) -> Dict[str, Any]:
            """Dispatch schema validation task."""
            task_id = f"schema_validation_{uuid.uuid4().hex[:8]}"

            # Depends on ontology design
            ontology_tasks = [
                t for t in state.get("pending_tasks", [])
                if t.startswith("ontology_")
            ]

            await self.task_router.submit_task(
                task_id=task_id,
                task_type=TaskType.SCHEMA_VALIDATION,
                context=state.get("agent_outputs", {}),
                priority=TaskPriority.HIGH,
                dependencies=ontology_tasks
            )

            pending = state.get("pending_tasks", [])
            pending.append(task_id)

            return {
                "pending_tasks": pending,
                "current_step": WorkflowStep.REVIEW_DESIGN_OUTPUTS.value,
                "updated_at": datetime.utcnow()
            }

        async def review_design_outputs(state: Dict[str, Any]) -> Dict[str, Any]:
            """Review design outputs and prepare for approval."""
            outputs = state.get("agent_outputs", {})

            return {
                "requires_human_input": True,
                "human_input_request": {
                    "type": "phase_approval",
                    "approval_type": "design_approval",
                    "title": "Design Phase Review",
                    "message": "Please review ontology and schema designs",
                    "items_to_review": [
                        {"type": "ontology_draft", "summary": outputs.get("ontology_draft", {})},
                        {"type": "schema_definitions", "summary": outputs.get("schema_definitions", {})}
                    ]
                },
                "current_step": WorkflowStep.DESIGN_APPROVAL.value,
                "updated_at": datetime.utcnow()
            }

        async def design_approval(state: Dict[str, Any]) -> Dict[str, Any]:
            """Handle design phase approval."""
            human_inputs = state.get("human_inputs", [])

            for inp in reversed(human_inputs):
                if inp.get("type") == "approval_response":
                    if inp.get("approved"):
                        self.phase_manager.receive_approval(
                            "design_approval",
                            inp.get("approved_by", "unknown")
                        )

                        self.phase_manager.transition_to(
                            EngagementPhase.BUILD,
                            approved_by=inp.get("approved_by")
                        )

                        return {
                            "current_phase": EngagementPhase.BUILD.value,
                            "current_step": WorkflowStep.RUN_DATA_TRANSFORMATION.value,
                            "phase_history": [{
                                "from_phase": EngagementPhase.DESIGN.value,
                                "to_phase": EngagementPhase.BUILD.value,
                                "timestamp": datetime.utcnow().isoformat()
                            }],
                            "requires_human_input": False,
                            "updated_at": datetime.utcnow()
                        }
                    else:
                        return {
                            "current_step": WorkflowStep.RUN_ONTOLOGY_DESIGN.value,
                            "requires_human_input": False,
                            "errors": [f"Design approval rejected: {inp.get('comments', '')}"],
                            "updated_at": datetime.utcnow()
                        }

            return {"requires_human_input": True}

        # Build Phase Nodes
        async def run_data_transformation(state: Dict[str, Any]) -> Dict[str, Any]:
            """Dispatch data transformation tasks."""
            task_id = f"transform_{uuid.uuid4().hex[:8]}"

            await self.task_router.submit_task(
                task_id=task_id,
                task_type=TaskType.DATA_TRANSFORMATION,
                context=state.get("agent_outputs", {}),
                priority=TaskPriority.HIGH
            )

            return {
                "pending_tasks": [task_id],
                "current_step": WorkflowStep.RUN_UI_GENERATION.value,
                "updated_at": datetime.utcnow()
            }

        async def run_ui_generation(state: Dict[str, Any]) -> Dict[str, Any]:
            """Dispatch UI generation tasks to App Builder cluster."""
            task_id = f"ui_{uuid.uuid4().hex[:8]}"

            await self.task_router.submit_task(
                task_id=task_id,
                task_type=TaskType.UI_GENERATION,
                context=state.get("agent_outputs", {}),
                priority=TaskPriority.NORMAL
            )

            pending = state.get("pending_tasks", [])
            pending.append(task_id)

            return {
                "pending_tasks": pending,
                "current_step": WorkflowStep.RUN_WORKFLOW_AUTOMATION.value,
                "updated_at": datetime.utcnow()
            }

        async def run_workflow_automation(state: Dict[str, Any]) -> Dict[str, Any]:
            """Dispatch workflow automation tasks."""
            task_id = f"workflow_{uuid.uuid4().hex[:8]}"

            await self.task_router.submit_task(
                task_id=task_id,
                task_type=TaskType.WORKFLOW_AUTOMATION,
                context=state.get("agent_outputs", {}),
                priority=TaskPriority.NORMAL
            )

            pending = state.get("pending_tasks", [])
            pending.append(task_id)

            return {
                "pending_tasks": pending,
                "current_step": WorkflowStep.REVIEW_BUILD_OUTPUTS.value,
                "updated_at": datetime.utcnow()
            }

        async def review_build_outputs(state: Dict[str, Any]) -> Dict[str, Any]:
            """Review build outputs and prepare for approval."""
            return {
                "requires_human_input": True,
                "human_input_request": {
                    "type": "phase_approval",
                    "approval_type": "build_approval",
                    "title": "Build Phase Review",
                    "message": "Please review built components and workflows"
                },
                "current_step": WorkflowStep.BUILD_APPROVAL.value,
                "updated_at": datetime.utcnow()
            }

        async def build_approval(state: Dict[str, Any]) -> Dict[str, Any]:
            """Handle build phase approval."""
            human_inputs = state.get("human_inputs", [])

            for inp in reversed(human_inputs):
                if inp.get("type") == "approval_response":
                    if inp.get("approved"):
                        self.phase_manager.receive_approval(
                            "build_approval",
                            inp.get("approved_by", "unknown")
                        )

                        self.phase_manager.transition_to(
                            EngagementPhase.DEPLOY,
                            approved_by=inp.get("approved_by")
                        )

                        return {
                            "current_phase": EngagementPhase.DEPLOY.value,
                            "current_step": WorkflowStep.RUN_DEPLOYMENT_CONFIG.value,
                            "requires_human_input": False,
                            "updated_at": datetime.utcnow()
                        }
                    else:
                        return {
                            "current_step": WorkflowStep.RUN_DATA_TRANSFORMATION.value,
                            "requires_human_input": False,
                            "updated_at": datetime.utcnow()
                        }

            return {"requires_human_input": True}

        # Deploy Phase Nodes
        async def run_deployment_config(state: Dict[str, Any]) -> Dict[str, Any]:
            """Dispatch deployment configuration tasks."""
            task_id = f"deploy_config_{uuid.uuid4().hex[:8]}"

            await self.task_router.submit_task(
                task_id=task_id,
                task_type=TaskType.DEPLOYMENT_CONFIG,
                context=state.get("agent_outputs", {}),
                priority=TaskPriority.HIGH
            )

            return {
                "pending_tasks": [task_id],
                "current_step": WorkflowStep.RUN_INTEGRATION_SETUP.value,
                "updated_at": datetime.utcnow()
            }

        async def run_integration_setup(state: Dict[str, Any]) -> Dict[str, Any]:
            """Dispatch integration setup tasks."""
            task_id = f"integration_{uuid.uuid4().hex[:8]}"

            await self.task_router.submit_task(
                task_id=task_id,
                task_type=TaskType.INTEGRATION_SETUP,
                context=state.get("agent_outputs", {}),
                priority=TaskPriority.HIGH
            )

            pending = state.get("pending_tasks", [])
            pending.append(task_id)

            return {
                "pending_tasks": pending,
                "current_step": WorkflowStep.REVIEW_DEPLOYMENT.value,
                "updated_at": datetime.utcnow()
            }

        async def review_deployment(state: Dict[str, Any]) -> Dict[str, Any]:
            """Review deployment and prepare for final approval."""
            return {
                "requires_human_input": True,
                "human_input_request": {
                    "type": "phase_approval",
                    "approval_type": "deployment_approval",
                    "title": "Deployment Review",
                    "message": "Please review deployment configuration and approve for production"
                },
                "current_step": WorkflowStep.DEPLOYMENT_APPROVAL.value,
                "updated_at": datetime.utcnow()
            }

        async def deployment_approval(state: Dict[str, Any]) -> Dict[str, Any]:
            """Handle deployment approval."""
            human_inputs = state.get("human_inputs", [])

            for inp in reversed(human_inputs):
                if inp.get("type") == "approval_response":
                    if inp.get("approved"):
                        self.phase_manager.receive_approval(
                            "deployment_approval",
                            inp.get("approved_by", "unknown")
                        )

                        self.phase_manager.transition_to(
                            EngagementPhase.COMPLETE,
                            approved_by=inp.get("approved_by")
                        )

                        return {
                            "current_phase": EngagementPhase.COMPLETE.value,
                            "current_step": WorkflowStep.FINALIZE.value,
                            "requires_human_input": False,
                            "updated_at": datetime.utcnow()
                        }
                    else:
                        return {
                            "current_step": WorkflowStep.RUN_DEPLOYMENT_CONFIG.value,
                            "requires_human_input": False,
                            "updated_at": datetime.utcnow()
                        }

            return {"requires_human_input": True}

        async def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
            """Finalize the engagement workflow."""
            return {
                "current_step": "complete",
                "checkpoints": [{
                    "checkpoint_id": f"final_{uuid.uuid4().hex[:8]}",
                    "name": "workflow_completed",
                    "phase": EngagementPhase.COMPLETE.value,
                    "timestamp": datetime.utcnow().isoformat()
                }],
                "updated_at": datetime.utcnow()
            }

        async def await_human_input(state: Dict[str, Any]) -> Dict[str, Any]:
            """Wait for human input."""
            # This is a checkpoint node - workflow pauses here
            return {
                "checkpoints": [{
                    "checkpoint_id": f"human_input_{uuid.uuid4().hex[:8]}",
                    "name": "awaiting_human_input",
                    "phase": state.get("current_phase"),
                    "request": state.get("human_input_request"),
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }

        async def handle_error(state: Dict[str, Any]) -> Dict[str, Any]:
            """Handle workflow errors."""
            errors = state.get("errors", [])

            return {
                "checkpoints": [{
                    "checkpoint_id": f"error_{uuid.uuid4().hex[:8]}",
                    "name": "error_checkpoint",
                    "phase": state.get("current_phase"),
                    "errors": errors,
                    "timestamp": datetime.utcnow().isoformat()
                }],
                "requires_human_input": True,
                "human_input_request": {
                    "type": "error_resolution",
                    "message": "Workflow encountered errors that require attention",
                    "errors": errors
                }
            }

        # -------------------------------------------------------------------------
        # Routing Functions
        # -------------------------------------------------------------------------

        def route_from_initialize(state: Dict[str, Any]) -> str:
            """Route after initialization based on phase."""
            phase = state.get("current_phase", EngagementPhase.DISCOVERY.value)

            if phase == EngagementPhase.DISCOVERY.value:
                return WorkflowStep.RUN_STAKEHOLDER_ANALYSIS.value
            elif phase == EngagementPhase.DESIGN.value:
                return WorkflowStep.RUN_ONTOLOGY_DESIGN.value
            elif phase == EngagementPhase.BUILD.value:
                return WorkflowStep.RUN_DATA_TRANSFORMATION.value
            elif phase == EngagementPhase.DEPLOY.value:
                return WorkflowStep.RUN_DEPLOYMENT_CONFIG.value
            else:
                return WorkflowStep.FINALIZE.value

        def route_after_approval(state: Dict[str, Any]) -> str:
            """Route based on whether we're still waiting for approval."""
            if state.get("requires_human_input"):
                return WorkflowStep.AWAIT_HUMAN_INPUT.value
            return state.get("current_step", WorkflowStep.HANDLE_ERROR.value)

        def route_from_human_input(state: Dict[str, Any]) -> str:
            """Route after receiving human input."""
            human_inputs = state.get("human_inputs", [])

            if not human_inputs:
                # Still waiting
                return WorkflowStep.AWAIT_HUMAN_INPUT.value

            # Get the step we were at before waiting
            return state.get("current_step", WorkflowStep.HANDLE_ERROR.value)

        def should_continue_or_complete(state: Dict[str, Any]) -> str:
            """Determine if workflow should continue or complete."""
            current_step = state.get("current_step")

            if current_step == "complete":
                return "END"

            errors = state.get("errors", [])
            if errors and not state.get("recoverable", True):
                return WorkflowStep.HANDLE_ERROR.value

            return current_step

        # -------------------------------------------------------------------------
        # Build Graph
        # -------------------------------------------------------------------------

        # Add all nodes
        workflow.add_node(WorkflowStep.INITIALIZE.value, initialize)

        # Discovery nodes
        workflow.add_node(WorkflowStep.RUN_STAKEHOLDER_ANALYSIS.value, run_stakeholder_analysis)
        workflow.add_node(WorkflowStep.RUN_SOURCE_DISCOVERY.value, run_source_discovery)
        workflow.add_node(WorkflowStep.REVIEW_DISCOVERY_OUTPUTS.value, review_discovery_outputs)
        workflow.add_node(WorkflowStep.DISCOVERY_APPROVAL.value, discovery_approval)

        # Design nodes
        workflow.add_node(WorkflowStep.RUN_ONTOLOGY_DESIGN.value, run_ontology_design)
        workflow.add_node(WorkflowStep.RUN_SCHEMA_VALIDATION.value, run_schema_validation)
        workflow.add_node(WorkflowStep.REVIEW_DESIGN_OUTPUTS.value, review_design_outputs)
        workflow.add_node(WorkflowStep.DESIGN_APPROVAL.value, design_approval)

        # Build nodes
        workflow.add_node(WorkflowStep.RUN_DATA_TRANSFORMATION.value, run_data_transformation)
        workflow.add_node(WorkflowStep.RUN_UI_GENERATION.value, run_ui_generation)
        workflow.add_node(WorkflowStep.RUN_WORKFLOW_AUTOMATION.value, run_workflow_automation)
        workflow.add_node(WorkflowStep.REVIEW_BUILD_OUTPUTS.value, review_build_outputs)
        workflow.add_node(WorkflowStep.BUILD_APPROVAL.value, build_approval)

        # Deploy nodes
        workflow.add_node(WorkflowStep.RUN_DEPLOYMENT_CONFIG.value, run_deployment_config)
        workflow.add_node(WorkflowStep.RUN_INTEGRATION_SETUP.value, run_integration_setup)
        workflow.add_node(WorkflowStep.REVIEW_DEPLOYMENT.value, review_deployment)
        workflow.add_node(WorkflowStep.DEPLOYMENT_APPROVAL.value, deployment_approval)

        # Terminal nodes
        workflow.add_node(WorkflowStep.FINALIZE.value, finalize)
        workflow.add_node(WorkflowStep.AWAIT_HUMAN_INPUT.value, await_human_input)
        workflow.add_node(WorkflowStep.HANDLE_ERROR.value, handle_error)

        # Set entry point
        workflow.set_entry_point(WorkflowStep.INITIALIZE.value)

        # Add edges - Discovery phase
        workflow.add_conditional_edges(
            WorkflowStep.INITIALIZE.value,
            route_from_initialize,
            {
                WorkflowStep.RUN_STAKEHOLDER_ANALYSIS.value: WorkflowStep.RUN_STAKEHOLDER_ANALYSIS.value,
                WorkflowStep.RUN_ONTOLOGY_DESIGN.value: WorkflowStep.RUN_ONTOLOGY_DESIGN.value,
                WorkflowStep.RUN_DATA_TRANSFORMATION.value: WorkflowStep.RUN_DATA_TRANSFORMATION.value,
                WorkflowStep.RUN_DEPLOYMENT_CONFIG.value: WorkflowStep.RUN_DEPLOYMENT_CONFIG.value,
                WorkflowStep.FINALIZE.value: WorkflowStep.FINALIZE.value
            }
        )

        workflow.add_edge(
            WorkflowStep.RUN_STAKEHOLDER_ANALYSIS.value,
            WorkflowStep.RUN_SOURCE_DISCOVERY.value
        )
        workflow.add_edge(
            WorkflowStep.RUN_SOURCE_DISCOVERY.value,
            WorkflowStep.REVIEW_DISCOVERY_OUTPUTS.value
        )
        workflow.add_edge(
            WorkflowStep.REVIEW_DISCOVERY_OUTPUTS.value,
            WorkflowStep.DISCOVERY_APPROVAL.value
        )

        workflow.add_conditional_edges(
            WorkflowStep.DISCOVERY_APPROVAL.value,
            route_after_approval,
            {
                WorkflowStep.AWAIT_HUMAN_INPUT.value: WorkflowStep.AWAIT_HUMAN_INPUT.value,
                WorkflowStep.RUN_ONTOLOGY_DESIGN.value: WorkflowStep.RUN_ONTOLOGY_DESIGN.value,
                WorkflowStep.RUN_STAKEHOLDER_ANALYSIS.value: WorkflowStep.RUN_STAKEHOLDER_ANALYSIS.value,
                WorkflowStep.HANDLE_ERROR.value: WorkflowStep.HANDLE_ERROR.value
            }
        )

        # Design phase edges
        workflow.add_edge(
            WorkflowStep.RUN_ONTOLOGY_DESIGN.value,
            WorkflowStep.RUN_SCHEMA_VALIDATION.value
        )
        workflow.add_edge(
            WorkflowStep.RUN_SCHEMA_VALIDATION.value,
            WorkflowStep.REVIEW_DESIGN_OUTPUTS.value
        )
        workflow.add_edge(
            WorkflowStep.REVIEW_DESIGN_OUTPUTS.value,
            WorkflowStep.DESIGN_APPROVAL.value
        )

        workflow.add_conditional_edges(
            WorkflowStep.DESIGN_APPROVAL.value,
            route_after_approval,
            {
                WorkflowStep.AWAIT_HUMAN_INPUT.value: WorkflowStep.AWAIT_HUMAN_INPUT.value,
                WorkflowStep.RUN_DATA_TRANSFORMATION.value: WorkflowStep.RUN_DATA_TRANSFORMATION.value,
                WorkflowStep.RUN_ONTOLOGY_DESIGN.value: WorkflowStep.RUN_ONTOLOGY_DESIGN.value,
                WorkflowStep.HANDLE_ERROR.value: WorkflowStep.HANDLE_ERROR.value
            }
        )

        # Build phase edges
        workflow.add_edge(
            WorkflowStep.RUN_DATA_TRANSFORMATION.value,
            WorkflowStep.RUN_UI_GENERATION.value
        )
        workflow.add_edge(
            WorkflowStep.RUN_UI_GENERATION.value,
            WorkflowStep.RUN_WORKFLOW_AUTOMATION.value
        )
        workflow.add_edge(
            WorkflowStep.RUN_WORKFLOW_AUTOMATION.value,
            WorkflowStep.REVIEW_BUILD_OUTPUTS.value
        )
        workflow.add_edge(
            WorkflowStep.REVIEW_BUILD_OUTPUTS.value,
            WorkflowStep.BUILD_APPROVAL.value
        )

        workflow.add_conditional_edges(
            WorkflowStep.BUILD_APPROVAL.value,
            route_after_approval,
            {
                WorkflowStep.AWAIT_HUMAN_INPUT.value: WorkflowStep.AWAIT_HUMAN_INPUT.value,
                WorkflowStep.RUN_DEPLOYMENT_CONFIG.value: WorkflowStep.RUN_DEPLOYMENT_CONFIG.value,
                WorkflowStep.RUN_DATA_TRANSFORMATION.value: WorkflowStep.RUN_DATA_TRANSFORMATION.value,
                WorkflowStep.HANDLE_ERROR.value: WorkflowStep.HANDLE_ERROR.value
            }
        )

        # Deploy phase edges
        workflow.add_edge(
            WorkflowStep.RUN_DEPLOYMENT_CONFIG.value,
            WorkflowStep.RUN_INTEGRATION_SETUP.value
        )
        workflow.add_edge(
            WorkflowStep.RUN_INTEGRATION_SETUP.value,
            WorkflowStep.REVIEW_DEPLOYMENT.value
        )
        workflow.add_edge(
            WorkflowStep.REVIEW_DEPLOYMENT.value,
            WorkflowStep.DEPLOYMENT_APPROVAL.value
        )

        workflow.add_conditional_edges(
            WorkflowStep.DEPLOYMENT_APPROVAL.value,
            route_after_approval,
            {
                WorkflowStep.AWAIT_HUMAN_INPUT.value: WorkflowStep.AWAIT_HUMAN_INPUT.value,
                WorkflowStep.FINALIZE.value: WorkflowStep.FINALIZE.value,
                WorkflowStep.RUN_DEPLOYMENT_CONFIG.value: WorkflowStep.RUN_DEPLOYMENT_CONFIG.value,
                WorkflowStep.HANDLE_ERROR.value: WorkflowStep.HANDLE_ERROR.value
            }
        )

        # Terminal edges
        workflow.add_edge(WorkflowStep.FINALIZE.value, END)
        workflow.add_edge(WorkflowStep.HANDLE_ERROR.value, WorkflowStep.AWAIT_HUMAN_INPUT.value)

        # Human input can route back to any approval step
        workflow.add_conditional_edges(
            WorkflowStep.AWAIT_HUMAN_INPUT.value,
            route_from_human_input,
            {
                WorkflowStep.AWAIT_HUMAN_INPUT.value: WorkflowStep.AWAIT_HUMAN_INPUT.value,
                WorkflowStep.DISCOVERY_APPROVAL.value: WorkflowStep.DISCOVERY_APPROVAL.value,
                WorkflowStep.DESIGN_APPROVAL.value: WorkflowStep.DESIGN_APPROVAL.value,
                WorkflowStep.BUILD_APPROVAL.value: WorkflowStep.BUILD_APPROVAL.value,
                WorkflowStep.DEPLOYMENT_APPROVAL.value: WorkflowStep.DEPLOYMENT_APPROVAL.value,
                WorkflowStep.HANDLE_ERROR.value: WorkflowStep.HANDLE_ERROR.value
            }
        )

        self._graph = workflow
        return workflow

    def compile(self):
        """Compile the workflow for execution."""
        if self._compiled is None:
            graph = self.build()
            self._compiled = graph.compile(checkpointer=self.memory)
        return self._compiled

    async def start(
        self,
        customer_name: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start the orchestrator workflow.

        Args:
            customer_name: Name of the customer/engagement
            initial_context: Initial context data

        Returns:
            Initial state after starting
        """
        initial_state = create_initial_orchestrator_state(
            engagement_id=self.engagement_id,
            customer_name=customer_name,
            initial_context=initial_context
        )

        compiled = self.compile()
        config = {"configurable": {"thread_id": self.engagement_id}}

        result = await compiled.ainvoke(initial_state, config)
        return result

    async def resume(
        self,
        human_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resume workflow with human input.

        Args:
            human_input: Human input/approval data

        Returns:
            Updated state after processing input
        """
        compiled = self.compile()
        config = {"configurable": {"thread_id": self.engagement_id}}

        # Get current state
        state = await compiled.aget_state(config)
        current_values = state.values

        # Add human input
        human_inputs = current_values.get("human_inputs", [])
        human_inputs.append({
            **human_input,
            "received_at": datetime.utcnow().isoformat()
        })

        # Update and resume
        update = {
            "human_inputs": human_inputs,
            "requires_human_input": False
        }

        result = await compiled.ainvoke(update, config)
        return result

    async def get_state(self) -> Dict[str, Any]:
        """Get current workflow state."""
        compiled = self.compile()
        config = {"configurable": {"thread_id": self.engagement_id}}
        state = await compiled.aget_state(config)
        return state.values

    def get_workflow_summary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the current workflow state."""
        return {
            "engagement_id": state.get("engagement_id"),
            "customer_name": state.get("customer_name"),
            "current_phase": state.get("current_phase"),
            "current_step": state.get("current_step"),
            "requires_human_input": state.get("requires_human_input"),
            "human_input_request": state.get("human_input_request"),
            "pending_tasks": len(state.get("pending_tasks", [])),
            "completed_tasks": len(state.get("completed_tasks", set())),
            "errors": state.get("errors", []),
            "phase_summary": self.phase_manager.get_phase_summary()
        }
