"""
Operations Agent Cluster

Orchestrates the operations agents for comprehensive system operations management
including monitoring, scaling, maintenance, and incident response.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from enum import Enum
import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from agent_framework.base_agent import BaseOpenForgeAgent
from agent_framework.state_management import (
    OperationsState,
    Decision,
    Message,
    add_decision,
    mark_for_review,
)
from agent_framework.graph_builder import WorkflowBuilder
from agent_framework.prompts import PromptTemplate, PromptLibrary

from contracts.agent_interface import AgentInput, AgentOutput

from .monitoring_agent import MonitoringAgent
from .scaling_agent import ScalingAgent
from .maintenance_agent import MaintenanceAgent
from .incident_agent import IncidentAgent


class OperationsPhase(str, Enum):
    """Phases of the operations configuration process."""
    MONITORING = "monitoring"
    SCALING = "scaling"
    MAINTENANCE = "maintenance"
    INCIDENT = "incident"
    CONSOLIDATION = "consolidation"
    COMPLETE = "complete"


class OperationsReport(BaseModel):
    """Consolidated operations report output."""
    engagement_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Monitoring outputs
    prometheus_configs: Dict[str, Any] = Field(default_factory=dict)
    grafana_dashboards: List[Dict[str, Any]] = Field(default_factory=list)
    alerting_rules: List[Dict[str, Any]] = Field(default_factory=list)
    entity_metrics_map: Dict[str, Any] = Field(default_factory=dict)

    # Scaling outputs
    hpa_configs: List[Dict[str, Any]] = Field(default_factory=list)
    load_balancer_configs: Dict[str, Any] = Field(default_factory=dict)
    scaling_recommendations: Dict[str, Any] = Field(default_factory=dict)

    # Maintenance outputs
    backup_strategies: List[Dict[str, Any]] = Field(default_factory=list)
    maintenance_schedules: List[Dict[str, Any]] = Field(default_factory=list)
    health_check_scripts: List[Dict[str, Any]] = Field(default_factory=list)
    disaster_recovery_plan: Dict[str, Any] = Field(default_factory=dict)

    # Incident outputs
    incident_playbooks: List[Dict[str, Any]] = Field(default_factory=list)
    escalation_procedures: List[Dict[str, Any]] = Field(default_factory=list)
    postmortem_templates: List[Dict[str, Any]] = Field(default_factory=list)

    # Overall metrics
    confidence_score: float = 0.0
    requires_human_review: bool = False
    review_items: List[Dict[str, Any]] = Field(default_factory=list)
    all_decisions: List[Dict[str, Any]] = Field(default_factory=list)

    # Next steps
    recommended_actions: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)


# Cluster orchestration prompts
OPERATIONS_ORCHESTRATOR_SYSTEM = PromptTemplate("""You are the Operations Cluster Orchestrator in the Open Forge platform.

Your role is to coordinate the operations agents and produce comprehensive operations configurations.

Engagement ID: $engagement_id
Phase: $phase

Operations agents under your coordination:
1. Monitoring Agent - Generates Prometheus configs, Grafana dashboards, and alerting rules
2. Scaling Agent - Creates auto-scaling policies and load balancer configurations
3. Maintenance Agent - Produces backup strategies, maintenance schedules, and health checks
4. Incident Agent - Develops incident playbooks, escalation procedures, and post-mortems

Your responsibilities:
- Orchestrate agent execution in the correct order
- Pass relevant context between agents (ontology, system architecture, etc.)
- Consolidate outputs into a unified operations package
- Identify blockers and required human reviews
- Ensure consistency across all operational configurations

Current context:
$context
""")

OPERATIONS_CONSOLIDATION_PROMPT = PromptTemplate("""Consolidate all operations configurations into a comprehensive summary.

Monitoring Results:
$monitoring_results

Scaling Results:
$scaling_results

Maintenance Results:
$maintenance_results

Incident Results:
$incident_results

Create a consolidated summary that includes:
1. Operations readiness assessment
2. Key configurations generated
3. Integration points between components
4. Deployment recommendations
5. Gaps or areas needing attention
6. Recommended actions for operations team
7. Training recommendations for new configurations

Output as a structured JSON summary.
""")


class OperationsCluster:
    """
    Orchestrates the operations agent cluster.

    The operations cluster coordinates four specialized agents:
    1. MonitoringAgent - Prometheus, Grafana, alerting configurations
    2. ScalingAgent - HPA, load balancer, auto-scaling configurations
    3. MaintenanceAgent - Backup, maintenance schedule, health check configurations
    4. IncidentAgent - Playbooks, escalation, post-mortem configurations

    The cluster manages the workflow between agents, passing outputs from
    one agent as context to the next, and produces a consolidated
    operations package.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        memory: Optional[MemorySaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.llm = llm
        self.memory = memory or MemorySaver()
        self.config = config or {}

        # Initialize the specialized agents
        self.monitoring_agent = MonitoringAgent(
            llm=llm,
            memory=memory,
            config=config
        )
        self.scaling_agent = ScalingAgent(
            llm=llm,
            memory=memory,
            config=config
        )
        self.maintenance_agent = MaintenanceAgent(
            llm=llm,
            memory=memory,
            config=config
        )
        self.incident_agent = IncidentAgent(
            llm=llm,
            memory=memory,
            config=config
        )

        self._graph: Optional[StateGraph] = None
        self._compiled_graph = None

        # Register prompts
        PromptLibrary.register("operations_orchestrator_system", OPERATIONS_ORCHESTRATOR_SYSTEM)
        PromptLibrary.register("operations_consolidation_prompt", OPERATIONS_CONSOLIDATION_PROMPT)

    @property
    def name(self) -> str:
        return "operations_cluster"

    @property
    def description(self) -> str:
        return (
            "Orchestrates operations agents to generate monitoring, scaling, "
            "maintenance, and incident management configurations."
        )

    @property
    def agents(self) -> List[BaseOpenForgeAgent]:
        """Return list of agents in this cluster."""
        return [
            self.monitoring_agent,
            self.scaling_agent,
            self.maintenance_agent,
            self.incident_agent
        ]

    def build_graph(self) -> StateGraph:
        """Build the cluster orchestration workflow."""
        builder = WorkflowBuilder(OperationsState)

        async def run_monitoring(state: OperationsState) -> Dict[str, Any]:
            """Run the monitoring agent."""
            context = state.get("agent_context", {})

            # Create input for monitoring agent
            agent_input = AgentInput(
                engagement_id=state.get("engagement_id", ""),
                phase=OperationsPhase.MONITORING.value,
                context={
                    "ontology_schema": context.get("ontology_schema", ""),
                    "system_requirements": context.get("system_requirements", {}),
                    "metrics_namespace": context.get("metrics_namespace", "openforge"),
                    "dashboard_title": context.get("dashboard_title", "Open Forge Operations")
                },
                previous_outputs=None,
                human_inputs=context.get("human_inputs", [])
            )

            # Run the agent
            output = await self.monitoring_agent.run(agent_input)

            # Handle errors
            if not output.success:
                return {
                    "errors": output.errors or ["Monitoring configuration failed"],
                    "current_step": "monitoring_failed"
                }

            # Store outputs in state
            return {
                "outputs": output.outputs,
                "prometheus_configs": output.outputs.get("prometheus_config", {}),
                "grafana_dashboards": output.outputs.get("grafana_dashboards", []),
                "alerting_rules": output.outputs.get("alerting_rules", []),
                "entity_metrics_map": output.outputs.get("entity_metrics_map", {}),
                "decisions": [Decision(**d) for d in output.decisions],
                "requires_human_review": output.requires_human_review,
                "review_items": output.review_items or [],
                "current_step": "monitoring_complete"
            }

        async def run_scaling(state: OperationsState) -> Dict[str, Any]:
            """Run the scaling agent."""
            context = state.get("agent_context", {})
            current_outputs = state.get("outputs", {})

            # Pass monitoring outputs as context
            agent_input = AgentInput(
                engagement_id=state.get("engagement_id", ""),
                phase=OperationsPhase.SCALING.value,
                context={
                    "workload_specs": context.get("workload_specs", {}),
                    "scaling_requirements": context.get("scaling_requirements", {}),
                    "ontology_schema": context.get("ontology_schema", ""),
                    "namespace": context.get("namespace", "default"),
                    "domain": context.get("domain", "example.com"),
                    "historical_metrics": context.get("historical_metrics", {}),
                    "sla_requirements": context.get("sla_requirements", {})
                },
                previous_outputs={
                    "prometheus_metrics": state.get("prometheus_configs", {}),
                    **current_outputs
                },
                human_inputs=context.get("human_inputs", [])
            )

            output = await self.scaling_agent.run(agent_input)

            if not output.success:
                return {
                    "errors": output.errors or ["Scaling configuration failed"],
                    "current_step": "scaling_failed"
                }

            # Merge outputs
            merged_outputs = {**current_outputs, **output.outputs}

            return {
                "outputs": merged_outputs,
                "scaling_policies": output.outputs.get("hpa_configs", []),
                "load_balancer_configs": output.outputs.get("load_balancer_configs", {}),
                "workload_analysis": output.outputs.get("workload_analysis", {}),
                "decisions": [Decision(**d) for d in output.decisions],
                "requires_human_review": (
                    state.get("requires_human_review", False) or output.requires_human_review
                ),
                "review_items": output.review_items or [],
                "current_step": "scaling_complete"
            }

        async def run_maintenance(state: OperationsState) -> Dict[str, Any]:
            """Run the maintenance agent."""
            context = state.get("agent_context", {})
            current_outputs = state.get("outputs", {})

            agent_input = AgentInput(
                engagement_id=state.get("engagement_id", ""),
                phase=OperationsPhase.MAINTENANCE.value,
                context={
                    "system_components": context.get("system_components", {}),
                    "maintenance_requirements": context.get("maintenance_requirements", {}),
                    "ontology_schema": context.get("ontology_schema", ""),
                    "backup_storage": context.get("backup_storage", "s3://backups"),
                    "retention_policy": context.get("retention_policy", {}),
                    "maintenance_windows": context.get("maintenance_windows", {}),
                    "timezone": context.get("timezone", "UTC"),
                    "endpoints": context.get("endpoints", {})
                },
                previous_outputs={
                    "monitoring_configs": state.get("prometheus_configs", {}),
                    "scaling_configs": state.get("scaling_policies", []),
                    **current_outputs
                },
                human_inputs=context.get("human_inputs", [])
            )

            output = await self.maintenance_agent.run(agent_input)

            if not output.success:
                return {
                    "errors": output.errors or ["Maintenance configuration failed"],
                    "current_step": "maintenance_failed"
                }

            # Merge outputs
            merged_outputs = {**current_outputs, **output.outputs}

            return {
                "outputs": merged_outputs,
                "backup_strategies": output.outputs.get("backup_strategies", []),
                "maintenance_schedules": output.outputs.get("maintenance_schedules", []),
                "health_check_scripts": output.outputs.get("health_check_scripts", []),
                "decisions": [Decision(**d) for d in output.decisions],
                "requires_human_review": (
                    state.get("requires_human_review", False) or output.requires_human_review
                ),
                "review_items": output.review_items or [],
                "current_step": "maintenance_complete"
            }

        async def run_incident(state: OperationsState) -> Dict[str, Any]:
            """Run the incident agent."""
            context = state.get("agent_context", {})
            current_outputs = state.get("outputs", {})

            agent_input = AgentInput(
                engagement_id=state.get("engagement_id", ""),
                phase=OperationsPhase.INCIDENT.value,
                context={
                    "system_architecture": context.get("system_architecture", {}),
                    "team_structure": context.get("team_structure", {}),
                    "ontology_schema": context.get("ontology_schema", ""),
                    "communication_channels": context.get("communication_channels", {}),
                    "business_hours": context.get("business_hours", "09:00-18:00 UTC, Mon-Fri"),
                    "sla_requirements": context.get("sla_requirements", {}),
                    "historical_incidents": context.get("historical_incidents", [])
                },
                previous_outputs={
                    "monitoring_configs": state.get("prometheus_configs", {}),
                    "alerting_rules": state.get("alerting_rules", []),
                    "health_checks": state.get("health_check_scripts", []),
                    **current_outputs
                },
                human_inputs=context.get("human_inputs", [])
            )

            output = await self.incident_agent.run(agent_input)

            if not output.success:
                return {
                    "errors": output.errors or ["Incident configuration failed"],
                    "current_step": "incident_failed"
                }

            # Merge outputs
            merged_outputs = {**current_outputs, **output.outputs}

            return {
                "outputs": merged_outputs,
                "incident_playbooks": output.outputs.get("incident_playbooks", []),
                "escalation_procedures": output.outputs.get("escalation_procedures", []),
                "postmortem_templates": output.outputs.get("postmortem_templates", []),
                "decisions": [Decision(**d) for d in output.decisions],
                "requires_human_review": (
                    state.get("requires_human_review", False) or output.requires_human_review
                ),
                "review_items": output.review_items or [],
                "current_step": "incident_complete"
            }

        async def consolidate_results(state: OperationsState) -> Dict[str, Any]:
            """Consolidate all operations results into a report."""
            outputs = state.get("outputs", {})

            # Create consolidation prompt
            prompt = PromptLibrary.format(
                "operations_consolidation_prompt",
                monitoring_results=json.dumps({
                    "prometheus_configs": state.get("prometheus_configs", {}),
                    "grafana_dashboards": state.get("grafana_dashboards", []),
                    "alerting_rules": state.get("alerting_rules", []),
                    "entity_metrics_map": state.get("entity_metrics_map", {})
                }, default=str),
                scaling_results=json.dumps({
                    "scaling_policies": state.get("scaling_policies", []),
                    "load_balancer_configs": state.get("load_balancer_configs", {}),
                    "workload_analysis": state.get("workload_analysis", {})
                }, default=str),
                maintenance_results=json.dumps({
                    "backup_strategies": state.get("backup_strategies", []),
                    "maintenance_schedules": state.get("maintenance_schedules", []),
                    "health_check_scripts": state.get("health_check_scripts", [])
                }, default=str),
                incident_results=json.dumps({
                    "incident_playbooks": state.get("incident_playbooks", []),
                    "escalation_procedures": state.get("escalation_procedures", []),
                    "postmortem_templates": state.get("postmortem_templates", [])
                }, default=str)
            )

            messages = [
                SystemMessage(content=PromptLibrary.format(
                    "operations_orchestrator_system",
                    engagement_id=state.get("engagement_id", ""),
                    phase=OperationsPhase.CONSOLIDATION.value,
                    context=""
                )),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                summary = json.loads(response.content)
            except json.JSONDecodeError:
                summary = self._extract_json_from_response(response.content)

            # Build the final report
            decisions = state.get("decisions", [])
            avg_confidence = (
                sum(d.confidence for d in decisions) / len(decisions)
                if decisions else 0.5
            )

            # Identify blockers
            blockers = []
            if state.get("requires_human_review"):
                blockers.append("Human review required for flagged items")
            if state.get("errors"):
                blockers.extend([f"Error: {e}" for e in state.get("errors", [])])

            report = {
                "operations_report": {
                    "engagement_id": state.get("engagement_id", ""),
                    "generated_at": datetime.utcnow().isoformat(),
                    "summary": summary,
                    # Monitoring
                    "prometheus_configs": state.get("prometheus_configs", {}),
                    "grafana_dashboards": state.get("grafana_dashboards", []),
                    "alerting_rules": state.get("alerting_rules", []),
                    "entity_metrics_map": state.get("entity_metrics_map", {}),
                    # Scaling
                    "hpa_configs": state.get("scaling_policies", []),
                    "load_balancer_configs": state.get("load_balancer_configs", {}),
                    "scaling_recommendations": outputs.get("scaling_recommendations", {}),
                    # Maintenance
                    "backup_strategies": state.get("backup_strategies", []),
                    "maintenance_schedules": state.get("maintenance_schedules", []),
                    "health_check_scripts": state.get("health_check_scripts", []),
                    "disaster_recovery_plan": outputs.get("disaster_recovery_plan", {}),
                    # Incident
                    "incident_playbooks": state.get("incident_playbooks", []),
                    "escalation_procedures": state.get("escalation_procedures", []),
                    "postmortem_templates": state.get("postmortem_templates", []),
                    # Metadata
                    "confidence_score": avg_confidence,
                    "requires_human_review": state.get("requires_human_review", False),
                    "review_items": state.get("review_items", []),
                    "all_decisions": [d.model_dump() for d in decisions],
                    "recommended_actions": summary.get("recommended_actions", []) if isinstance(summary, dict) else [],
                    "blockers": blockers
                }
            }

            decision = add_decision(
                state,
                decision_type="operations_consolidation",
                description="Consolidated operations results into final report",
                confidence=avg_confidence,
                reasoning="Aggregated outputs from all operations agents"
            )

            return {
                "outputs": {**outputs, **report},
                "decisions": [decision],
                "current_step": "complete"
            }

        def route_after_monitoring(state: OperationsState) -> str:
            """Route after monitoring phase."""
            if state.get("errors"):
                return "handle_error"
            return "scaling"

        def route_after_scaling(state: OperationsState) -> str:
            """Route after scaling phase."""
            if state.get("errors"):
                return "handle_error"
            return "maintenance"

        def route_after_maintenance(state: OperationsState) -> str:
            """Route after maintenance phase."""
            if state.get("errors"):
                return "handle_error"
            return "incident"

        def route_after_incident(state: OperationsState) -> str:
            """Route after incident phase."""
            if state.get("errors"):
                return "handle_error"
            return "consolidate"

        async def handle_error(state: OperationsState) -> Dict[str, Any]:
            """Handle errors in the workflow."""
            errors = state.get("errors", [])

            review_items = state.get("review_items", [])
            review_items.append(
                mark_for_review(
                    state,
                    item_type="cluster_error",
                    item_id="operations_cluster_error",
                    description=f"Operations cluster encountered errors: {', '.join(errors)}",
                    priority="high"
                )
            )

            return {
                "requires_human_review": True,
                "review_items": review_items,
                "current_step": "error_handled"
            }

        # Build the workflow
        graph = (builder
            .add_node("monitoring", run_monitoring)
            .add_node("scaling", run_scaling)
            .add_node("maintenance", run_maintenance)
            .add_node("incident", run_incident)
            .add_node("consolidate", consolidate_results)
            .add_node("handle_error", handle_error)
            .set_entry("monitoring")
            .add_conditional("monitoring", route_after_monitoring, {
                "scaling": "scaling",
                "handle_error": "handle_error"
            })
            .add_conditional("scaling", route_after_scaling, {
                "maintenance": "maintenance",
                "handle_error": "handle_error"
            })
            .add_conditional("maintenance", route_after_maintenance, {
                "incident": "incident",
                "handle_error": "handle_error"
            })
            .add_conditional("incident", route_after_incident, {
                "consolidate": "consolidate",
                "handle_error": "handle_error"
            })
            .add_edge("consolidate", "END")
            .add_edge("handle_error", "END")
            .build())

        return graph

    def get_graph(self) -> StateGraph:
        """Get or build the cluster graph."""
        if self._graph is None:
            self._graph = self.build_graph()
        return self._graph

    def compile(self):
        """Compile the graph for execution."""
        if self._compiled_graph is None:
            graph = self.get_graph()
            self._compiled_graph = graph.compile(checkpointer=self.memory)
        return self._compiled_graph

    async def run(self, input: AgentInput) -> AgentOutput:
        """Execute the operations cluster workflow."""
        # Validate required inputs
        required = ["ontology_schema", "system_architecture"]
        missing = [r for r in required if r not in input.context]
        if missing:
            return AgentOutput(
                agent_name=self.name,
                timestamp=datetime.utcnow(),
                success=False,
                outputs={},
                decisions=[],
                confidence=0.0,
                requires_human_review=False,
                errors=[f"Missing required inputs: {missing}"]
            )

        # Create initial state
        initial_state = OperationsState(
            engagement_id=input.engagement_id,
            phase=input.phase,
            messages=[],
            outputs={},
            decisions=[],
            current_step="start",
            requires_human_review=False,
            review_items=[],
            errors=[],
            agent_context=input.context,
            # Monitoring state
            prometheus_configs={},
            grafana_dashboards=[],
            alerting_rules=[],
            # Scaling state
            scaling_policies=[],
            load_balancer_configs={},
            workload_analysis={},
            # Maintenance state
            backup_strategies=[],
            maintenance_schedules=[],
            health_check_scripts=[],
            # Incident state
            incident_playbooks=[],
            escalation_procedures=[],
            postmortem_templates=[],
            # Ontology integration
            entity_metrics_map={}
        )

        # Add human inputs if provided
        if input.human_inputs:
            initial_state["agent_context"]["human_inputs"] = input.human_inputs

        # Add previous outputs if provided
        if input.previous_outputs:
            initial_state["agent_context"]["previous_outputs"] = input.previous_outputs

        # Run the graph
        compiled = self.compile()
        config = {"configurable": {"thread_id": input.engagement_id}}

        try:
            final_state = await compiled.ainvoke(initial_state, config)

            # Extract the operations report
            outputs = final_state.get("outputs", {})
            operations_report = outputs.get("operations_report", {})

            # Calculate overall confidence
            decisions = final_state.get("decisions", [])
            confidence = (
                sum(d.confidence for d in decisions) / len(decisions)
                if decisions else 0.0
            )

            return AgentOutput(
                agent_name=self.name,
                timestamp=datetime.utcnow(),
                success=len(final_state.get("errors", [])) == 0,
                outputs=outputs,
                decisions=[d.model_dump() for d in decisions],
                confidence=confidence,
                requires_human_review=final_state.get("requires_human_review", False),
                review_items=final_state.get("review_items", []),
                next_suggested_action=self._get_next_action(final_state),
                errors=final_state.get("errors", [])
            )
        except Exception as e:
            return AgentOutput(
                agent_name=self.name,
                timestamp=datetime.utcnow(),
                success=False,
                outputs={},
                decisions=[],
                confidence=0.0,
                requires_human_review=True,
                review_items=[{
                    "type": "error",
                    "description": f"Operations cluster execution failed: {str(e)}",
                    "priority": "high"
                }],
                errors=[str(e)]
            )

    def _get_next_action(self, state: OperationsState) -> Optional[str]:
        """Determine suggested next action based on state."""
        if state.get("requires_human_review"):
            return "await_human_review"
        if state.get("errors"):
            return "handle_errors"
        if state.get("current_step") == "complete":
            return "deploy_operations_configs"
        return None

    def get_report(self, outputs: Dict[str, Any]) -> Optional[OperationsReport]:
        """Extract and validate the operations report from outputs."""
        report_data = outputs.get("operations_report")
        if report_data:
            return OperationsReport(**report_data)
        return None

    def _extract_json_from_response(self, response: str) -> Any:
        """Extract JSON from an LLM response that may contain other text."""
        import re

        # Look for JSON object
        object_match = re.search(r'\{[\s\S]*\}', response)
        if object_match:
            try:
                return json.loads(object_match.group())
            except json.JSONDecodeError:
                pass

        # Look for JSON array
        array_match = re.search(r'\[[\s\S]*\]', response)
        if array_match:
            try:
                return json.loads(array_match.group())
            except json.JSONDecodeError:
                pass

        return {}


# Convenience function for running operations cluster
async def run_operations(
    llm: BaseChatModel,
    engagement_id: str,
    ontology_schema: str,
    system_architecture: Dict[str, Any],
    workload_specs: Optional[Dict[str, Any]] = None,
    system_components: Optional[Dict[str, Any]] = None,
    team_structure: Optional[Dict[str, Any]] = None,
    system_requirements: Optional[Dict[str, Any]] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> AgentOutput:
    """
    Convenience function to run the operations cluster.

    Args:
        llm: The language model to use
        engagement_id: Unique identifier for the engagement
        ontology_schema: LinkML ontology schema (YAML string)
        system_architecture: System architecture description
        workload_specs: Workload specifications for scaling
        system_components: System components for maintenance
        team_structure: Team structure for incident management
        system_requirements: System requirements for monitoring
        additional_context: Additional context information

    Returns:
        AgentOutput with the operations report
    """
    cluster = OperationsCluster(llm=llm)

    context = {
        "ontology_schema": ontology_schema,
        "system_architecture": system_architecture,
        "workload_specs": workload_specs or {},
        "system_components": system_components or {},
        "team_structure": team_structure or {},
        "system_requirements": system_requirements or {},
        **(additional_context or {})
    }

    input_data = AgentInput(
        engagement_id=engagement_id,
        phase="operations",
        context=context
    )

    return await cluster.run(input_data)


# Convenience function for creating the cluster
def create_operations_cluster(
    llm: BaseChatModel,
    memory: Optional[MemorySaver] = None,
    config: Optional[Dict[str, Any]] = None
) -> OperationsCluster:
    """Create a configured OperationsCluster instance."""
    default_config = {
        "max_iterations": 3,
        "validation_threshold": 0.8
    }
    if config:
        default_config.update(config)
    return OperationsCluster(llm, memory, default_config)
