"""
App Builder Cluster

Orchestrates the app builder agents to generate complete application specifications
from ontology definitions. Manages the build workflow including UI generation,
workflow design, integration configuration, and deployment setup.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from enum import Enum

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
from agent_framework.state_management import (
    AppBuilderState,
    Decision,
    Message,
    add_decision,
    mark_for_review,
    create_initial_state
)
from contracts.agent_interface import AgentInput, AgentOutput

from agents.app_builder.ui_generator_agent import UIGeneratorAgent
from agents.app_builder.workflow_agent import WorkflowDesignerAgent
from agents.app_builder.integration_agent import IntegrationAgent
from agents.app_builder.deployment_agent import DeploymentAgent


class BuildPhase(str, Enum):
    """Phases in the app building process."""
    PLANNING = "planning"
    UI_GENERATION = "ui_generation"
    WORKFLOW_DESIGN = "workflow_design"
    INTEGRATION_CONFIG = "integration_config"
    DEPLOYMENT_SETUP = "deployment_setup"
    VALIDATION = "validation"
    COMPLETE = "complete"


APP_BUILDER_CLUSTER_SYSTEM_PROMPT = """You are the App Builder Cluster Orchestrator for Open Forge, an enterprise data platform.

Your role is to coordinate the app building agents to generate complete application specifications from ontology definitions.

## Your Responsibilities:
1. Plan the app building process based on requirements
2. Coordinate UI Generator, Workflow Designer, Integration, and Deployment agents
3. Ensure consistency across all generated specifications
4. Validate the complete application specification
5. Handle errors and request human review when needed

## Build Process:
1. Planning: Analyze requirements and create build plan
2. UI Generation: Generate React/TypeScript component specifications
3. Workflow Design: Create workflow automations and approval flows
4. Integration Config: Set up API connections and authentication
5. Deployment Setup: Generate Kubernetes manifests and CI/CD pipelines
6. Validation: Verify complete specification meets requirements

## Output:
A complete application specification containing:
- UI component specifications
- Workflow definitions
- Integration configurations
- Deployment manifests
- Documentation and runbooks

## Quality Gates:
- Each phase must complete successfully before proceeding
- Critical issues require human review
- Final specification must pass validation
"""


class AppBuilderCluster(BaseOpenForgeAgent):
    """
    Orchestrator for the app builder agent cluster.

    This cluster coordinates multiple specialist agents to generate
    complete application specifications from ontology definitions,
    including UI components, workflows, integrations, and deployment configs.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        memory: Optional[MemorySaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(llm, memory, config)

        # Initialize specialist agents
        self.ui_generator = UIGeneratorAgent(llm, memory, config)
        self.workflow_designer = WorkflowDesignerAgent(llm, memory, config)
        self.integration_agent = IntegrationAgent(llm, memory, config)
        self.deployment_agent = DeploymentAgent(llm, memory, config)

    @property
    def name(self) -> str:
        return "app_builder_cluster"

    @property
    def description(self) -> str:
        return "Orchestrates app builder agents to generate complete application specifications from ontology definitions."

    @property
    def required_inputs(self) -> List[str]:
        return ["ontology_schema", "requirements"]

    @property
    def output_keys(self) -> List[str]:
        return [
            "app_specification",
            "ui_components",
            "workflows",
            "integrations",
            "deployment_config",
            "build_summary"
        ]

    @property
    def state_class(self) -> Type[AppBuilderState]:
        return AppBuilderState

    def get_system_prompt(self) -> str:
        return APP_BUILDER_CLUSTER_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools available to the cluster."""
        return []

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for app building orchestration."""
        graph = StateGraph(AppBuilderState)

        # Add nodes
        graph.add_node("plan_build", self._plan_build)
        graph.add_node("generate_ui", self._generate_ui)
        graph.add_node("design_workflows", self._design_workflows)
        graph.add_node("configure_integrations", self._configure_integrations)
        graph.add_node("setup_deployment", self._setup_deployment)
        graph.add_node("compile_specification", self._compile_specification)
        graph.add_node("validate_application", self._validate_application)
        graph.add_node("handle_review", self._handle_review)

        # Define edges
        graph.set_entry_point("plan_build")
        graph.add_conditional_edges(
            "plan_build",
            self._route_after_planning,
            {
                "generate_ui": "generate_ui",
                "review": "handle_review"
            }
        )
        graph.add_conditional_edges(
            "generate_ui",
            self._route_after_ui,
            {
                "design_workflows": "design_workflows",
                "review": "handle_review"
            }
        )
        graph.add_conditional_edges(
            "design_workflows",
            self._route_after_workflows,
            {
                "configure_integrations": "configure_integrations",
                "review": "handle_review"
            }
        )
        graph.add_conditional_edges(
            "configure_integrations",
            self._route_after_integrations,
            {
                "setup_deployment": "setup_deployment",
                "review": "handle_review"
            }
        )
        graph.add_conditional_edges(
            "setup_deployment",
            self._route_after_deployment,
            {
                "compile_specification": "compile_specification",
                "review": "handle_review"
            }
        )
        graph.add_edge("compile_specification", "validate_application")
        graph.add_conditional_edges(
            "validate_application",
            self._route_after_validation,
            {
                "complete": END,
                "refine": "generate_ui",
                "review": "handle_review"
            }
        )
        graph.add_edge("handle_review", END)

        return graph

    async def _plan_build(self, state: AppBuilderState) -> Dict[str, Any]:
        """Plan the app building process."""
        context = state.get("agent_context", {})
        ontology_schema = context.get("ontology_schema", {})
        requirements = context.get("requirements", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Analyze the following inputs and create a build plan for generating the application.

Ontology Schema:
{ontology_schema}

Requirements:
{requirements}

Create a build plan that identifies:
1. UI Components Needed:
   - Forms for each entity type
   - Tables/lists for data display
   - Dashboards for analytics
   - Detail views

2. Workflows Needed:
   - Entity lifecycle workflows
   - Approval workflows
   - Notification workflows
   - Scheduled workflows

3. Integrations Needed:
   - External API connections
   - Authentication requirements
   - Data synchronization needs
   - Webhook requirements

4. Deployment Considerations:
   - Infrastructure requirements
   - Scaling needs
   - Security requirements
   - Environment configurations

5. Risks and Dependencies:
   - Potential blockers
   - Items requiring human review
   - Complex areas needing attention

Provide a structured build plan with priorities and dependencies.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="build_planning",
            description="Created app build plan from ontology and requirements",
            confidence=0.85,
            reasoning="Analyzed ontology and requirements to identify build components"
        )

        # Extract requirements for each agent
        build_plan = {
            "ui_requirements": self._extract_ui_requirements(response.content),
            "business_rules": self._extract_business_rules(response.content),
            "integration_requirements": self._extract_integration_requirements(response.content),
            "deployment_requirements": self._extract_deployment_requirements(response.content)
        }

        return {
            "outputs": {"build_plan": response.content},
            "agent_context": {
                **context,
                **build_plan,
                "current_phase": BuildPhase.PLANNING.value
            },
            "decisions": [decision],
            "current_step": "plan_build",
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _extract_ui_requirements(self, build_plan: str) -> Dict[str, Any]:
        """Extract UI requirements from build plan."""
        return {"build_plan_section": "ui", "raw": build_plan}

    def _extract_business_rules(self, build_plan: str) -> Dict[str, Any]:
        """Extract business rules from build plan."""
        return {"build_plan_section": "workflows", "raw": build_plan}

    def _extract_integration_requirements(self, build_plan: str) -> Dict[str, Any]:
        """Extract integration requirements from build plan."""
        return {"build_plan_section": "integrations", "raw": build_plan}

    def _extract_deployment_requirements(self, build_plan: str) -> Dict[str, Any]:
        """Extract deployment requirements from build plan."""
        return {"build_plan_section": "deployment", "raw": build_plan}

    async def _generate_ui(self, state: AppBuilderState) -> Dict[str, Any]:
        """Generate UI components using the UI Generator agent."""
        context = state.get("agent_context", {})

        # Create input for UI Generator agent
        ui_input = AgentInput(
            engagement_id=state.get("engagement_id", ""),
            phase=BuildPhase.UI_GENERATION.value,
            context={
                "ontology_schema": context.get("ontology_schema", {}),
                "ui_requirements": context.get("ui_requirements", {})
            },
            previous_outputs=state.get("outputs", {})
        )

        # Run UI Generator
        ui_output = await self.ui_generator.run(ui_input)

        decision = add_decision(
            state,
            decision_type="ui_generation",
            description="Generated UI component specifications",
            confidence=ui_output.confidence,
            reasoning="UI Generator produced component specs for forms, tables, and dashboards",
            requires_approval=ui_output.requires_human_review
        )

        review_items = []
        if ui_output.requires_human_review:
            review_items.extend(ui_output.review_items or [])

        return {
            "outputs": {"ui_generation_result": ui_output.outputs},
            "ui_components": ui_output.outputs.get("component_specs", []),
            "decisions": [decision],
            "requires_human_review": ui_output.requires_human_review,
            "review_items": review_items,
            "current_step": "generate_ui",
            "agent_context": {
                **context,
                "current_phase": BuildPhase.UI_GENERATION.value
            },
            "messages": [Message(
                role="assistant",
                content=f"UI Generation completed. Success: {ui_output.success}, Confidence: {ui_output.confidence}"
            )],
            "errors": ui_output.errors or []
        }

    async def _design_workflows(self, state: AppBuilderState) -> Dict[str, Any]:
        """Design workflows using the Workflow Designer agent."""
        context = state.get("agent_context", {})

        # Create input for Workflow Designer agent
        workflow_input = AgentInput(
            engagement_id=state.get("engagement_id", ""),
            phase=BuildPhase.WORKFLOW_DESIGN.value,
            context={
                "ontology_schema": context.get("ontology_schema", {}),
                "business_rules": context.get("business_rules", {})
            },
            previous_outputs=state.get("outputs", {})
        )

        # Run Workflow Designer
        workflow_output = await self.workflow_designer.run(workflow_input)

        decision = add_decision(
            state,
            decision_type="workflow_design",
            description="Designed workflow automations",
            confidence=workflow_output.confidence,
            reasoning="Workflow Designer created approval flows, triggers, and actions",
            requires_approval=workflow_output.requires_human_review
        )

        review_items = []
        if workflow_output.requires_human_review:
            review_items.extend(workflow_output.review_items or [])

        return {
            "outputs": {"workflow_design_result": workflow_output.outputs},
            "workflows": workflow_output.outputs.get("workflow_definitions", []),
            "decisions": [decision],
            "requires_human_review": workflow_output.requires_human_review,
            "review_items": review_items,
            "current_step": "design_workflows",
            "agent_context": {
                **context,
                "current_phase": BuildPhase.WORKFLOW_DESIGN.value
            },
            "messages": [Message(
                role="assistant",
                content=f"Workflow Design completed. Success: {workflow_output.success}, Confidence: {workflow_output.confidence}"
            )],
            "errors": workflow_output.errors or []
        }

    async def _configure_integrations(self, state: AppBuilderState) -> Dict[str, Any]:
        """Configure integrations using the Integration agent."""
        context = state.get("agent_context", {})

        # Create input for Integration agent
        integration_input = AgentInput(
            engagement_id=state.get("engagement_id", ""),
            phase=BuildPhase.INTEGRATION_CONFIG.value,
            context={
                "ontology_schema": context.get("ontology_schema", {}),
                "integration_requirements": context.get("integration_requirements", {})
            },
            previous_outputs=state.get("outputs", {})
        )

        # Run Integration agent
        integration_output = await self.integration_agent.run(integration_input)

        decision = add_decision(
            state,
            decision_type="integration_configuration",
            description="Configured system integrations",
            confidence=integration_output.confidence,
            reasoning="Integration agent set up API connections and authentication",
            requires_approval=integration_output.requires_human_review
        )

        review_items = []
        if integration_output.requires_human_review:
            review_items.extend(integration_output.review_items or [])

        return {
            "outputs": {"integration_config_result": integration_output.outputs},
            "integrations": integration_output.outputs.get("connector_specs", {}),
            "decisions": [decision],
            "requires_human_review": integration_output.requires_human_review,
            "review_items": review_items,
            "current_step": "configure_integrations",
            "agent_context": {
                **context,
                "current_phase": BuildPhase.INTEGRATION_CONFIG.value
            },
            "messages": [Message(
                role="assistant",
                content=f"Integration Configuration completed. Success: {integration_output.success}, Confidence: {integration_output.confidence}"
            )],
            "errors": integration_output.errors or []
        }

    async def _setup_deployment(self, state: AppBuilderState) -> Dict[str, Any]:
        """Set up deployment using the Deployment agent."""
        context = state.get("agent_context", {})
        outputs = state.get("outputs", {})

        # Create app spec from previous outputs
        app_spec = {
            "ui_components": state.get("ui_components", []),
            "workflows": state.get("workflows", []),
            "integrations": state.get("integrations", {})
        }

        # Create input for Deployment agent
        deployment_input = AgentInput(
            engagement_id=state.get("engagement_id", ""),
            phase=BuildPhase.DEPLOYMENT_SETUP.value,
            context={
                "app_spec": app_spec,
                "deployment_requirements": context.get("deployment_requirements", {})
            },
            previous_outputs=outputs
        )

        # Run Deployment agent
        deployment_output = await self.deployment_agent.run(deployment_input)

        decision = add_decision(
            state,
            decision_type="deployment_setup",
            description="Set up deployment configuration",
            confidence=deployment_output.confidence,
            reasoning="Deployment agent generated K8s manifests, Docker configs, and CI/CD pipelines",
            requires_approval=deployment_output.requires_human_review
        )

        review_items = []
        if deployment_output.requires_human_review:
            review_items.extend(deployment_output.review_items or [])

        return {
            "outputs": {"deployment_setup_result": deployment_output.outputs},
            "deployment_config": deployment_output.outputs.get("infrastructure_spec", {}),
            "decisions": [decision],
            "requires_human_review": deployment_output.requires_human_review,
            "review_items": review_items,
            "current_step": "setup_deployment",
            "agent_context": {
                **context,
                "current_phase": BuildPhase.DEPLOYMENT_SETUP.value
            },
            "messages": [Message(
                role="assistant",
                content=f"Deployment Setup completed. Success: {deployment_output.success}, Confidence: {deployment_output.confidence}"
            )],
            "errors": deployment_output.errors or []
        }

    async def _compile_specification(self, state: AppBuilderState) -> Dict[str, Any]:
        """Compile the complete application specification."""
        context = state.get("agent_context", {})
        outputs = state.get("outputs", {})

        ui_components = state.get("ui_components", [])
        workflows = state.get("workflows", [])
        integrations = state.get("integrations", {})
        deployment_config = state.get("deployment_config", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Compile the complete application specification from all generated components.

UI Components:
{ui_components}

Workflows:
{workflows}

Integrations:
{integrations}

Deployment Configuration:
{deployment_config}

Original Requirements:
{context.get('requirements', {})}

Create a comprehensive application specification document that includes:

1. Application Overview:
   - Name and description
   - Architecture diagram (text-based)
   - Technology stack summary
   - Key features and capabilities

2. Component Inventory:
   - UI components with dependencies
   - Workflow definitions with triggers
   - Integration endpoints with authentication
   - Infrastructure resources

3. Data Flow:
   - User interactions
   - Workflow execution paths
   - Integration data flows
   - Event propagation

4. Configuration Summary:
   - Environment variables required
   - Secrets and credentials needed
   - Feature flags
   - Scaling parameters

5. Deployment Guide:
   - Prerequisites
   - Installation steps
   - Configuration steps
   - Verification steps

6. Operations Guide:
   - Monitoring setup
   - Alerting configuration
   - Backup procedures
   - Troubleshooting guide

Output as a comprehensive JSON application specification.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="specification_compilation",
            description="Compiled complete application specification",
            confidence=0.85,
            reasoning="Combined all generated components into unified specification"
        )

        return {
            "outputs": {"app_specification": response.content},
            "decisions": [decision],
            "current_step": "compile_specification",
            "agent_context": {
                **context,
                "current_phase": BuildPhase.VALIDATION.value
            },
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _validate_application(self, state: AppBuilderState) -> Dict[str, Any]:
        """Validate the complete application specification."""
        context = state.get("agent_context", {})
        outputs = state.get("outputs", {})
        app_specification = outputs.get("app_specification", "")
        requirements = context.get("requirements", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate the complete application specification.

Application Specification:
{app_specification}

Original Requirements:
{requirements}

Validate:
1. Requirement Coverage:
   - All functional requirements addressed
   - All non-functional requirements met
   - All entities have CRUD operations
   - All workflows are complete

2. Consistency:
   - UI types match ontology
   - Workflow entities match schema
   - Integration endpoints are valid
   - Deployment configs are coherent

3. Completeness:
   - All components defined
   - All configurations specified
   - All dependencies listed
   - Documentation complete

4. Security:
   - Authentication configured
   - Authorization rules defined
   - Secrets properly managed
   - Network policies specified

5. Operability:
   - Monitoring configured
   - Logging specified
   - Alerting defined
   - Runbooks provided

6. Quality:
   - Best practices followed
   - Patterns consistent
   - Code generation ready
   - Maintainable structure

Provide:
1. Validation status (PASS/FAIL)
2. Requirements coverage percentage
3. List of issues found
4. Critical items for review
5. Recommendations
6. Overall confidence score (0-1)
7. Build summary""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse validation result
        response_lower = response.content.lower()
        has_critical_issues = "critical" in response_lower or "fail" in response_lower
        has_minor_issues = "issue" in response_lower or "warning" in response_lower

        if has_critical_issues:
            needs_review = True
            needs_refinement = False  # Critical issues need human review
            confidence = 0.50
        elif has_minor_issues:
            needs_review = False
            needs_refinement = True  # Minor issues can be auto-refined
            confidence = 0.75
        else:
            needs_review = False
            needs_refinement = False
            confidence = 0.90

        decision = add_decision(
            state,
            decision_type="application_validation",
            description="Validated complete application specification",
            confidence=confidence,
            reasoning=response.content[:500],
            requires_approval=has_critical_issues
        )

        review_items = []
        if has_critical_issues:
            review_items.append(mark_for_review(
                state,
                item_type="application_specification",
                item_id="critical_issues",
                description="Application specification has critical issues requiring review",
                priority="critical"
            ))

        return {
            "outputs": {
                "validation_result": response.content,
                "build_summary": self._create_build_summary(state, response.content),
                "needs_refinement": needs_refinement,
                "has_critical_issues": has_critical_issues
            },
            "decisions": [decision],
            "requires_human_review": needs_review,
            "review_items": review_items,
            "current_step": "validate_application",
            "agent_context": {
                **context,
                "current_phase": BuildPhase.COMPLETE.value if not needs_refinement and not needs_review else BuildPhase.VALIDATION.value
            },
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _create_build_summary(self, state: AppBuilderState, validation_result: str) -> Dict[str, Any]:
        """Create a summary of the build process."""
        decisions = state.get("decisions", [])
        errors = state.get("errors", [])

        return {
            "total_decisions": len(decisions),
            "phases_completed": [
                BuildPhase.PLANNING.value,
                BuildPhase.UI_GENERATION.value,
                BuildPhase.WORKFLOW_DESIGN.value,
                BuildPhase.INTEGRATION_CONFIG.value,
                BuildPhase.DEPLOYMENT_SETUP.value,
                BuildPhase.VALIDATION.value
            ],
            "errors_encountered": len(errors),
            "validation_summary": validation_result[:1000],
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_review(self, state: AppBuilderState) -> Dict[str, Any]:
        """Handle items that require human review."""
        review_items = state.get("review_items", [])
        current_step = state.get("current_step", "")

        decision = add_decision(
            state,
            decision_type="review_required",
            description=f"Human review required after {current_step}",
            confidence=0.5,
            reasoning=f"Issues found during {current_step} require human attention",
            requires_approval=True
        )

        return {
            "decisions": [decision],
            "requires_human_review": True,
            "current_step": "handle_review",
            "messages": [Message(
                role="assistant",
                content=f"Build paused for review. {len(review_items)} items require attention."
            )]
        }

    def _route_after_planning(self, state: AppBuilderState) -> str:
        """Route after planning phase."""
        if state.get("requires_human_review", False):
            return "review"
        return "generate_ui"

    def _route_after_ui(self, state: AppBuilderState) -> str:
        """Route after UI generation phase."""
        if state.get("requires_human_review", False):
            return "review"
        return "design_workflows"

    def _route_after_workflows(self, state: AppBuilderState) -> str:
        """Route after workflow design phase."""
        if state.get("requires_human_review", False):
            return "review"
        return "configure_integrations"

    def _route_after_integrations(self, state: AppBuilderState) -> str:
        """Route after integration configuration phase."""
        if state.get("requires_human_review", False):
            return "review"
        return "setup_deployment"

    def _route_after_deployment(self, state: AppBuilderState) -> str:
        """Route after deployment setup phase."""
        if state.get("requires_human_review", False):
            return "review"
        return "compile_specification"

    def _route_after_validation(self, state: AppBuilderState) -> str:
        """Route after validation phase."""
        outputs = state.get("outputs", {})

        if outputs.get("has_critical_issues", False):
            return "review"
        if outputs.get("needs_refinement", False):
            # Track iterations
            iteration_count = state.get("agent_context", {}).get("iteration_count", 0)
            max_iterations = self.config.get("max_iterations", 2)
            if iteration_count < max_iterations:
                return "refine"
        return "complete"
