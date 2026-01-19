"""
Main Orchestrator Agent

Coordinates work across Discovery, Data Architect, and App Builder clusters.
Manages engagement lifecycle phases and routes tasks to appropriate agents.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
import uuid

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from contracts.agent_interface import AgentInput, AgentOutput
from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
from agent_framework.state_management import (
    AgentState,
    Decision,
    add_decision,
    mark_for_review,
    create_initial_state
)
from agent_framework.graph_builder import WorkflowBuilder
from agent_framework.prompts import PromptTemplate, PromptLibrary, build_context_string

from core.messaging.events import EventBus
from agents.orchestrator.phase_manager import (
    EngagementPhase,
    PhaseManager,
    PhaseRequirements,
    PHASE_REQUIREMENTS,
    VALID_TRANSITIONS
)
from agents.orchestrator.router import (
    TaskRouter,
    TaskType,
    TaskPriority,
    AgentCluster,
    Task
)
from agents.orchestrator.events import (
    OrchestratorEventHandler,
    OrchestratorEventType,
    EventDrivenOrchestration
)
from agents.orchestrator.workflow import (
    OrchestratorWorkflow,
    WorkflowStep,
    create_initial_orchestrator_state
)


# Orchestrator-specific prompts
ORCHESTRATOR_SYSTEM_PROMPT = PromptTemplate("""You are the Main Orchestrator Agent for Open Forge.

Your role is to coordinate work across three specialist agent clusters:
1. Discovery Cluster - Stakeholder analysis, requirements gathering, source discovery
2. Data Architect Cluster - Ontology design, schema validation, data transformation
3. App Builder Cluster - UI generation, workflow automation, deployment

Engagement ID: $engagement_id
Current Phase: $phase

Your responsibilities:
- Route tasks to appropriate specialist agents based on phase and task type
- Manage engagement lifecycle from Discovery through Deployment
- Enforce quality gates between phases
- Handle human-in-the-loop checkpoints for approvals
- Coordinate parallel work streams when possible
- Ensure phase completion criteria are met before transitions

Current Phase Requirements:
$phase_requirements

Available Transitions:
$available_transitions

Active Tasks:
$active_tasks

Quality Gate Status:
$quality_gates

Guidelines:
- Always validate phase requirements before transitions
- Prioritize tasks that unblock other work
- Request human approval at phase boundaries
- Track and report progress transparently
- Handle errors gracefully with recovery options
""")

TASK_ROUTING_PROMPT = PromptTemplate("""Determine how to route the following task.

Task Description: $task_description
Task Context: $task_context
Current Phase: $current_phase
Available Clusters: Discovery, Data Architect, App Builder

Consider:
1. Which cluster has the expertise for this task?
2. What is the appropriate priority given the current phase?
3. Are there dependencies on other tasks?
4. Should this run in parallel with other work?

Provide routing decision as JSON:
{
    "target_cluster": "discovery|data_architect|app_builder",
    "task_type": "<specific task type>",
    "priority": "critical|high|normal|low|background",
    "dependencies": ["<task_id1>", ...],
    "reasoning": "<why this routing decision>"
}
""")

PHASE_TRANSITION_PROMPT = PromptTemplate("""Evaluate readiness for phase transition.

Current Phase: $current_phase
Target Phase: $target_phase

Phase Requirements:
$requirements

Current Status:
- Completed Outputs: $completed_outputs
- Passed Quality Gates: $passed_gates
- Received Approvals: $approvals

Missing Items:
- Outputs: $missing_outputs
- Quality Gates: $missing_gates
- Approvals: $missing_approvals

Evaluate whether transition should proceed and provide recommendation:
{
    "ready": true|false,
    "confidence": 0.0-1.0,
    "recommendation": "proceed|wait|escalate",
    "reasoning": "<detailed reasoning>",
    "blockers": ["<blocker1>", ...],
    "risks": ["<risk1>", ...]
}
""")


class OrchestratorState(AgentState):
    """Extended state for orchestrator agent."""
    # Workflow state
    workflow_step: str
    engagement_phase: str

    # Cluster coordination
    active_clusters: List[str]
    cluster_status: Dict[str, Any]

    # Task management
    pending_tasks: List[str]
    completed_tasks: List[str]
    task_results: Dict[str, Any]

    # Phase tracking
    phase_outputs: Dict[str, Any]
    quality_gates: Dict[str, bool]

    # Human interaction
    pending_approvals: Dict[str, Any]
    approval_history: List[Dict[str, Any]]


class MainOrchestrator(BaseOpenForgeAgent):
    """
    Main Orchestrator Agent for Open Forge.

    Coordinates all specialist agent clusters and manages the
    engagement lifecycle through discovery, design, build, and deploy phases.

    This agent:
    - Routes tasks to Discovery, Data Architect, and App Builder clusters
    - Manages phase transitions with quality gates
    - Integrates human-in-the-loop checkpoints
    - Tracks engagement progress across all clusters
    - Handles errors and recovery
    """

    def __init__(
        self,
        llm: BaseChatModel,
        event_bus: Optional[EventBus] = None,
        memory: Optional[MemorySaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(llm, memory, config)

        # Event bus for coordination
        self.event_bus = event_bus

        # These are initialized per-engagement
        self._phase_manager: Optional[PhaseManager] = None
        self._task_router: Optional[TaskRouter] = None
        self._event_handler: Optional[OrchestratorEventHandler] = None
        self._workflow: Optional[OrchestratorWorkflow] = None

        # Register prompts
        self._register_prompts()

    def _register_prompts(self) -> None:
        """Register orchestrator-specific prompts."""
        PromptLibrary.register("orchestrator_system_prompt", ORCHESTRATOR_SYSTEM_PROMPT)
        PromptLibrary.register("task_routing_prompt", TASK_ROUTING_PROMPT)
        PromptLibrary.register("phase_transition_prompt", PHASE_TRANSITION_PROMPT)

    @property
    def name(self) -> str:
        return "main_orchestrator"

    @property
    def description(self) -> str:
        return (
            "Main orchestrator that coordinates Discovery, Data Architect, and "
            "App Builder agent clusters throughout the engagement lifecycle."
        )

    @property
    def required_inputs(self) -> List[str]:
        return ["customer_name"]  # Minimal required input to start

    @property
    def output_keys(self) -> List[str]:
        return [
            "engagement_id",
            "current_phase",
            "phase_status",
            "task_summary",
            "workflow_status",
            "next_actions"
        ]

    @property
    def state_class(self) -> Type[OrchestratorState]:
        return OrchestratorState

    def get_system_prompt(self) -> str:
        """Get the system prompt for the orchestrator."""
        return ORCHESTRATOR_SYSTEM_PROMPT.template

    async def initialize_engagement(
        self,
        engagement_id: str,
        customer_name: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize a new engagement.

        Args:
            engagement_id: Unique identifier for the engagement
            customer_name: Name of the customer
            initial_context: Optional initial context data

        Returns:
            Initialization result with engagement details
        """
        # Create phase manager
        self._phase_manager = PhaseManager(engagement_id)

        # Create task router
        self._task_router = TaskRouter(engagement_id)

        # Register default agents for each cluster
        self._register_default_agents()

        # Create event handler if event bus available
        if self.event_bus:
            self._event_handler = OrchestratorEventHandler(
                self.event_bus,
                engagement_id
            )
            await self._event_handler.setup()

            # Publish engagement created event
            await self._event_handler.publish_engagement_created(
                customer_name=customer_name,
                created_by="main_orchestrator",
                initial_context=initial_context
            )

        # Create workflow
        self._workflow = OrchestratorWorkflow(
            engagement_id=engagement_id,
            phase_manager=self._phase_manager,
            task_router=self._task_router,
            memory=self.memory
        )

        return {
            "engagement_id": engagement_id,
            "customer_name": customer_name,
            "current_phase": self._phase_manager.get_current_phase().value,
            "status": "initialized",
            "message": f"Engagement {engagement_id} initialized successfully"
        }

    def _register_default_agents(self) -> None:
        """Register default agents for each cluster."""
        # Discovery cluster agents
        self._task_router.register_agent(
            "stakeholder_agent",
            AgentCluster.DISCOVERY,
            {TaskType.STAKEHOLDER_ANALYSIS, TaskType.REQUIREMENTS_GATHERING}
        )
        self._task_router.register_agent(
            "source_discovery_agent",
            AgentCluster.DISCOVERY,
            {TaskType.SOURCE_DISCOVERY}
        )

        # Data Architect cluster agents
        self._task_router.register_agent(
            "ontology_designer_agent",
            AgentCluster.DATA_ARCHITECT,
            {TaskType.ONTOLOGY_DESIGN}
        )
        self._task_router.register_agent(
            "schema_validator_agent",
            AgentCluster.DATA_ARCHITECT,
            {TaskType.SCHEMA_VALIDATION}
        )
        self._task_router.register_agent(
            "transformation_agent",
            AgentCluster.DATA_ARCHITECT,
            {TaskType.DATA_TRANSFORMATION}
        )

        # App Builder cluster agents
        self._task_router.register_agent(
            "ui_generator_agent",
            AgentCluster.APP_BUILDER,
            {TaskType.UI_GENERATION}
        )
        self._task_router.register_agent(
            "workflow_automation_agent",
            AgentCluster.APP_BUILDER,
            {TaskType.WORKFLOW_AUTOMATION}
        )
        self._task_router.register_agent(
            "deployment_agent",
            AgentCluster.APP_BUILDER,
            {TaskType.DEPLOYMENT_CONFIG, TaskType.INTEGRATION_SETUP}
        )

    async def route_task(
        self,
        task_description: str,
        task_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route a task to the appropriate cluster using LLM reasoning.

        Args:
            task_description: Description of the task
            task_context: Additional context for the task

        Returns:
            Routing decision with task details
        """
        if not self._phase_manager or not self._task_router:
            raise RuntimeError("Orchestrator not initialized. Call initialize_engagement first.")

        current_phase = self._phase_manager.get_current_phase()

        # Use LLM to determine routing
        prompt = PromptLibrary.format(
            "task_routing_prompt",
            task_description=task_description,
            task_context=build_context_string(task_context or {}),
            current_phase=current_phase.value
        )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt)
        ]

        response = await self.llm.ainvoke(messages)

        # Parse routing decision
        import json
        try:
            routing = json.loads(response.content)
        except json.JSONDecodeError:
            # Default routing based on phase
            routing = self._get_default_routing(current_phase, task_description)

        # Create and submit task
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_type = self._map_task_type(routing.get("task_type", ""))
        priority = self._map_priority(routing.get("priority", "normal"))

        task = await self._task_router.submit_task(
            task_id=task_id,
            task_type=task_type,
            context=task_context,
            priority=priority,
            dependencies=routing.get("dependencies", [])
        )

        # Publish event
        if self._event_handler:
            await self._event_handler.publish_task_routed(
                task_id=task_id,
                task_type=task_type.value,
                target_cluster=task.assigned_cluster.value if task.assigned_cluster else "unknown",
                priority=priority.name.lower()
            )

        return {
            "task_id": task_id,
            "task_type": task_type.value,
            "cluster": task.assigned_cluster.value if task.assigned_cluster else None,
            "priority": priority.name.lower(),
            "status": task.status.value,
            "routing_reasoning": routing.get("reasoning", "")
        }

    def _get_default_routing(
        self,
        phase: EngagementPhase,
        task_description: str
    ) -> Dict[str, Any]:
        """Get default routing based on phase."""
        phase_clusters = {
            EngagementPhase.DISCOVERY: ("discovery", "stakeholder_analysis"),
            EngagementPhase.DESIGN: ("data_architect", "ontology_design"),
            EngagementPhase.BUILD: ("app_builder", "ui_generation"),
            EngagementPhase.DEPLOY: ("app_builder", "deployment_config"),
        }

        cluster, task_type = phase_clusters.get(
            phase,
            ("discovery", "stakeholder_analysis")
        )

        return {
            "target_cluster": cluster,
            "task_type": task_type,
            "priority": "normal",
            "dependencies": [],
            "reasoning": f"Default routing for {phase.value} phase"
        }

    def _map_task_type(self, task_type_str: str) -> TaskType:
        """Map string task type to TaskType enum."""
        mapping = {
            "stakeholder_analysis": TaskType.STAKEHOLDER_ANALYSIS,
            "source_discovery": TaskType.SOURCE_DISCOVERY,
            "requirements_gathering": TaskType.REQUIREMENTS_GATHERING,
            "ontology_design": TaskType.ONTOLOGY_DESIGN,
            "schema_validation": TaskType.SCHEMA_VALIDATION,
            "data_transformation": TaskType.DATA_TRANSFORMATION,
            "ui_generation": TaskType.UI_GENERATION,
            "workflow_automation": TaskType.WORKFLOW_AUTOMATION,
            "integration_setup": TaskType.INTEGRATION_SETUP,
            "deployment_config": TaskType.DEPLOYMENT_CONFIG,
        }
        return mapping.get(task_type_str.lower(), TaskType.STAKEHOLDER_ANALYSIS)

    def _map_priority(self, priority_str: str) -> TaskPriority:
        """Map string priority to TaskPriority enum."""
        mapping = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "normal": TaskPriority.NORMAL,
            "low": TaskPriority.LOW,
            "background": TaskPriority.BACKGROUND,
        }
        return mapping.get(priority_str.lower(), TaskPriority.NORMAL)

    async def check_phase_transition(
        self,
        target_phase: EngagementPhase
    ) -> Dict[str, Any]:
        """
        Check readiness for phase transition using LLM evaluation.

        Args:
            target_phase: The phase to transition to

        Returns:
            Evaluation result with recommendation
        """
        if not self._phase_manager:
            raise RuntimeError("Orchestrator not initialized.")

        current_phase = self._phase_manager.get_current_phase()
        validation = self._phase_manager.validate_transition(target_phase)
        remaining = self._phase_manager.get_remaining_work()
        status = self._phase_manager.get_phase_status()

        # Use LLM for nuanced evaluation
        requirements = PHASE_REQUIREMENTS[current_phase]

        prompt = PromptLibrary.format(
            "phase_transition_prompt",
            current_phase=current_phase.value,
            target_phase=target_phase.value,
            requirements=str(requirements.model_dump()),
            completed_outputs=list(status.outputs_completed),
            passed_gates=list(status.gates_passed),
            approvals=list(status.approvals_received),
            missing_outputs=remaining.get("remaining_outputs", []),
            missing_gates=remaining.get("remaining_gates", []),
            missing_approvals=remaining.get("remaining_approvals", [])
        )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt)
        ]

        response = await self.llm.ainvoke(messages)

        import json
        try:
            evaluation = json.loads(response.content)
        except json.JSONDecodeError:
            evaluation = {
                "ready": validation["valid"],
                "confidence": 0.5,
                "recommendation": "proceed" if validation["valid"] else "wait",
                "reasoning": "Based on validation rules"
            }

        return {
            "current_phase": current_phase.value,
            "target_phase": target_phase.value,
            "validation": validation,
            "evaluation": evaluation,
            "remaining_work": remaining
        }

    async def transition_phase(
        self,
        target_phase: EngagementPhase,
        approved_by: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Transition to a new phase.

        Args:
            target_phase: The phase to transition to
            approved_by: Who is approving the transition
            force: Force transition even if requirements not met

        Returns:
            Transition result
        """
        if not self._phase_manager:
            raise RuntimeError("Orchestrator not initialized.")

        previous_phase = self._phase_manager.get_current_phase()

        result = self._phase_manager.transition_to(
            target_phase,
            approved_by=approved_by,
            force=force
        )

        if result["success"] and self._event_handler:
            await self._event_handler.publish_phase_changed(
                previous_phase=previous_phase,
                new_phase=target_phase,
                changed_by=approved_by,
                notes=f"Transitioned from {previous_phase.value} to {target_phase.value}"
            )

        return result

    async def record_agent_output(
        self,
        agent_name: str,
        output_key: str,
        output_value: Any,
        phase: Optional[EngagementPhase] = None
    ) -> None:
        """
        Record output from a specialist agent.

        Args:
            agent_name: Name of the agent that produced the output
            output_key: Key for the output
            output_value: The output value
            phase: Phase to record output for (defaults to current)
        """
        if not self._phase_manager:
            raise RuntimeError("Orchestrator not initialized.")

        self._phase_manager.record_output(output_key, phase)

    async def pass_quality_gate(
        self,
        gate_id: str,
        validator: str,
        evidence: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Mark a quality gate as passed.

        Args:
            gate_id: ID of the quality gate
            validator: Who validated the gate
            evidence: Evidence supporting the validation

        Returns:
            Updated gate status
        """
        if not self._phase_manager:
            raise RuntimeError("Orchestrator not initialized.")

        phase = self._phase_manager.get_current_phase()
        success = self._phase_manager.pass_quality_gate(
            gate_id,
            evidence=evidence,
            validator=validator
        )

        if success and self._event_handler:
            requirements = PHASE_REQUIREMENTS[phase]
            gate = next(
                (g for g in requirements.quality_gates if g.gate_id == gate_id),
                None
            )
            if gate:
                await self._event_handler.publish_quality_gate_passed(
                    phase=phase,
                    gate_id=gate_id,
                    gate_name=gate.name,
                    validator=validator,
                    evidence=evidence
                )

        return {
            "gate_id": gate_id,
            "passed": success,
            "validator": validator,
            "phase": phase.value
        }

    async def request_approval(
        self,
        approval_type: str,
        title: str,
        description: Optional[str] = None,
        items_to_review: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Request approval for phase transition or major decision.

        Args:
            approval_type: Type of approval needed
            title: Title of the approval request
            description: Detailed description
            items_to_review: Items that need review

        Returns:
            Approval ID
        """
        if not self._event_handler:
            raise RuntimeError("Event handler not initialized.")

        approval_id = await self._event_handler.publish_approval_requested(
            approval_type=approval_type,
            title=title,
            description=description,
            requested_by=self.name,
            items_to_review=items_to_review
        )

        return approval_id

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        if not self._phase_manager or not self._task_router:
            return {"status": "not_initialized"}

        return {
            "phase_summary": self._phase_manager.get_phase_summary(),
            "routing_summary": self._task_router.get_routing_summary(),
            "remaining_work": self._phase_manager.get_remaining_work()
        }

    def build_graph(self) -> StateGraph:
        """Build the orchestrator's internal decision graph."""
        builder = WorkflowBuilder(OrchestratorState)

        async def analyze_request(state: OrchestratorState) -> Dict[str, Any]:
            """Analyze incoming request and determine action."""
            context = state.get("agent_context", {})
            action = context.get("action", "status")

            return {
                "current_step": f"processing_{action}",
                "outputs": {"action_type": action}
            }

        async def route_action(state: OrchestratorState) -> str:
            """Route to appropriate handler based on action."""
            outputs = state.get("outputs", {})
            action = outputs.get("action_type", "status")

            action_map = {
                "status": "get_status",
                "route_task": "route_task",
                "check_transition": "check_transition",
                "transition": "transition_phase",
            }

            return action_map.get(action, "get_status")

        async def get_status_node(state: OrchestratorState) -> Dict[str, Any]:
            """Get current status."""
            status = self.get_status()
            return {
                "outputs": {"status": status},
                "current_step": "complete"
            }

        async def route_task_node(state: OrchestratorState) -> Dict[str, Any]:
            """Route a task."""
            context = state.get("agent_context", {})
            task_desc = context.get("task_description", "")
            task_ctx = context.get("task_context", {})

            result = await self.route_task(task_desc, task_ctx)
            return {
                "outputs": {"routing_result": result},
                "current_step": "complete"
            }

        async def check_transition_node(state: OrchestratorState) -> Dict[str, Any]:
            """Check phase transition readiness."""
            context = state.get("agent_context", {})
            target = context.get("target_phase", "design")
            target_phase = EngagementPhase(target)

            result = await self.check_phase_transition(target_phase)
            return {
                "outputs": {"transition_check": result},
                "current_step": "complete"
            }

        async def transition_phase_node(state: OrchestratorState) -> Dict[str, Any]:
            """Execute phase transition."""
            context = state.get("agent_context", {})
            target = context.get("target_phase", "design")
            approved_by = context.get("approved_by", "system")
            force = context.get("force", False)

            target_phase = EngagementPhase(target)
            result = await self.transition_phase(target_phase, approved_by, force)

            return {
                "outputs": {"transition_result": result},
                "current_step": "complete"
            }

        # Build the graph
        graph = (builder
            .add_node("analyze", analyze_request)
            .add_node("get_status", get_status_node)
            .add_node("route_task", route_task_node)
            .add_node("check_transition", check_transition_node)
            .add_node("transition_phase", transition_phase_node)
            .set_entry("analyze")
            .add_conditional("analyze", route_action, {
                "get_status": "get_status",
                "route_task": "route_task",
                "check_transition": "check_transition",
                "transition_phase": "transition_phase"
            })
            .add_edge("get_status", "END")
            .add_edge("route_task", "END")
            .add_edge("check_transition", "END")
            .add_edge("transition_phase", "END")
            .build())

        return graph

    def get_tools(self) -> List[Any]:
        """Return list of tools the orchestrator uses."""
        # The orchestrator coordinates other agents rather than using tools directly
        return []

    async def start_workflow(
        self,
        engagement_id: str,
        customer_name: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start the full orchestrator workflow.

        This is the main entry point for running a complete engagement.

        Args:
            engagement_id: Unique engagement ID
            customer_name: Customer name
            initial_context: Initial context data

        Returns:
            Workflow result
        """
        # Initialize engagement
        await self.initialize_engagement(
            engagement_id,
            customer_name,
            initial_context
        )

        # Start the workflow
        result = await self._workflow.start(
            customer_name=customer_name,
            initial_context=initial_context
        )

        return result

    async def resume_workflow(
        self,
        human_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resume workflow with human input.

        Args:
            human_input: Human input/approval data

        Returns:
            Updated workflow state
        """
        if not self._workflow:
            raise RuntimeError("Workflow not started.")

        return await self._workflow.resume(human_input)

    async def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        if not self._workflow:
            return {"status": "not_started"}

        state = await self._workflow.get_state()
        return self._workflow.get_workflow_summary(state)
