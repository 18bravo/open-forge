"""
Requirements Gathering Agent

Synthesizes requirements from stakeholder input,
prioritizes features, and identifies integration needs.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from enum import Enum
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


class RequirementPriority(str, Enum):
    """Priority levels for requirements."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RequirementType(str, Enum):
    """Types of requirements."""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    DATA = "data"
    INTEGRATION = "integration"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"


class RequirementStatus(str, Enum):
    """Status of requirements."""
    DRAFT = "draft"
    VALIDATED = "validated"
    APPROVED = "approved"
    DEFERRED = "deferred"
    REJECTED = "rejected"


# Requirements-specific prompt templates
REQUIREMENTS_SYSTEM = PromptTemplate("""You are a Requirements Gathering Agent in the Open Forge platform.

Your role is to synthesize, prioritize, and document requirements for data engagements.

Engagement ID: $engagement_id
Phase: $phase

Your capabilities:
- Consolidate requirements from multiple stakeholders
- Identify functional and non-functional requirements
- Prioritize features using MoSCoW or similar frameworks
- Detect integration requirements and dependencies
- Ensure requirements are clear, measurable, and testable

Guidelines:
- Use SMART criteria for requirements (Specific, Measurable, Achievable, Relevant, Time-bound)
- Document acceptance criteria for each requirement
- Flag ambiguous or conflicting requirements
- Consider technical feasibility and constraints
- Trace requirements to stakeholder needs

Current context:
$context
""")

SYNTHESIZE_REQUIREMENTS = PromptTemplate("""Synthesize requirements from the following stakeholder inputs.

Stakeholder requirements: $stakeholder_requirements
Business processes: $business_processes
Data sources available: $data_sources

Consolidate into a unified requirements list with:
1. Requirement ID
2. Title
3. Description
4. Type (functional, non_functional, data, integration, security, compliance, performance)
5. Priority (critical, high, medium, low)
6. Source stakeholders
7. Acceptance criteria
8. Dependencies
9. Estimated complexity (1-5)

Output as a JSON array of requirement objects.
""")

PRIORITIZE_REQUIREMENTS = PromptTemplate("""Prioritize the following requirements using MoSCoW framework.

Requirements: $requirements
Project constraints: $constraints
Timeline: $timeline
Available resources: $resources

Categorize each requirement as:
- Must Have: Critical for project success
- Should Have: Important but not critical
- Could Have: Nice to have if time permits
- Won't Have: Out of scope for current phase

For each requirement, provide:
1. MoSCoW category
2. Priority score (1-10)
3. Justification
4. Dependencies that affect priority
5. Risk if not implemented

Output as JSON with prioritized_requirements array.
""")

IDENTIFY_INTEGRATIONS = PromptTemplate("""Identify integration requirements based on the following.

Requirements: $requirements
Data sources: $data_sources
Existing systems: $existing_systems
Target architecture: $target_architecture

For each integration need, document:
1. Integration name
2. Source system
3. Target system
4. Data flow direction
5. Integration pattern (batch, real-time, event-driven)
6. Data volume estimate
7. Frequency
8. Technical requirements
9. Security requirements
10. Dependencies

Output as a JSON array of integration requirement objects.
""")

VALIDATE_REQUIREMENTS = PromptTemplate("""Validate the following requirements for completeness and quality.

Requirements: $requirements
Validation criteria:
- Clear and unambiguous
- Measurable and testable
- Achievable within constraints
- Relevant to business goals
- Time-bound with deadlines

For each requirement, assess:
1. Clarity score (0-1)
2. Completeness score (0-1)
3. Testability score (0-1)
4. Issues found
5. Suggested improvements
6. Overall quality (pass/needs_work/fail)

Output as JSON with validation_results.
""")

GENERATE_REQUIREMENTS_DOC = PromptTemplate("""Generate a requirements document summary.

Prioritized requirements: $prioritized_requirements
Integration requirements: $integration_requirements
Validation results: $validation_results
Project context: $project_context

Create a structured summary including:
1. Executive summary
2. Scope and objectives
3. Functional requirements (grouped by domain)
4. Non-functional requirements
5. Integration requirements
6. Data requirements
7. Constraints and assumptions
8. Dependencies
9. Risks and mitigations
10. Success criteria

Output as a structured JSON document.
""")


class RequirementsGatheringAgent(BaseOpenForgeAgent):
    """
    Agent for synthesizing and prioritizing requirements.

    This agent:
    - Consolidates requirements from stakeholder analysis
    - Prioritizes features using MoSCoW framework
    - Identifies integration requirements
    - Validates requirement quality
    - Produces a comprehensive requirements document
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
        """Register requirements-specific prompts with the library."""
        PromptLibrary.register("requirements_system", REQUIREMENTS_SYSTEM)
        PromptLibrary.register("synthesize_requirements", SYNTHESIZE_REQUIREMENTS)
        PromptLibrary.register("prioritize_requirements", PRIORITIZE_REQUIREMENTS)
        PromptLibrary.register("identify_integrations", IDENTIFY_INTEGRATIONS)
        PromptLibrary.register("validate_requirements", VALIDATE_REQUIREMENTS)
        PromptLibrary.register("generate_requirements_doc", GENERATE_REQUIREMENTS_DOC)

    @property
    def name(self) -> str:
        return "requirements_gathering_agent"

    @property
    def description(self) -> str:
        return (
            "Synthesizes requirements from stakeholder input, "
            "prioritizes features, and identifies integration needs."
        )

    @property
    def required_inputs(self) -> List[str]:
        return ["stakeholder_requirements"]

    @property
    def output_keys(self) -> List[str]:
        return [
            "synthesized_requirements",
            "prioritized_requirements",
            "integration_requirements",
            "validation_results",
            "requirements_document"
        ]

    @property
    def state_class(self) -> Type[DiscoveryState]:
        return DiscoveryState

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return REQUIREMENTS_SYSTEM.template

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for requirements gathering."""
        builder = WorkflowBuilder(DiscoveryState)

        async def synthesize_requirements(state: DiscoveryState) -> Dict[str, Any]:
            """Synthesize requirements from stakeholder inputs."""
            context = state.get("agent_context", {})

            # Get stakeholder requirements from previous agents
            previous_outputs = context.get("previous_outputs", {})
            stakeholder_map = previous_outputs.get("stakeholder_map", {})
            source_recommendations = previous_outputs.get("source_recommendations", [])

            # Get requirements from context or stakeholder map
            stakeholder_reqs = context.get(
                "stakeholder_requirements",
                stakeholder_map.get("requirements_by_stakeholder", [])
            )

            # Get business processes
            business_processes = stakeholder_map.get("business_processes", [])

            # Get data sources
            discovered_sources = previous_outputs.get("discovered_sources", [])

            prompt = PromptLibrary.format(
                "synthesize_requirements",
                stakeholder_requirements=json.dumps(stakeholder_reqs),
                business_processes=json.dumps(business_processes),
                data_sources=json.dumps(discovered_sources)
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                requirements = json.loads(response.content)
            except json.JSONDecodeError:
                requirements = self._extract_json_from_response(response.content)

            # Normalize requirement types and priorities
            for req in requirements:
                try:
                    req["type"] = RequirementType(req.get("type", "functional").lower()).value
                except ValueError:
                    req["type"] = RequirementType.FUNCTIONAL.value

                try:
                    req["priority"] = RequirementPriority(req.get("priority", "medium").lower()).value
                except ValueError:
                    req["priority"] = RequirementPriority.MEDIUM.value

                req["status"] = RequirementStatus.DRAFT.value

            decision = add_decision(
                state,
                decision_type="requirements_synthesis",
                description=f"Synthesized {len(requirements)} requirements from stakeholder input",
                confidence=0.75,
                reasoning="Consolidated from stakeholder interviews and business processes"
            )

            return {
                "outputs": {"synthesized_requirements": requirements},
                "requirements": requirements,
                "decisions": [decision],
                "current_step": "requirements_synthesized"
            }

        async def prioritize_requirements(state: DiscoveryState) -> Dict[str, Any]:
            """Prioritize requirements using MoSCoW framework."""
            outputs = state.get("outputs", {})
            context = state.get("agent_context", {})
            requirements = outputs.get("synthesized_requirements", [])

            prompt = PromptLibrary.format(
                "prioritize_requirements",
                requirements=json.dumps(requirements),
                constraints=json.dumps(context.get("constraints", {})),
                timeline=context.get("timeline", "Not specified"),
                resources=json.dumps(context.get("resources", {}))
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                result = json.loads(response.content)
            except json.JSONDecodeError:
                result = self._extract_json_from_response(response.content)

            prioritized = result.get("prioritized_requirements", requirements)

            # Count by MoSCoW category
            moscow_counts = {
                "must_have": 0,
                "should_have": 0,
                "could_have": 0,
                "wont_have": 0
            }
            for req in prioritized:
                category = req.get("moscow_category", "should_have").lower().replace(" ", "_")
                if category in moscow_counts:
                    moscow_counts[category] += 1

            decision = add_decision(
                state,
                decision_type="requirements_prioritization",
                description=f"Prioritized requirements: {moscow_counts['must_have']} must-have, "
                           f"{moscow_counts['should_have']} should-have, "
                           f"{moscow_counts['could_have']} could-have",
                confidence=0.8,
                reasoning="Applied MoSCoW framework based on project constraints and timeline"
            )

            return {
                "outputs": {"prioritized_requirements": prioritized},
                "requirements": prioritized,
                "decisions": [decision],
                "current_step": "requirements_prioritized"
            }

        async def identify_integration_requirements(state: DiscoveryState) -> Dict[str, Any]:
            """Identify integration requirements."""
            outputs = state.get("outputs", {})
            context = state.get("agent_context", {})
            previous_outputs = context.get("previous_outputs", {})

            requirements = outputs.get("prioritized_requirements", [])
            data_sources = previous_outputs.get("discovered_sources", [])
            existing_systems = context.get("existing_systems", [])
            target_arch = context.get("target_architecture", {})

            prompt = PromptLibrary.format(
                "identify_integrations",
                requirements=json.dumps(requirements),
                data_sources=json.dumps(data_sources),
                existing_systems=json.dumps(existing_systems),
                target_architecture=json.dumps(target_arch)
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                integrations = json.loads(response.content)
            except json.JSONDecodeError:
                integrations = self._extract_json_from_response(response.content)

            # Ensure it's a list
            if isinstance(integrations, dict):
                integrations = integrations.get("integrations", [])

            decision = add_decision(
                state,
                decision_type="integration_identification",
                description=f"Identified {len(integrations)} integration requirements",
                confidence=0.75,
                reasoning="Analyzed data flows and system dependencies"
            )

            return {
                "outputs": {"integration_requirements": integrations},
                "decisions": [decision],
                "current_step": "integrations_identified"
            }

        async def validate_requirements(state: DiscoveryState) -> Dict[str, Any]:
            """Validate requirements for quality and completeness."""
            outputs = state.get("outputs", {})
            requirements = outputs.get("prioritized_requirements", [])

            prompt = PromptLibrary.format(
                "validate_requirements",
                requirements=json.dumps(requirements)
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                validation = json.loads(response.content)
            except json.JSONDecodeError:
                validation = self._extract_json_from_response(response.content)

            validation_results = validation.get("validation_results", [])

            # Identify requirements that need work
            needs_work = [
                r for r in validation_results
                if r.get("overall_quality") == "needs_work"
            ]
            failed = [
                r for r in validation_results
                if r.get("overall_quality") == "fail"
            ]

            # Create review items for failed validations
            review_items = []
            for failed_req in failed:
                review_items.append(
                    mark_for_review(
                        state,
                        item_type="requirement_validation",
                        item_id=f"req_{failed_req.get('requirement_id', 'unknown')}",
                        description=f"Requirement '{failed_req.get('requirement_id')}' failed validation: "
                                   f"{', '.join(failed_req.get('issues', ['Unknown issues']))}",
                        priority="high"
                    )
                )

            decision = add_decision(
                state,
                decision_type="requirements_validation",
                description=f"Validated {len(requirements)} requirements: "
                           f"{len(validation_results) - len(needs_work) - len(failed)} passed, "
                           f"{len(needs_work)} need work, {len(failed)} failed",
                confidence=0.85,
                reasoning="Applied SMART criteria and testability checks",
                requires_approval=len(failed) > 0
            )

            return {
                "outputs": {"validation_results": validation_results},
                "decisions": [decision],
                "review_items": review_items,
                "requires_human_review": len(failed) > 0,
                "current_step": "requirements_validated"
            }

        async def generate_document(state: DiscoveryState) -> Dict[str, Any]:
            """Generate comprehensive requirements document."""
            outputs = state.get("outputs", {})
            context = state.get("agent_context", {})

            prompt = PromptLibrary.format(
                "generate_requirements_doc",
                prioritized_requirements=json.dumps(outputs.get("prioritized_requirements", [])),
                integration_requirements=json.dumps(outputs.get("integration_requirements", [])),
                validation_results=json.dumps(outputs.get("validation_results", [])),
                project_context=json.dumps({
                    "organization": context.get("organization", "Unknown"),
                    "project_description": context.get("project_description", ""),
                    "timeline": context.get("timeline", "Not specified"),
                    "constraints": context.get("constraints", {})
                })
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                document = json.loads(response.content)
            except json.JSONDecodeError:
                document = self._extract_json_from_response(response.content)

            # Add metadata
            document["metadata"] = {
                "generated_at": datetime.utcnow().isoformat(),
                "engagement_id": state.get("engagement_id"),
                "phase": state.get("phase"),
                "version": "1.0"
            }

            decision = add_decision(
                state,
                decision_type="document_generation",
                description="Generated comprehensive requirements document",
                confidence=0.9,
                reasoning="Consolidated all requirements analysis into structured document"
            )

            return {
                "outputs": {"requirements_document": document},
                "decisions": [decision],
                "current_step": "complete"
            }

        def route_after_validation(state: DiscoveryState) -> str:
            """Route based on validation results."""
            if state.get("requires_human_review"):
                return "await_review"
            return "generate_document"

        async def await_human_review(state: DiscoveryState) -> Dict[str, Any]:
            """Wait for human review of failed requirements."""
            return {
                "current_step": "awaiting_human_review"
            }

        # Build the workflow
        graph = (builder
            .add_node("synthesize_requirements", synthesize_requirements)
            .add_node("prioritize_requirements", prioritize_requirements)
            .add_node("identify_integrations", identify_integration_requirements)
            .add_node("validate_requirements", validate_requirements)
            .add_node("await_review", await_human_review)
            .add_node("generate_document", generate_document)
            .set_entry("synthesize_requirements")
            .add_edge("synthesize_requirements", "prioritize_requirements")
            .add_edge("prioritize_requirements", "identify_integrations")
            .add_edge("identify_integrations", "validate_requirements")
            .add_conditional("validate_requirements", route_after_validation, {
                "await_review": "await_review",
                "generate_document": "generate_document"
            })
            .add_edge("await_review", "END")
            .add_edge("generate_document", "END")
            .build())

        return graph

    def get_tools(self) -> List[Any]:
        """Return list of tools this agent uses."""
        # Future: Add tools for requirements management systems, Jira, etc.
        return []

    def _extract_json_from_response(self, response: str) -> Any:
        """Extract JSON from an LLM response that may contain other text."""
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

        return {}
