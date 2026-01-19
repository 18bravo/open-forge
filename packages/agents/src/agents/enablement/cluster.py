"""
Enablement Agent Cluster

Orchestrates the enablement agents for comprehensive documentation,
training, and support content generation.
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
    EnablementState,
    Decision,
    Message,
    add_decision,
    mark_for_review,
)
from agent_framework.graph_builder import WorkflowBuilder
from agent_framework.prompts import PromptTemplate, PromptLibrary

from contracts.agent_interface import AgentInput, AgentOutput

from .documentation_agent import DocumentationAgent
from .training_agent import TrainingAgent
from .support_agent import SupportAgent


class EnablementPhase(str, Enum):
    """Phases of the enablement content generation process."""
    DOCUMENTATION = "documentation"
    TRAINING = "training"
    SUPPORT = "support"
    CONSOLIDATION = "consolidation"
    COMPLETE = "complete"


class EnablementReport(BaseModel):
    """Consolidated enablement report output."""
    engagement_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Documentation outputs
    api_documentation: Dict[str, Any] = Field(default_factory=dict)
    user_guides: List[Dict[str, Any]] = Field(default_factory=list)
    runbooks: List[Dict[str, Any]] = Field(default_factory=list)

    # Training outputs
    training_materials: List[Dict[str, Any]] = Field(default_factory=list)
    tutorials: List[Dict[str, Any]] = Field(default_factory=list)
    quickstart_guides: List[Dict[str, Any]] = Field(default_factory=list)

    # Support outputs
    faq_documents: List[Dict[str, Any]] = Field(default_factory=list)
    troubleshooting_guides: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge_base_articles: List[Dict[str, Any]] = Field(default_factory=list)

    # Overall metrics
    confidence_score: float = 0.0
    requires_human_review: bool = False
    review_items: List[Dict[str, Any]] = Field(default_factory=list)
    all_decisions: List[Dict[str, Any]] = Field(default_factory=list)

    # Next steps
    recommended_actions: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)


# Cluster orchestration prompts
ENABLEMENT_ORCHESTRATOR_SYSTEM = PromptTemplate("""You are the Enablement Cluster Orchestrator in the Open Forge platform.

Your role is to coordinate the enablement agents and produce comprehensive enablement content.

Engagement ID: $engagement_id
Phase: $phase

Enablement agents under your coordination:
1. Documentation Agent - Generates API docs, user guides, and runbooks
2. Training Agent - Creates training curricula, tutorials, and quickstart guides
3. Support Agent - Produces FAQs, troubleshooting guides, and knowledge base articles

Your responsibilities:
- Orchestrate agent execution in the correct order
- Pass relevant context between agents (ontology, previous outputs, etc.)
- Consolidate outputs into a unified enablement package
- Identify gaps and required human reviews
- Ensure consistency across all enablement materials

Current context:
$context
""")

ENABLEMENT_CONSOLIDATION_PROMPT = PromptTemplate("""Consolidate all enablement content into a comprehensive summary.

Documentation Results:
$documentation_results

Training Results:
$training_results

Support Results:
$support_results

Create a consolidated summary that includes:
1. Enablement readiness assessment
2. Key materials generated
3. Cross-references between content types
4. Deployment recommendations
5. Gaps or areas needing attention
6. Recommended actions for enablement team
7. Content maintenance recommendations

Output as a structured JSON summary.
""")


class EnablementCluster:
    """
    Orchestrates the enablement agent cluster.

    The enablement cluster coordinates three specialized agents:
    1. DocumentationAgent - API docs, user guides, runbooks
    2. TrainingAgent - Curricula, tutorials, quickstart guides
    3. SupportAgent - FAQs, troubleshooting guides, KB articles

    The cluster manages the workflow between agents, passing outputs from
    one agent as context to the next, and produces a consolidated
    enablement package.
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
        self.documentation_agent = DocumentationAgent(
            llm=llm,
            memory=memory,
            config=config
        )
        self.training_agent = TrainingAgent(
            llm=llm,
            memory=memory,
            config=config
        )
        self.support_agent = SupportAgent(
            llm=llm,
            memory=memory,
            config=config
        )

        self._graph: Optional[StateGraph] = None
        self._compiled_graph = None

        # Register prompts
        PromptLibrary.register("enablement_orchestrator_system", ENABLEMENT_ORCHESTRATOR_SYSTEM)
        PromptLibrary.register("enablement_consolidation_prompt", ENABLEMENT_CONSOLIDATION_PROMPT)

    @property
    def name(self) -> str:
        return "enablement_cluster"

    @property
    def description(self) -> str:
        return (
            "Orchestrates enablement agents to generate documentation, "
            "training materials, and support content."
        )

    @property
    def agents(self) -> List[BaseOpenForgeAgent]:
        """Return list of agents in this cluster."""
        return [
            self.documentation_agent,
            self.training_agent,
            self.support_agent
        ]

    def build_graph(self) -> StateGraph:
        """Build the cluster orchestration workflow."""
        builder = WorkflowBuilder(EnablementState)

        async def run_documentation(state: EnablementState) -> Dict[str, Any]:
            """Run the documentation agent."""
            context = state.get("agent_context", {})

            # Create input for documentation agent
            agent_input = AgentInput(
                engagement_id=state.get("engagement_id", ""),
                phase=EnablementPhase.DOCUMENTATION.value,
                context={
                    "ontology_schema": context.get("ontology_schema", ""),
                    "system_architecture": context.get("system_architecture", {}),
                    "target_audiences": context.get("target_audiences", []),
                    "runbook_types": context.get("runbook_types", [])
                },
                previous_outputs=None,
                human_inputs=context.get("human_inputs", [])
            )

            # Run the agent
            output = await self.documentation_agent.run(agent_input)

            # Handle errors
            if not output.success:
                return {
                    "errors": output.errors or ["Documentation generation failed"],
                    "current_step": "documentation_failed"
                }

            # Store outputs in state
            return {
                "outputs": output.outputs,
                "api_documentation": output.outputs.get("api_documentation", {}),
                "user_guides": output.outputs.get("user_guides", []),
                "runbooks": output.outputs.get("runbooks", []),
                "decisions": [Decision(**d) for d in output.decisions],
                "requires_human_review": output.requires_human_review,
                "review_items": output.review_items or [],
                "current_step": "documentation_complete"
            }

        async def run_training(state: EnablementState) -> Dict[str, Any]:
            """Run the training agent."""
            context = state.get("agent_context", {})
            current_outputs = state.get("outputs", {})

            # Pass documentation outputs as context for training
            agent_input = AgentInput(
                engagement_id=state.get("engagement_id", ""),
                phase=EnablementPhase.TRAINING.value,
                context={
                    "ontology_schema": context.get("ontology_schema", ""),
                    "system_features": context.get("system_features", []),
                    "api_documentation": state.get("api_documentation", {}),
                    "skill_levels": context.get("skill_levels", []),
                    "tutorial_topics": context.get("tutorial_topics", []),
                    "quickstart_scenarios": context.get("quickstart_scenarios", [])
                },
                previous_outputs={
                    "documentation": {
                        "api_documentation": state.get("api_documentation", {}),
                        "user_guides": state.get("user_guides", []),
                        "runbooks": state.get("runbooks", [])
                    },
                    **current_outputs
                },
                human_inputs=context.get("human_inputs", [])
            )

            output = await self.training_agent.run(agent_input)

            if not output.success:
                return {
                    "errors": output.errors or ["Training content generation failed"],
                    "current_step": "training_failed"
                }

            # Merge outputs
            merged_outputs = {**current_outputs, **output.outputs}

            return {
                "outputs": merged_outputs,
                "training_materials": output.outputs.get("training_materials", []),
                "tutorials": output.outputs.get("tutorials", []),
                "quickstart_guides": output.outputs.get("quickstart_guides", []),
                "decisions": [Decision(**d) for d in output.decisions],
                "requires_human_review": (
                    state.get("requires_human_review", False) or output.requires_human_review
                ),
                "review_items": output.review_items or [],
                "current_step": "training_complete"
            }

        async def run_support(state: EnablementState) -> Dict[str, Any]:
            """Run the support agent."""
            context = state.get("agent_context", {})
            current_outputs = state.get("outputs", {})

            # Pass previous outputs as context for support content
            agent_input = AgentInput(
                engagement_id=state.get("engagement_id", ""),
                phase=EnablementPhase.SUPPORT.value,
                context={
                    "ontology_schema": context.get("ontology_schema", ""),
                    "system_features": context.get("system_features", []),
                    "system_architecture": context.get("system_architecture", {}),
                    "common_tasks": context.get("common_tasks", []),
                    "historical_issues": context.get("historical_issues", []),
                    "error_codes": context.get("error_codes", []),
                    "user_personas": context.get("user_personas", []),
                    "kb_topics": context.get("kb_topics", [])
                },
                previous_outputs={
                    "documentation": {
                        "api_documentation": state.get("api_documentation", {}),
                        "user_guides": state.get("user_guides", [])
                    },
                    "training": {
                        "tutorials": state.get("tutorials", []),
                        "quickstart_guides": state.get("quickstart_guides", [])
                    },
                    **current_outputs
                },
                human_inputs=context.get("human_inputs", [])
            )

            output = await self.support_agent.run(agent_input)

            if not output.success:
                return {
                    "errors": output.errors or ["Support content generation failed"],
                    "current_step": "support_failed"
                }

            # Merge outputs
            merged_outputs = {**current_outputs, **output.outputs}

            return {
                "outputs": merged_outputs,
                "faq_documents": output.outputs.get("faq_documents", []),
                "troubleshooting_guides": output.outputs.get("troubleshooting_guides", []),
                "knowledge_base_articles": output.outputs.get("knowledge_base_articles", []),
                "decisions": [Decision(**d) for d in output.decisions],
                "requires_human_review": (
                    state.get("requires_human_review", False) or output.requires_human_review
                ),
                "review_items": output.review_items or [],
                "current_step": "support_complete"
            }

        async def consolidate_results(state: EnablementState) -> Dict[str, Any]:
            """Consolidate all enablement results into a report."""
            outputs = state.get("outputs", {})

            # Create consolidation prompt
            prompt = PromptLibrary.format(
                "enablement_consolidation_prompt",
                documentation_results=json.dumps({
                    "api_documentation": state.get("api_documentation", {}),
                    "user_guides": state.get("user_guides", []),
                    "runbooks": state.get("runbooks", [])
                }, default=str)[:3000],
                training_results=json.dumps({
                    "training_materials": state.get("training_materials", []),
                    "tutorials": state.get("tutorials", []),
                    "quickstart_guides": state.get("quickstart_guides", [])
                }, default=str)[:3000],
                support_results=json.dumps({
                    "faq_documents": state.get("faq_documents", []),
                    "troubleshooting_guides": state.get("troubleshooting_guides", []),
                    "knowledge_base_articles": state.get("knowledge_base_articles", [])
                }, default=str)[:3000]
            )

            messages = [
                SystemMessage(content=PromptLibrary.format(
                    "enablement_orchestrator_system",
                    engagement_id=state.get("engagement_id", ""),
                    phase=EnablementPhase.CONSOLIDATION.value,
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
                "enablement_report": {
                    "engagement_id": state.get("engagement_id", ""),
                    "generated_at": datetime.utcnow().isoformat(),
                    "summary": summary,
                    # Documentation
                    "api_documentation": state.get("api_documentation", {}),
                    "user_guides": state.get("user_guides", []),
                    "runbooks": state.get("runbooks", []),
                    # Training
                    "training_materials": state.get("training_materials", []),
                    "tutorials": state.get("tutorials", []),
                    "quickstart_guides": state.get("quickstart_guides", []),
                    # Support
                    "faq_documents": state.get("faq_documents", []),
                    "troubleshooting_guides": state.get("troubleshooting_guides", []),
                    "knowledge_base_articles": state.get("knowledge_base_articles", []),
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
                decision_type="enablement_consolidation",
                description="Consolidated enablement results into final report",
                confidence=avg_confidence,
                reasoning="Aggregated outputs from all enablement agents"
            )

            return {
                "outputs": {**outputs, **report},
                "decisions": [decision],
                "current_step": "complete"
            }

        def route_after_documentation(state: EnablementState) -> str:
            """Route after documentation phase."""
            if state.get("errors"):
                return "handle_error"
            return "training"

        def route_after_training(state: EnablementState) -> str:
            """Route after training phase."""
            if state.get("errors"):
                return "handle_error"
            return "support"

        def route_after_support(state: EnablementState) -> str:
            """Route after support phase."""
            if state.get("errors"):
                return "handle_error"
            return "consolidate"

        async def handle_error(state: EnablementState) -> Dict[str, Any]:
            """Handle errors in the workflow."""
            errors = state.get("errors", [])

            review_items = state.get("review_items", [])
            review_items.append(
                mark_for_review(
                    state,
                    item_type="cluster_error",
                    item_id="enablement_cluster_error",
                    description=f"Enablement cluster encountered errors: {', '.join(errors)}",
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
            .add_node("documentation", run_documentation)
            .add_node("training", run_training)
            .add_node("support", run_support)
            .add_node("consolidate", consolidate_results)
            .add_node("handle_error", handle_error)
            .set_entry("documentation")
            .add_conditional("documentation", route_after_documentation, {
                "training": "training",
                "handle_error": "handle_error"
            })
            .add_conditional("training", route_after_training, {
                "support": "support",
                "handle_error": "handle_error"
            })
            .add_conditional("support", route_after_support, {
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
        """Execute the enablement cluster workflow."""
        # Validate required inputs
        required = ["ontology_schema"]
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
        initial_state = EnablementState(
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
            # Documentation state
            api_documentation={},
            user_guides=[],
            runbooks=[],
            # Training state
            training_materials=[],
            tutorials=[],
            quickstart_guides=[],
            # Support state
            faq_documents=[],
            troubleshooting_guides=[],
            knowledge_base_articles=[],
            # Ontology integration
            ontology_entities=[],
            ontology_relationships=[]
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

            # Extract the enablement report
            outputs = final_state.get("outputs", {})
            enablement_report = outputs.get("enablement_report", {})

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
                    "description": f"Enablement cluster execution failed: {str(e)}",
                    "priority": "high"
                }],
                errors=[str(e)]
            )

    def _get_next_action(self, state: EnablementState) -> Optional[str]:
        """Determine suggested next action based on state."""
        if state.get("requires_human_review"):
            return "await_human_review"
        if state.get("errors"):
            return "handle_errors"
        if state.get("current_step") == "complete":
            return "publish_enablement_content"
        return None

    def get_report(self, outputs: Dict[str, Any]) -> Optional[EnablementReport]:
        """Extract and validate the enablement report from outputs."""
        report_data = outputs.get("enablement_report")
        if report_data:
            return EnablementReport(**report_data)
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


# Convenience function for running enablement cluster
async def run_enablement(
    llm: BaseChatModel,
    engagement_id: str,
    ontology_schema: str,
    system_architecture: Optional[Dict[str, Any]] = None,
    system_features: Optional[List[str]] = None,
    target_audiences: Optional[List[Dict[str, Any]]] = None,
    common_tasks: Optional[List[str]] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> AgentOutput:
    """
    Convenience function to run the enablement cluster.

    Args:
        llm: The language model to use
        engagement_id: Unique identifier for the engagement
        ontology_schema: LinkML ontology schema (YAML string)
        system_architecture: System architecture description
        system_features: List of system features
        target_audiences: Target audiences for documentation
        common_tasks: Common user tasks
        additional_context: Additional context information

    Returns:
        AgentOutput with the enablement report
    """
    cluster = EnablementCluster(llm=llm)

    context = {
        "ontology_schema": ontology_schema,
        "system_architecture": system_architecture or {},
        "system_features": system_features or [],
        "target_audiences": target_audiences or [],
        "common_tasks": common_tasks or [],
        **(additional_context or {})
    }

    input_data = AgentInput(
        engagement_id=engagement_id,
        phase="enablement",
        context=context
    )

    return await cluster.run(input_data)


# Convenience function for creating the cluster
def create_enablement_cluster(
    llm: BaseChatModel,
    memory: Optional[MemorySaver] = None,
    config: Optional[Dict[str, Any]] = None
) -> EnablementCluster:
    """Create a configured EnablementCluster instance."""
    default_config = {
        "max_iterations": 3,
        "validation_threshold": 0.8
    }
    if config:
        default_config.update(config)
    return EnablementCluster(llm, memory, default_config)
