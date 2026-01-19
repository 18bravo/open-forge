"""
Discovery Agent Cluster

Orchestrates the discovery agents to understand client needs
and discover data sources for an engagement.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from enum import Enum
import json

from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from agent_framework.base_agent import BaseOpenForgeAgent
from agent_framework.state_management import (
    DiscoveryState,
    Decision,
    add_decision,
    mark_for_review,
    create_initial_state,
)
from agent_framework.graph_builder import WorkflowBuilder
from agent_framework.prompts import PromptTemplate, PromptLibrary

from contracts.agent_interface import AgentInput, AgentOutput

from .stakeholder_agent import StakeholderAnalysisAgent
from .source_discovery_agent import SourceDiscoveryAgent
from .requirements_agent import RequirementsGatheringAgent


class DiscoveryPhase(str, Enum):
    """Phases of the discovery process."""
    STAKEHOLDER_ANALYSIS = "stakeholder_analysis"
    SOURCE_DISCOVERY = "source_discovery"
    REQUIREMENTS_GATHERING = "requirements_gathering"
    CONSOLIDATION = "consolidation"
    COMPLETE = "complete"


class DiscoveryReport(BaseModel):
    """Consolidated discovery report output."""
    engagement_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Stakeholder analysis outputs
    stakeholders: List[Dict[str, Any]] = Field(default_factory=list)
    business_processes: List[Dict[str, Any]] = Field(default_factory=list)
    stakeholder_map: Dict[str, Any] = Field(default_factory=dict)

    # Source discovery outputs
    discovered_sources: List[Dict[str, Any]] = Field(default_factory=list)
    source_catalog: Dict[str, Any] = Field(default_factory=dict)
    quality_assessments: Dict[str, Any] = Field(default_factory=dict)
    source_recommendations: List[Dict[str, Any]] = Field(default_factory=list)

    # Requirements gathering outputs
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    prioritized_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    integration_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    requirements_document: Dict[str, Any] = Field(default_factory=dict)

    # Overall metrics
    confidence_score: float = 0.0
    requires_human_review: bool = False
    review_items: List[Dict[str, Any]] = Field(default_factory=list)
    all_decisions: List[Dict[str, Any]] = Field(default_factory=list)

    # Next steps
    recommended_next_phase: str = "data_architecture"
    blockers: List[str] = Field(default_factory=list)


# Cluster orchestration prompts
CLUSTER_ORCHESTRATOR_SYSTEM = PromptTemplate("""You are the Discovery Cluster Orchestrator in the Open Forge platform.

Your role is to coordinate the discovery agents and produce a consolidated discovery report.

Engagement ID: $engagement_id
Phase: $phase

Discovery agents under your coordination:
1. Stakeholder Analysis Agent - Analyzes stakeholder requirements and maps business processes
2. Source Discovery Agent - Discovers and assesses data sources
3. Requirements Gathering Agent - Synthesizes and prioritizes requirements

Your responsibilities:
- Orchestrate agent execution in the correct order
- Pass context between agents
- Consolidate outputs into a unified discovery report
- Identify blockers and required human reviews
- Recommend next steps

Current context:
$context
""")

CONSOLIDATION_PROMPT = PromptTemplate("""Consolidate the discovery phase outputs into a summary.

Stakeholder Analysis Results:
$stakeholder_results

Source Discovery Results:
$source_results

Requirements Gathering Results:
$requirements_results

Create a consolidated summary that includes:
1. Key findings
2. Critical stakeholders identified
3. Priority data sources
4. Must-have requirements
5. Key integration points
6. Risks and concerns
7. Recommended next steps
8. Blockers that need resolution

Output as a structured JSON summary.
""")


class DiscoveryCluster:
    """
    Orchestrates the discovery agent cluster.

    The discovery cluster coordinates three specialized agents:
    1. StakeholderAnalysisAgent - Stakeholder requirements and business processes
    2. SourceDiscoveryAgent - Data source discovery and assessment
    3. RequirementsGatheringAgent - Requirements synthesis and prioritization

    The cluster manages the workflow between agents, passing outputs from
    one agent as context to the next, and produces a consolidated
    discovery report.
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
        self.stakeholder_agent = StakeholderAnalysisAgent(
            llm=llm,
            memory=memory,
            config=config
        )
        self.source_discovery_agent = SourceDiscoveryAgent(
            llm=llm,
            memory=memory,
            config=config
        )
        self.requirements_agent = RequirementsGatheringAgent(
            llm=llm,
            memory=memory,
            config=config
        )

        self._graph: Optional[StateGraph] = None
        self._compiled_graph = None

        # Register prompts
        PromptLibrary.register("cluster_orchestrator_system", CLUSTER_ORCHESTRATOR_SYSTEM)
        PromptLibrary.register("consolidation_prompt", CONSOLIDATION_PROMPT)

    @property
    def name(self) -> str:
        return "discovery_cluster"

    @property
    def description(self) -> str:
        return (
            "Orchestrates discovery agents to understand client needs, "
            "discover data sources, and produce consolidated discovery report."
        )

    @property
    def agents(self) -> List[BaseOpenForgeAgent]:
        """Return list of agents in this cluster."""
        return [
            self.stakeholder_agent,
            self.source_discovery_agent,
            self.requirements_agent
        ]

    def build_graph(self) -> StateGraph:
        """Build the cluster orchestration workflow."""
        builder = WorkflowBuilder(DiscoveryState)

        async def run_stakeholder_analysis(state: DiscoveryState) -> Dict[str, Any]:
            """Run the stakeholder analysis agent."""
            context = state.get("agent_context", {})

            # Create input for stakeholder agent
            agent_input = AgentInput(
                engagement_id=state.get("engagement_id", ""),
                phase=DiscoveryPhase.STAKEHOLDER_ANALYSIS.value,
                context=context,
                previous_outputs=None,
                human_inputs=context.get("human_inputs", [])
            )

            # Run the agent
            output = await self.stakeholder_agent.run(agent_input)

            # Handle errors
            if not output.success:
                return {
                    "errors": output.errors or ["Stakeholder analysis failed"],
                    "current_step": "stakeholder_analysis_failed"
                }

            # Store outputs in state
            return {
                "outputs": output.outputs,
                "stakeholder_map": output.outputs.get("stakeholder_map", {}),
                "decisions": [Decision(**d) for d in output.decisions],
                "requires_human_review": output.requires_human_review,
                "review_items": output.review_items or [],
                "current_step": "stakeholder_analysis_complete"
            }

        async def run_source_discovery(state: DiscoveryState) -> Dict[str, Any]:
            """Run the source discovery agent."""
            context = state.get("agent_context", {})
            current_outputs = state.get("outputs", {})

            # Pass stakeholder outputs as previous outputs
            agent_input = AgentInput(
                engagement_id=state.get("engagement_id", ""),
                phase=DiscoveryPhase.SOURCE_DISCOVERY.value,
                context=context,
                previous_outputs={
                    "stakeholder_map": state.get("stakeholder_map", {}),
                    **current_outputs
                },
                human_inputs=context.get("human_inputs", [])
            )

            output = await self.source_discovery_agent.run(agent_input)

            if not output.success:
                return {
                    "errors": output.errors or ["Source discovery failed"],
                    "current_step": "source_discovery_failed"
                }

            # Merge outputs
            merged_outputs = {**current_outputs, **output.outputs}

            return {
                "outputs": merged_outputs,
                "discovered_sources": output.outputs.get("discovered_sources", []),
                "source_assessments": output.outputs.get("quality_assessments", {}),
                "decisions": [Decision(**d) for d in output.decisions],
                "requires_human_review": (
                    state.get("requires_human_review", False) or output.requires_human_review
                ),
                "review_items": output.review_items or [],
                "current_step": "source_discovery_complete"
            }

        async def run_requirements_gathering(state: DiscoveryState) -> Dict[str, Any]:
            """Run the requirements gathering agent."""
            context = state.get("agent_context", {})
            current_outputs = state.get("outputs", {})

            # Pass all previous outputs
            agent_input = AgentInput(
                engagement_id=state.get("engagement_id", ""),
                phase=DiscoveryPhase.REQUIREMENTS_GATHERING.value,
                context={
                    **context,
                    "stakeholder_requirements": state.get("stakeholder_map", {}).get(
                        "requirements_by_stakeholder", []
                    )
                },
                previous_outputs={
                    "stakeholder_map": state.get("stakeholder_map", {}),
                    "discovered_sources": state.get("discovered_sources", []),
                    "source_assessments": state.get("source_assessments", {}),
                    **current_outputs
                },
                human_inputs=context.get("human_inputs", [])
            )

            output = await self.requirements_agent.run(agent_input)

            if not output.success:
                return {
                    "errors": output.errors or ["Requirements gathering failed"],
                    "current_step": "requirements_gathering_failed"
                }

            # Merge outputs
            merged_outputs = {**current_outputs, **output.outputs}

            return {
                "outputs": merged_outputs,
                "requirements": output.outputs.get("prioritized_requirements", []),
                "decisions": [Decision(**d) for d in output.decisions],
                "requires_human_review": (
                    state.get("requires_human_review", False) or output.requires_human_review
                ),
                "review_items": output.review_items or [],
                "current_step": "requirements_gathering_complete"
            }

        async def consolidate_results(state: DiscoveryState) -> Dict[str, Any]:
            """Consolidate all discovery results into a report."""
            outputs = state.get("outputs", {})

            # Create consolidation prompt
            prompt = PromptLibrary.format(
                "consolidation_prompt",
                stakeholder_results=json.dumps({
                    "stakeholders": outputs.get("stakeholders", []),
                    "business_processes": outputs.get("business_processes", []),
                    "stakeholder_map": outputs.get("stakeholder_map", {})
                }),
                source_results=json.dumps({
                    "discovered_sources": outputs.get("discovered_sources", []),
                    "source_catalog": outputs.get("source_catalog", {}),
                    "quality_assessments": outputs.get("quality_assessments", {}),
                    "source_recommendations": outputs.get("source_recommendations", [])
                }),
                requirements_results=json.dumps({
                    "requirements": outputs.get("synthesized_requirements", []),
                    "prioritized_requirements": outputs.get("prioritized_requirements", []),
                    "integration_requirements": outputs.get("integration_requirements", []),
                    "requirements_document": outputs.get("requirements_document", {})
                })
            )

            from langchain_core.messages import SystemMessage, HumanMessage

            messages = [
                SystemMessage(content=PromptLibrary.format(
                    "cluster_orchestrator_system",
                    engagement_id=state.get("engagement_id", ""),
                    phase=DiscoveryPhase.CONSOLIDATION.value,
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
                "discovery_report": {
                    "engagement_id": state.get("engagement_id", ""),
                    "generated_at": datetime.utcnow().isoformat(),
                    "summary": summary,
                    "stakeholders": outputs.get("stakeholders", []),
                    "business_processes": outputs.get("business_processes", []),
                    "stakeholder_map": outputs.get("stakeholder_map", {}),
                    "discovered_sources": outputs.get("discovered_sources", []),
                    "source_catalog": outputs.get("source_catalog", {}),
                    "quality_assessments": outputs.get("quality_assessments", {}),
                    "source_recommendations": outputs.get("source_recommendations", []),
                    "requirements": outputs.get("prioritized_requirements", []),
                    "integration_requirements": outputs.get("integration_requirements", []),
                    "requirements_document": outputs.get("requirements_document", {}),
                    "confidence_score": avg_confidence,
                    "requires_human_review": state.get("requires_human_review", False),
                    "review_items": state.get("review_items", []),
                    "all_decisions": [d.model_dump() for d in decisions],
                    "recommended_next_phase": "data_architecture",
                    "blockers": blockers
                }
            }

            decision = add_decision(
                state,
                decision_type="discovery_consolidation",
                description="Consolidated discovery results into final report",
                confidence=avg_confidence,
                reasoning="Aggregated outputs from all discovery agents"
            )

            return {
                "outputs": {**outputs, **report},
                "decisions": [decision],
                "current_step": "complete"
            }

        def route_after_stakeholder(state: DiscoveryState) -> str:
            """Route after stakeholder analysis."""
            if state.get("errors"):
                return "handle_error"
            if state.get("requires_human_review"):
                # In a real implementation, might wait for review
                # For now, continue to next phase
                pass
            return "source_discovery"

        def route_after_source(state: DiscoveryState) -> str:
            """Route after source discovery."""
            if state.get("errors"):
                return "handle_error"
            return "requirements_gathering"

        def route_after_requirements(state: DiscoveryState) -> str:
            """Route after requirements gathering."""
            if state.get("errors"):
                return "handle_error"
            return "consolidate"

        async def handle_error(state: DiscoveryState) -> Dict[str, Any]:
            """Handle errors in the workflow."""
            errors = state.get("errors", [])

            review_items = state.get("review_items", [])
            review_items.append(
                mark_for_review(
                    state,
                    item_type="cluster_error",
                    item_id="discovery_cluster_error",
                    description=f"Discovery cluster encountered errors: {', '.join(errors)}",
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
            .add_node("stakeholder_analysis", run_stakeholder_analysis)
            .add_node("source_discovery", run_source_discovery)
            .add_node("requirements_gathering", run_requirements_gathering)
            .add_node("consolidate", consolidate_results)
            .add_node("handle_error", handle_error)
            .set_entry("stakeholder_analysis")
            .add_conditional("stakeholder_analysis", route_after_stakeholder, {
                "source_discovery": "source_discovery",
                "handle_error": "handle_error"
            })
            .add_conditional("source_discovery", route_after_source, {
                "requirements_gathering": "requirements_gathering",
                "handle_error": "handle_error"
            })
            .add_conditional("requirements_gathering", route_after_requirements, {
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
        """Execute the discovery cluster workflow."""
        # Validate required inputs
        required = ["organization", "project_description"]
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
        initial_state = DiscoveryState(
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
            discovered_sources=[],
            source_assessments={},
            stakeholder_map={},
            requirements=[]
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

            # Extract the discovery report
            outputs = final_state.get("outputs", {})
            discovery_report = outputs.get("discovery_report", {})

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
                    "description": f"Discovery cluster execution failed: {str(e)}",
                    "priority": "high"
                }],
                errors=[str(e)]
            )

    def _get_next_action(self, state: DiscoveryState) -> Optional[str]:
        """Determine suggested next action based on state."""
        if state.get("requires_human_review"):
            return "await_human_review"
        if state.get("errors"):
            return "handle_errors"
        if state.get("current_step") == "complete":
            return "proceed_to_data_architecture"
        return None

    def get_report(self, outputs: Dict[str, Any]) -> Optional[DiscoveryReport]:
        """Extract and validate the discovery report from outputs."""
        report_data = outputs.get("discovery_report")
        if report_data:
            return DiscoveryReport(**report_data)
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


# Convenience function for running discovery
async def run_discovery(
    llm: BaseChatModel,
    engagement_id: str,
    organization: str,
    project_description: str,
    tech_stack: Optional[List[str]] = None,
    known_systems: Optional[List[Dict[str, Any]]] = None,
    initial_contacts: Optional[List[Dict[str, Any]]] = None,
    business_processes: Optional[List[Dict[str, Any]]] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> AgentOutput:
    """
    Convenience function to run the discovery cluster.

    Args:
        llm: The language model to use
        engagement_id: Unique identifier for the engagement
        organization: Name of the client organization
        project_description: Description of the project
        tech_stack: Known technology stack
        known_systems: Known systems in the organization
        initial_contacts: Initial stakeholder contacts
        business_processes: Business processes to analyze
        additional_context: Additional context information

    Returns:
        AgentOutput with the discovery report
    """
    cluster = DiscoveryCluster(llm=llm)

    context = {
        "organization": organization,
        "project_description": project_description,
        "tech_stack": tech_stack or [],
        "known_systems": known_systems or [],
        "initial_contacts": initial_contacts or [],
        "business_processes": business_processes or [],
        **(additional_context or {})
    }

    input_data = AgentInput(
        engagement_id=engagement_id,
        phase="discovery",
        context=context
    )

    return await cluster.run(input_data)
