"""
Stakeholder Analysis Agent

Analyzes stakeholder requirements, maps business processes,
and identifies key users and their needs.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
from agent_framework.state_management import (
    DiscoveryState,
    Decision,
    add_decision,
    mark_for_review,
)
from agent_framework.graph_builder import WorkflowBuilder
from agent_framework.prompts import PromptTemplate, PromptLibrary, build_context_string


# Stakeholder-specific prompt templates
STAKEHOLDER_ANALYSIS_SYSTEM = PromptTemplate("""You are a Stakeholder Analysis Agent in the Open Forge platform.

Your role is to analyze stakeholder requirements and map business processes for data engagements.

Engagement ID: $engagement_id
Phase: $phase

Your capabilities:
- Identify key stakeholders and their roles
- Analyze business requirements and pain points
- Map business processes and workflows
- Determine data needs for each stakeholder group
- Assess organizational readiness for data initiatives

Guidelines:
- Ask clarifying questions when requirements are ambiguous
- Document assumptions explicitly
- Flag stakeholders with conflicting requirements for human review
- Provide confidence scores for your assessments
- Consider both technical and non-technical stakeholders

Current context:
$context
""")

IDENTIFY_STAKEHOLDERS = PromptTemplate("""Analyze the provided information to identify key stakeholders.

Organization: $organization
Project description: $project_description
Initial contacts: $initial_contacts

For each stakeholder identified, provide:
1. Name/Role
2. Department/Team
3. Primary responsibilities
4. Data needs
5. Success criteria
6. Influence level (high/medium/low)
7. Engagement priority (high/medium/low)

Output as a structured JSON array of stakeholder objects.
""")

MAP_BUSINESS_PROCESS = PromptTemplate("""Map the business process described below.

Process name: $process_name
Description: $description
Stakeholders involved: $stakeholders

Identify:
1. Process steps (in order)
2. Decision points
3. Data inputs required at each step
4. Data outputs produced
5. Systems/tools involved
6. Pain points and bottlenecks
7. Improvement opportunities

Output as a structured process map in JSON format.
""")

ANALYZE_REQUIREMENTS = PromptTemplate("""Analyze the requirements from the stakeholder interview.

Stakeholder: $stakeholder_name
Role: $stakeholder_role
Interview notes: $interview_notes

Extract:
1. Explicit requirements (directly stated)
2. Implicit requirements (inferred from context)
3. Constraints and limitations
4. Dependencies on other systems/teams
5. Timeline expectations
6. Success metrics

Output as a structured requirements object in JSON format.
""")


class StakeholderAnalysisAgent(BaseOpenForgeAgent):
    """
    Agent for analyzing stakeholder requirements and mapping business processes.

    This agent:
    - Identifies key stakeholders in the organization
    - Conducts stakeholder interviews (virtual or guided)
    - Maps business processes and workflows
    - Documents requirements and success criteria
    - Identifies potential conflicts or gaps
    """

    def __init__(
        self,
        llm: BaseChatModel,
        memory: Optional[MemorySaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(llm, memory, config)
        self._register_prompts()

    def _register_prompts(self) -> None:
        """Register stakeholder-specific prompts with the library."""
        PromptLibrary.register("stakeholder_analysis_system", STAKEHOLDER_ANALYSIS_SYSTEM)
        PromptLibrary.register("identify_stakeholders", IDENTIFY_STAKEHOLDERS)
        PromptLibrary.register("map_business_process", MAP_BUSINESS_PROCESS)
        PromptLibrary.register("analyze_requirements", ANALYZE_REQUIREMENTS)

    @property
    def name(self) -> str:
        return "stakeholder_analysis_agent"

    @property
    def description(self) -> str:
        return (
            "Analyzes stakeholder requirements, maps business processes, "
            "and identifies key users and their needs for data engagements."
        )

    @property
    def required_inputs(self) -> List[str]:
        return ["organization", "project_description"]

    @property
    def output_keys(self) -> List[str]:
        return [
            "stakeholders",
            "business_processes",
            "requirements",
            "stakeholder_map",
            "conflicts",
            "recommendations"
        ]

    @property
    def state_class(self) -> Type[DiscoveryState]:
        return DiscoveryState

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return STAKEHOLDER_ANALYSIS_SYSTEM.template

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for stakeholder analysis."""
        builder = WorkflowBuilder(DiscoveryState)

        # Define workflow nodes
        async def identify_stakeholders(state: DiscoveryState) -> Dict[str, Any]:
            """Identify key stakeholders from initial context."""
            context = state.get("agent_context", {})

            prompt = PromptLibrary.format(
                "identify_stakeholders",
                organization=context.get("organization", "Unknown"),
                project_description=context.get("project_description", ""),
                initial_contacts=json.dumps(context.get("initial_contacts", []))
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                stakeholders = json.loads(response.content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                stakeholders = self._extract_json_from_response(response.content)

            # Create decision for stakeholder identification
            decision = add_decision(
                state,
                decision_type="stakeholder_identification",
                description=f"Identified {len(stakeholders)} key stakeholders",
                confidence=0.8 if stakeholders else 0.3,
                reasoning="Based on initial project context and contacts provided"
            )

            return {
                "outputs": {"stakeholders": stakeholders},
                "stakeholder_map": {"identified_stakeholders": stakeholders},
                "decisions": [decision],
                "current_step": "stakeholders_identified"
            }

        async def map_processes(state: DiscoveryState) -> Dict[str, Any]:
            """Map business processes based on stakeholder input."""
            context = state.get("agent_context", {})
            outputs = state.get("outputs", {})
            stakeholders = outputs.get("stakeholders", [])

            processes = []
            process_descriptions = context.get("business_processes", [])

            for proc in process_descriptions:
                prompt = PromptLibrary.format(
                    "map_business_process",
                    process_name=proc.get("name", "Unknown Process"),
                    description=proc.get("description", ""),
                    stakeholders=json.dumps([s.get("name", "") for s in stakeholders])
                )

                messages = [
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = await self.llm.ainvoke(messages)

                try:
                    process_map = json.loads(response.content)
                except json.JSONDecodeError:
                    process_map = self._extract_json_from_response(response.content)

                processes.append(process_map)

            decision = add_decision(
                state,
                decision_type="process_mapping",
                description=f"Mapped {len(processes)} business processes",
                confidence=0.75 if processes else 0.4,
                reasoning="Derived from stakeholder input and process descriptions"
            )

            return {
                "outputs": {"business_processes": processes},
                "decisions": [decision],
                "current_step": "processes_mapped"
            }

        async def analyze_requirements_node(state: DiscoveryState) -> Dict[str, Any]:
            """Analyze and consolidate requirements from stakeholders."""
            context = state.get("agent_context", {})
            outputs = state.get("outputs", {})
            stakeholders = outputs.get("stakeholders", [])

            requirements_list = []
            interview_data = context.get("stakeholder_interviews", [])

            for interview in interview_data:
                stakeholder = next(
                    (s for s in stakeholders if s.get("name") == interview.get("stakeholder_name")),
                    {"name": interview.get("stakeholder_name", "Unknown"), "role": "Unknown"}
                )

                prompt = PromptLibrary.format(
                    "analyze_requirements",
                    stakeholder_name=stakeholder.get("name", "Unknown"),
                    stakeholder_role=stakeholder.get("role", "Unknown"),
                    interview_notes=interview.get("notes", "")
                )

                messages = [
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = await self.llm.ainvoke(messages)

                try:
                    reqs = json.loads(response.content)
                except json.JSONDecodeError:
                    reqs = self._extract_json_from_response(response.content)

                requirements_list.append({
                    "stakeholder": stakeholder.get("name"),
                    "requirements": reqs
                })

            return {
                "outputs": {"requirements": requirements_list},
                "requirements": requirements_list,
                "current_step": "requirements_analyzed"
            }

        async def identify_conflicts(state: DiscoveryState) -> Dict[str, Any]:
            """Identify conflicts and gaps in requirements."""
            outputs = state.get("outputs", {})
            requirements = outputs.get("requirements", [])
            stakeholders = outputs.get("stakeholders", [])

            # Analyze for conflicts
            prompt = f"""Analyze the following requirements from different stakeholders and identify:
1. Conflicting requirements (where stakeholders want different things)
2. Gaps in requirements (missing information)
3. Dependencies between requirements
4. Prioritization recommendations

Stakeholders: {json.dumps(stakeholders)}
Requirements: {json.dumps(requirements)}

Output as JSON with keys: conflicts, gaps, dependencies, priority_recommendations
"""
            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                analysis = self._extract_json_from_response(response.content)

            conflicts = analysis.get("conflicts", [])
            requires_review = len(conflicts) > 0

            review_items = []
            if requires_review:
                for conflict in conflicts:
                    review_items.append(
                        mark_for_review(
                            state,
                            item_type="requirement_conflict",
                            item_id=f"conflict_{len(review_items)}",
                            description=conflict.get("description", str(conflict)),
                            priority="high" if conflict.get("severity") == "high" else "medium"
                        )
                    )

            decision = add_decision(
                state,
                decision_type="conflict_analysis",
                description=f"Found {len(conflicts)} conflicts requiring resolution",
                confidence=0.85,
                reasoning="Cross-referenced requirements from all stakeholders",
                requires_approval=requires_review
            )

            return {
                "outputs": {
                    "conflicts": conflicts,
                    "gaps": analysis.get("gaps", []),
                    "dependencies": analysis.get("dependencies", []),
                    "recommendations": analysis.get("priority_recommendations", [])
                },
                "decisions": [decision],
                "requires_human_review": requires_review,
                "review_items": review_items,
                "current_step": "conflicts_identified"
            }

        async def generate_stakeholder_map(state: DiscoveryState) -> Dict[str, Any]:
            """Generate comprehensive stakeholder map."""
            outputs = state.get("outputs", {})

            stakeholder_map = {
                "stakeholders": outputs.get("stakeholders", []),
                "business_processes": outputs.get("business_processes", []),
                "requirements_by_stakeholder": outputs.get("requirements", []),
                "conflicts": outputs.get("conflicts", []),
                "gaps": outputs.get("gaps", []),
                "recommendations": outputs.get("recommendations", []),
                "generated_at": datetime.utcnow().isoformat()
            }

            # Calculate overall confidence
            decisions = state.get("decisions", [])
            avg_confidence = (
                sum(d.confidence for d in decisions) / len(decisions)
                if decisions else 0.5
            )

            decision = add_decision(
                state,
                decision_type="stakeholder_map_generation",
                description="Generated comprehensive stakeholder map",
                confidence=avg_confidence,
                reasoning="Consolidated all stakeholder analysis outputs"
            )

            return {
                "outputs": {"stakeholder_map": stakeholder_map},
                "stakeholder_map": stakeholder_map,
                "decisions": [decision],
                "current_step": "complete"
            }

        def route_after_conflicts(state: DiscoveryState) -> str:
            """Route based on whether conflicts require human review."""
            if state.get("requires_human_review"):
                return "await_review"
            return "generate_map"

        async def await_human_review(state: DiscoveryState) -> Dict[str, Any]:
            """Wait for human review of conflicts."""
            return {
                "current_step": "awaiting_human_review"
            }

        # Build the workflow
        graph = (builder
            .add_node("identify_stakeholders", identify_stakeholders)
            .add_node("map_processes", map_processes)
            .add_node("analyze_requirements", analyze_requirements_node)
            .add_node("identify_conflicts", identify_conflicts)
            .add_node("await_review", await_human_review)
            .add_node("generate_map", generate_stakeholder_map)
            .set_entry("identify_stakeholders")
            .add_edge("identify_stakeholders", "map_processes")
            .add_edge("map_processes", "analyze_requirements")
            .add_edge("analyze_requirements", "identify_conflicts")
            .add_conditional("identify_conflicts", route_after_conflicts, {
                "await_review": "await_review",
                "generate_map": "generate_map"
            })
            .add_edge("await_review", "END")
            .add_edge("generate_map", "END")
            .build())

        return graph

    def get_tools(self) -> List[Any]:
        """Return list of tools this agent uses."""
        # Future: Add tools for CRM integration, calendar access, etc.
        return []

    def _extract_json_from_response(self, response: str) -> Any:
        """Extract JSON from an LLM response that may contain other text."""
        # Try to find JSON array or object in the response
        import re

        # Look for JSON array
        array_match = re.search(r'\[[\s\S]*\]', response)
        if array_match:
            try:
                return json.loads(array_match.group())
            except json.JSONDecodeError:
                pass

        # Look for JSON object
        object_match = re.search(r'\{[\s\S]*\}', response)
        if object_match:
            try:
                return json.loads(object_match.group())
            except json.JSONDecodeError:
                pass

        # Return empty structure if no valid JSON found
        return {}
