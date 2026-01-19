"""
Source Discovery Agent

Discovers available data sources, catalogs data assets,
and assesses data quality indicators.
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


class DataSourceType(str, Enum):
    """Types of data sources that can be discovered."""
    DATABASE = "database"
    API = "api"
    FILE_SYSTEM = "file_system"
    CLOUD_STORAGE = "cloud_storage"
    SAAS_APPLICATION = "saas_application"
    DATA_WAREHOUSE = "data_warehouse"
    STREAMING = "streaming"
    LEGACY_SYSTEM = "legacy_system"
    UNKNOWN = "unknown"


class DataQualityDimension(str, Enum):
    """Dimensions for assessing data quality."""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"


# Source discovery-specific prompt templates
SOURCE_DISCOVERY_SYSTEM = PromptTemplate("""You are a Source Discovery Agent in the Open Forge platform.

Your role is to discover, catalog, and assess data sources for data engagements.

Engagement ID: $engagement_id
Phase: $phase

Your capabilities:
- Identify available data sources in an organization
- Catalog data assets with metadata
- Assess data quality indicators
- Evaluate integration complexity
- Determine data accessibility and permissions

Guidelines:
- Document all sources thoroughly
- Assess quality objectively with evidence
- Flag sources with quality issues for review
- Consider data sensitivity and compliance
- Provide confidence scores for assessments

Current context:
$context
""")

DISCOVER_SOURCES = PromptTemplate("""Discover data sources based on the following information.

Organization: $organization
Technology stack: $tech_stack
Known systems: $known_systems
Stakeholder data needs: $data_needs

For each data source discovered, provide:
1. Source name
2. Source type (database, api, file_system, cloud_storage, saas_application, data_warehouse, streaming, legacy_system)
3. Description
4. Owner/Team responsible
5. Technology/Platform
6. Estimated data volume
7. Update frequency
8. Access method
9. Known constraints or limitations

Output as a JSON array of source objects.
""")

CATALOG_SOURCE = PromptTemplate("""Create a detailed catalog entry for the following data source.

Source name: $source_name
Source type: $source_type
Connection info: $connection_info
Sample schema: $sample_schema

Document:
1. Entity types present
2. Key fields and their types
3. Relationships between entities
4. Temporal coverage (date ranges)
5. Granularity of data
6. Primary keys and identifiers
7. Sensitive data fields (PII, financial, etc.)
8. Data lineage (if known)

Output as a structured catalog entry in JSON format.
""")

ASSESS_QUALITY = PromptTemplate("""Assess the data quality of the following source.

Source: $source_name
Sample data statistics: $data_stats
Schema information: $schema_info
Known issues: $known_issues

Evaluate each quality dimension (0.0 to 1.0):
1. Completeness - Percentage of non-null values
2. Accuracy - Correctness of data values
3. Consistency - Uniformity across records
4. Timeliness - Freshness and update frequency
5. Validity - Conformance to business rules
6. Uniqueness - Absence of duplicates

For each dimension, provide:
- Score (0.0 to 1.0)
- Evidence/reasoning
- Recommendations for improvement

Output as JSON with overall_score and dimension_scores.
""")

EVALUATE_INTEGRATION = PromptTemplate("""Evaluate the integration complexity for the following data source.

Source: $source_name
Source type: $source_type
Technology: $technology
Current access methods: $access_methods
Target architecture: $target_architecture

Assess:
1. Technical complexity (1-5)
2. Effort estimate (hours/days)
3. Required connectors or adapters
4. Transformation requirements
5. Security considerations
6. Dependencies
7. Risks and mitigations

Output as a structured integration assessment in JSON format.
""")


class SourceDiscoveryAgent(BaseOpenForgeAgent):
    """
    Agent for discovering and assessing data sources.

    This agent:
    - Discovers data sources across the organization
    - Creates detailed catalog entries for each source
    - Assesses data quality across multiple dimensions
    - Evaluates integration complexity
    - Identifies data lineage and relationships
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
        """Register source discovery-specific prompts with the library."""
        PromptLibrary.register("source_discovery_system", SOURCE_DISCOVERY_SYSTEM)
        PromptLibrary.register("discover_sources", DISCOVER_SOURCES)
        PromptLibrary.register("catalog_source", CATALOG_SOURCE)
        PromptLibrary.register("assess_quality", ASSESS_QUALITY)
        PromptLibrary.register("evaluate_integration", EVALUATE_INTEGRATION)

    @property
    def name(self) -> str:
        return "source_discovery_agent"

    @property
    def description(self) -> str:
        return (
            "Discovers available data sources, catalogs data assets, "
            "and assesses data quality indicators for data engagements."
        )

    @property
    def required_inputs(self) -> List[str]:
        return ["organization", "tech_stack"]

    @property
    def output_keys(self) -> List[str]:
        return [
            "discovered_sources",
            "source_catalog",
            "quality_assessments",
            "integration_assessments",
            "source_recommendations"
        ]

    @property
    def state_class(self) -> Type[DiscoveryState]:
        return DiscoveryState

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return SOURCE_DISCOVERY_SYSTEM.template

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for source discovery."""
        builder = WorkflowBuilder(DiscoveryState)

        async def discover_sources(state: DiscoveryState) -> Dict[str, Any]:
            """Discover data sources from context and stakeholder input."""
            context = state.get("agent_context", {})

            # Get stakeholder data needs if available from previous agent
            previous_outputs = context.get("previous_outputs", {})
            stakeholder_map = previous_outputs.get("stakeholder_map", {})
            requirements = stakeholder_map.get("requirements_by_stakeholder", [])

            # Extract data needs from requirements
            data_needs = []
            for req in requirements:
                if isinstance(req, dict) and "requirements" in req:
                    reqs = req.get("requirements", {})
                    if isinstance(reqs, dict):
                        data_needs.extend(reqs.get("data_needs", []))

            prompt = PromptLibrary.format(
                "discover_sources",
                organization=context.get("organization", "Unknown"),
                tech_stack=json.dumps(context.get("tech_stack", [])),
                known_systems=json.dumps(context.get("known_systems", [])),
                data_needs=json.dumps(data_needs)
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                sources = json.loads(response.content)
            except json.JSONDecodeError:
                sources = self._extract_json_from_response(response.content)

            # Validate and normalize source types
            for source in sources:
                source_type = source.get("source_type", "unknown").lower()
                try:
                    source["source_type"] = DataSourceType(source_type).value
                except ValueError:
                    source["source_type"] = DataSourceType.UNKNOWN.value

            decision = add_decision(
                state,
                decision_type="source_discovery",
                description=f"Discovered {len(sources)} data sources",
                confidence=0.75 if sources else 0.3,
                reasoning="Based on technology stack and stakeholder data needs"
            )

            return {
                "outputs": {"discovered_sources": sources},
                "discovered_sources": sources,
                "decisions": [decision],
                "current_step": "sources_discovered"
            }

        async def catalog_sources(state: DiscoveryState) -> Dict[str, Any]:
            """Create detailed catalog entries for discovered sources."""
            sources = state.get("discovered_sources", [])
            context = state.get("agent_context", {})

            catalog = {}
            for source in sources:
                source_name = source.get("name", "Unknown")

                # Get additional info if available
                source_details = context.get("source_details", {}).get(source_name, {})

                prompt = PromptLibrary.format(
                    "catalog_source",
                    source_name=source_name,
                    source_type=source.get("source_type", "unknown"),
                    connection_info=json.dumps(source_details.get("connection_info", {})),
                    sample_schema=json.dumps(source_details.get("schema", {}))
                )

                messages = [
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = await self.llm.ainvoke(messages)

                try:
                    catalog_entry = json.loads(response.content)
                except json.JSONDecodeError:
                    catalog_entry = self._extract_json_from_response(response.content)

                catalog[source_name] = {
                    "source_info": source,
                    "catalog_entry": catalog_entry,
                    "cataloged_at": datetime.utcnow().isoformat()
                }

            decision = add_decision(
                state,
                decision_type="source_cataloging",
                description=f"Cataloged {len(catalog)} data sources",
                confidence=0.7,
                reasoning="Created detailed catalog entries based on available information"
            )

            return {
                "outputs": {"source_catalog": catalog},
                "decisions": [decision],
                "current_step": "sources_cataloged"
            }

        async def assess_quality(state: DiscoveryState) -> Dict[str, Any]:
            """Assess data quality for each discovered source."""
            sources = state.get("discovered_sources", [])
            context = state.get("agent_context", {})

            assessments = {}
            low_quality_sources = []

            for source in sources:
                source_name = source.get("name", "Unknown")

                # Get quality-related info if available
                source_stats = context.get("source_stats", {}).get(source_name, {})
                known_issues = context.get("known_issues", {}).get(source_name, [])

                prompt = PromptLibrary.format(
                    "assess_quality",
                    source_name=source_name,
                    data_stats=json.dumps(source_stats.get("statistics", {})),
                    schema_info=json.dumps(source_stats.get("schema", {})),
                    known_issues=json.dumps(known_issues)
                )

                messages = [
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = await self.llm.ainvoke(messages)

                try:
                    assessment = json.loads(response.content)
                except json.JSONDecodeError:
                    assessment = self._extract_json_from_response(response.content)

                # Calculate overall score if not provided
                if "overall_score" not in assessment:
                    dim_scores = assessment.get("dimension_scores", {})
                    if dim_scores:
                        assessment["overall_score"] = sum(
                            s.get("score", 0.5) for s in dim_scores.values()
                        ) / len(dim_scores)
                    else:
                        assessment["overall_score"] = 0.5

                assessments[source_name] = assessment

                # Track low quality sources for review
                if assessment.get("overall_score", 0.5) < 0.6:
                    low_quality_sources.append(source_name)

            # Create review items for low quality sources
            review_items = []
            for source_name in low_quality_sources:
                review_items.append(
                    mark_for_review(
                        state,
                        item_type="data_quality",
                        item_id=f"quality_{source_name}",
                        description=f"Data source '{source_name}' has quality score below threshold",
                        priority="medium"
                    )
                )

            decision = add_decision(
                state,
                decision_type="quality_assessment",
                description=f"Assessed quality for {len(assessments)} sources, {len(low_quality_sources)} below threshold",
                confidence=0.8,
                reasoning="Evaluated across completeness, accuracy, consistency, timeliness, validity, uniqueness"
            )

            return {
                "outputs": {"quality_assessments": assessments},
                "source_assessments": assessments,
                "decisions": [decision],
                "review_items": review_items,
                "requires_human_review": len(low_quality_sources) > 0,
                "current_step": "quality_assessed"
            }

        async def evaluate_integration(state: DiscoveryState) -> Dict[str, Any]:
            """Evaluate integration complexity for each source."""
            sources = state.get("discovered_sources", [])
            context = state.get("agent_context", {})
            target_arch = context.get("target_architecture", {})

            integration_assessments = {}

            for source in sources:
                source_name = source.get("name", "Unknown")

                prompt = PromptLibrary.format(
                    "evaluate_integration",
                    source_name=source_name,
                    source_type=source.get("source_type", "unknown"),
                    technology=source.get("technology", "unknown"),
                    access_methods=json.dumps(source.get("access_method", [])),
                    target_architecture=json.dumps(target_arch)
                )

                messages = [
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = await self.llm.ainvoke(messages)

                try:
                    assessment = json.loads(response.content)
                except json.JSONDecodeError:
                    assessment = self._extract_json_from_response(response.content)

                integration_assessments[source_name] = assessment

            decision = add_decision(
                state,
                decision_type="integration_assessment",
                description=f"Evaluated integration complexity for {len(integration_assessments)} sources",
                confidence=0.7,
                reasoning="Assessed based on source type, technology, and target architecture"
            )

            return {
                "outputs": {"integration_assessments": integration_assessments},
                "decisions": [decision],
                "current_step": "integration_evaluated"
            }

        async def generate_recommendations(state: DiscoveryState) -> Dict[str, Any]:
            """Generate recommendations based on all assessments."""
            outputs = state.get("outputs", {})
            sources = state.get("discovered_sources", [])
            quality = outputs.get("quality_assessments", {})
            integration = outputs.get("integration_assessments", {})

            recommendations = []

            for source in sources:
                source_name = source.get("name", "Unknown")
                quality_score = quality.get(source_name, {}).get("overall_score", 0.5)
                complexity = integration.get(source_name, {}).get("technical_complexity", 3)

                # High quality, low complexity = prioritize
                # Low quality, high complexity = flag for review
                priority = "high" if quality_score > 0.7 and complexity <= 2 else (
                    "low" if quality_score < 0.5 or complexity >= 4 else "medium"
                )

                recommendations.append({
                    "source_name": source_name,
                    "priority": priority,
                    "quality_score": quality_score,
                    "integration_complexity": complexity,
                    "recommendation": self._generate_recommendation_text(
                        source_name, quality_score, complexity
                    ),
                    "estimated_effort": integration.get(source_name, {}).get("effort_estimate", "unknown")
                })

            # Sort by priority
            priority_order = {"high": 0, "medium": 1, "low": 2}
            recommendations.sort(key=lambda x: priority_order.get(x["priority"], 1))

            decision = add_decision(
                state,
                decision_type="source_recommendations",
                description=f"Generated recommendations for {len(recommendations)} sources",
                confidence=0.85,
                reasoning="Combined quality and integration assessments for prioritization"
            )

            return {
                "outputs": {"source_recommendations": recommendations},
                "decisions": [decision],
                "current_step": "complete"
            }

        def route_after_quality(state: DiscoveryState) -> str:
            """Route based on quality assessment results."""
            # Continue to integration evaluation regardless of quality issues
            # Human review will happen after full assessment
            return "evaluate_integration"

        # Build the workflow
        graph = (builder
            .add_node("discover_sources", discover_sources)
            .add_node("catalog_sources", catalog_sources)
            .add_node("assess_quality", assess_quality)
            .add_node("evaluate_integration", evaluate_integration)
            .add_node("generate_recommendations", generate_recommendations)
            .set_entry("discover_sources")
            .add_edge("discover_sources", "catalog_sources")
            .add_edge("catalog_sources", "assess_quality")
            .add_conditional("assess_quality", route_after_quality, {
                "evaluate_integration": "evaluate_integration"
            })
            .add_edge("evaluate_integration", "generate_recommendations")
            .add_edge("generate_recommendations", "END")
            .build())

        return graph

    def get_tools(self) -> List[Any]:
        """Return list of tools this agent uses."""
        # Future: Add tools for database introspection, API discovery, etc.
        return []

    def _generate_recommendation_text(
        self,
        source_name: str,
        quality_score: float,
        complexity: int
    ) -> str:
        """Generate recommendation text based on scores."""
        if quality_score > 0.7 and complexity <= 2:
            return f"Prioritize integration of '{source_name}' - high quality data with low integration effort."
        elif quality_score > 0.7 and complexity > 2:
            return f"'{source_name}' has high quality data but requires significant integration effort. Plan accordingly."
        elif quality_score < 0.5:
            return f"'{source_name}' requires data quality improvements before integration. Address completeness and accuracy issues."
        else:
            return f"'{source_name}' is viable for integration with moderate effort. Consider quality improvements during ETL."

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
