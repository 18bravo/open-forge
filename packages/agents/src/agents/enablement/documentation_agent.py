"""
Documentation Agent

Generates API documentation, user guides, and operational runbooks
from ontology definitions and system architecture.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
import json
import re

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
from agent_framework.state_management import (
    EnablementState,
    Decision,
    add_decision,
    mark_for_review,
)
from agent_framework.graph_builder import WorkflowBuilder
from agent_framework.prompts import PromptTemplate, PromptLibrary, build_context_string


# Documentation-specific prompt templates
DOCUMENTATION_SYSTEM = PromptTemplate("""You are a Documentation Agent in the Open Forge platform.

Your role is to generate comprehensive documentation from ontology definitions and system architecture.

Engagement ID: $engagement_id
Phase: $phase

Your capabilities:
- Generate API documentation from ontology schemas
- Create user guides for different audience levels
- Produce operational runbooks for system administration
- Document entity relationships and data flows
- Create reference documentation with examples

Guidelines:
- Write clear, concise documentation appropriate for the target audience
- Include code examples and practical use cases
- Follow documentation best practices (clear headings, consistent formatting)
- Flag any gaps or ambiguities in source materials for review
- Provide confidence scores for documentation completeness

Current context:
$context
""")

GENERATE_API_DOCS = PromptTemplate("""Generate API documentation for the following ontology schema.

Ontology Schema:
$ontology_schema

System Architecture:
$system_architecture

Generate comprehensive API documentation including:
1. Overview and introduction
2. Authentication and authorization
3. Entity types with their properties and constraints
4. Relationships between entities
5. CRUD operations for each entity type
6. Query capabilities and filtering options
7. Error codes and handling
8. Code examples in multiple languages (Python, JavaScript, cURL)
9. Rate limiting and best practices

Output as a structured JSON object with sections:
{
    "title": "API Documentation",
    "version": "1.0.0",
    "overview": "...",
    "authentication": {...},
    "entities": [...],
    "relationships": [...],
    "operations": [...],
    "error_codes": [...],
    "examples": [...],
    "best_practices": [...]
}
""")

GENERATE_USER_GUIDE = PromptTemplate("""Generate a user guide for the following system.

Ontology Schema:
$ontology_schema

Target Audience: $target_audience
Use Cases: $use_cases
System Features: $system_features

Create a user guide that includes:
1. Getting started section
2. Core concepts explanation
3. Step-by-step workflows for common tasks
4. Screenshots/diagram descriptions
5. Tips and best practices
6. Common pitfalls to avoid
7. Glossary of terms

Output as a structured JSON object with sections:
{
    "title": "User Guide",
    "audience": "...",
    "getting_started": {...},
    "core_concepts": [...],
    "workflows": [...],
    "tips": [...],
    "glossary": [...]
}
""")

GENERATE_RUNBOOK = PromptTemplate("""Generate an operational runbook for the following system.

System Architecture:
$system_architecture

Ontology Schema:
$ontology_schema

Operations Context:
$operations_context

Create a comprehensive runbook including:
1. System overview and architecture
2. Deployment procedures
3. Configuration management
4. Monitoring and alerting procedures
5. Backup and recovery procedures
6. Scaling procedures
7. Incident response procedures
8. Maintenance windows and procedures
9. Troubleshooting guide
10. Contact information and escalation paths

Output as a structured JSON object with sections:
{
    "title": "Operations Runbook",
    "system_name": "...",
    "version": "1.0.0",
    "overview": {...},
    "deployment": {...},
    "configuration": {...},
    "monitoring": {...},
    "backup_recovery": {...},
    "scaling": {...},
    "incident_response": {...},
    "maintenance": {...},
    "troubleshooting": [...],
    "contacts": [...]
}
""")

VALIDATE_DOCUMENTATION = PromptTemplate("""Review the following documentation for completeness and quality.

Documentation Type: $doc_type
Documentation Content: $documentation

Evaluate:
1. Completeness - Are all necessary sections present?
2. Clarity - Is the writing clear and understandable?
3. Accuracy - Does it match the source schema/architecture?
4. Consistency - Is formatting and terminology consistent?
5. Examples - Are there sufficient practical examples?
6. Audience fit - Is it appropriate for the target audience?

Output as JSON:
{
    "score": 0.0-1.0,
    "completeness_score": 0.0-1.0,
    "clarity_score": 0.0-1.0,
    "issues": [...],
    "suggestions": [...],
    "requires_revision": true/false
}
""")


class DocumentationAgent(BaseOpenForgeAgent):
    """
    Agent for generating documentation from ontology and system architecture.

    This agent:
    - Generates API documentation from ontology schemas
    - Creates user guides for different audiences
    - Produces operational runbooks
    - Validates documentation quality and completeness
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
        """Register documentation-specific prompts with the library."""
        PromptLibrary.register("documentation_system", DOCUMENTATION_SYSTEM)
        PromptLibrary.register("generate_api_docs", GENERATE_API_DOCS)
        PromptLibrary.register("generate_user_guide", GENERATE_USER_GUIDE)
        PromptLibrary.register("generate_runbook", GENERATE_RUNBOOK)
        PromptLibrary.register("validate_documentation", VALIDATE_DOCUMENTATION)

    @property
    def name(self) -> str:
        return "documentation_agent"

    @property
    def description(self) -> str:
        return (
            "Generates API documentation, user guides, and operational runbooks "
            "from ontology definitions and system architecture."
        )

    @property
    def required_inputs(self) -> List[str]:
        return ["ontology_schema"]

    @property
    def output_keys(self) -> List[str]:
        return [
            "api_documentation",
            "user_guides",
            "runbooks",
            "documentation_quality_report"
        ]

    @property
    def state_class(self) -> Type[EnablementState]:
        return EnablementState

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return DOCUMENTATION_SYSTEM.template

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for documentation generation."""
        builder = WorkflowBuilder(EnablementState)

        async def extract_ontology_info(state: EnablementState) -> Dict[str, Any]:
            """Extract entities and relationships from ontology schema."""
            context = state.get("agent_context", {})
            ontology_schema = context.get("ontology_schema", "")

            prompt = f"""Analyze the following ontology schema and extract:
1. All entity types with their properties
2. Relationships between entities
3. Constraints and validations
4. Key use cases implied by the schema

Ontology Schema:
{ontology_schema}

Output as JSON with keys: entities, relationships, constraints, use_cases
"""
            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                extracted = json.loads(response.content)
            except json.JSONDecodeError:
                extracted = self._extract_json_from_response(response.content)

            decision = add_decision(
                state,
                decision_type="ontology_extraction",
                description=f"Extracted {len(extracted.get('entities', []))} entities from ontology",
                confidence=0.85 if extracted.get('entities') else 0.4,
                reasoning="Parsed ontology schema to identify documentation targets"
            )

            return {
                "outputs": {
                    "ontology_entities": extracted.get("entities", []),
                    "ontology_relationships": extracted.get("relationships", [])
                },
                "ontology_entities": extracted.get("entities", []),
                "ontology_relationships": extracted.get("relationships", []),
                "decisions": [decision],
                "current_step": "ontology_extracted"
            }

        async def generate_api_documentation(state: EnablementState) -> Dict[str, Any]:
            """Generate comprehensive API documentation."""
            context = state.get("agent_context", {})

            prompt = PromptLibrary.format(
                "generate_api_docs",
                ontology_schema=context.get("ontology_schema", ""),
                system_architecture=json.dumps(context.get("system_architecture", {}))
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                api_docs = json.loads(response.content)
            except json.JSONDecodeError:
                api_docs = self._extract_json_from_response(response.content)

            # Enhance with extracted entities
            entities = state.get("ontology_entities", [])
            if entities and isinstance(api_docs, dict):
                api_docs["entity_count"] = len(entities)
                api_docs["generated_at"] = datetime.utcnow().isoformat()

            decision = add_decision(
                state,
                decision_type="api_documentation_generation",
                description="Generated API documentation from ontology schema",
                confidence=0.8 if api_docs.get("entities") else 0.6,
                reasoning="Created comprehensive API reference from ontology definitions"
            )

            return {
                "outputs": {"api_documentation": api_docs},
                "api_documentation": api_docs,
                "decisions": [decision],
                "current_step": "api_docs_generated"
            }

        async def generate_user_guides(state: EnablementState) -> Dict[str, Any]:
            """Generate user guides for different audiences."""
            context = state.get("agent_context", {})
            outputs = state.get("outputs", {})

            # Define target audiences
            audiences = context.get("target_audiences", [
                {"name": "End Users", "level": "beginner", "focus": "daily tasks"},
                {"name": "Power Users", "level": "intermediate", "focus": "advanced features"},
                {"name": "Administrators", "level": "advanced", "focus": "configuration and management"}
            ])

            user_guides = []

            for audience in audiences:
                prompt = PromptLibrary.format(
                    "generate_user_guide",
                    ontology_schema=context.get("ontology_schema", ""),
                    target_audience=json.dumps(audience),
                    use_cases=json.dumps(context.get("use_cases", [])),
                    system_features=json.dumps(context.get("system_features", []))
                )

                messages = [
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = await self.llm.ainvoke(messages)

                try:
                    guide = json.loads(response.content)
                except json.JSONDecodeError:
                    guide = self._extract_json_from_response(response.content)

                guide["target_audience"] = audience
                guide["generated_at"] = datetime.utcnow().isoformat()
                user_guides.append(guide)

            decision = add_decision(
                state,
                decision_type="user_guide_generation",
                description=f"Generated {len(user_guides)} user guides for different audiences",
                confidence=0.75 if user_guides else 0.4,
                reasoning="Created audience-specific documentation"
            )

            return {
                "outputs": {"user_guides": user_guides},
                "user_guides": user_guides,
                "decisions": [decision],
                "current_step": "user_guides_generated"
            }

        async def generate_runbooks(state: EnablementState) -> Dict[str, Any]:
            """Generate operational runbooks."""
            context = state.get("agent_context", {})
            outputs = state.get("outputs", {})

            # Define runbook types based on context
            runbook_types = context.get("runbook_types", [
                {"name": "Deployment Runbook", "focus": "deployment and updates"},
                {"name": "Operations Runbook", "focus": "day-to-day operations"},
                {"name": "Incident Response Runbook", "focus": "incident handling"}
            ])

            runbooks = []

            for runbook_type in runbook_types:
                prompt = PromptLibrary.format(
                    "generate_runbook",
                    system_architecture=json.dumps(context.get("system_architecture", {})),
                    ontology_schema=context.get("ontology_schema", ""),
                    operations_context=json.dumps({
                        "runbook_type": runbook_type,
                        "monitoring_config": context.get("monitoring_config", {}),
                        "scaling_config": context.get("scaling_config", {}),
                        "team_structure": context.get("team_structure", {})
                    })
                )

                messages = [
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = await self.llm.ainvoke(messages)

                try:
                    runbook = json.loads(response.content)
                except json.JSONDecodeError:
                    runbook = self._extract_json_from_response(response.content)

                runbook["runbook_type"] = runbook_type
                runbook["generated_at"] = datetime.utcnow().isoformat()
                runbooks.append(runbook)

            decision = add_decision(
                state,
                decision_type="runbook_generation",
                description=f"Generated {len(runbooks)} operational runbooks",
                confidence=0.8 if runbooks else 0.5,
                reasoning="Created operational documentation for system management"
            )

            return {
                "outputs": {"runbooks": runbooks},
                "runbooks": runbooks,
                "decisions": [decision],
                "current_step": "runbooks_generated"
            }

        async def validate_documentation(state: EnablementState) -> Dict[str, Any]:
            """Validate all generated documentation for quality."""
            outputs = state.get("outputs", {})

            quality_reports = []
            requires_revision = False

            # Validate API documentation
            api_docs = outputs.get("api_documentation", {})
            if api_docs:
                api_validation = await self._validate_single_doc(
                    "API Documentation", api_docs
                )
                quality_reports.append(api_validation)
                if api_validation.get("requires_revision"):
                    requires_revision = True

            # Validate user guides
            for guide in outputs.get("user_guides", []):
                guide_validation = await self._validate_single_doc(
                    f"User Guide - {guide.get('target_audience', {}).get('name', 'Unknown')}",
                    guide
                )
                quality_reports.append(guide_validation)
                if guide_validation.get("requires_revision"):
                    requires_revision = True

            # Validate runbooks
            for runbook in outputs.get("runbooks", []):
                runbook_validation = await self._validate_single_doc(
                    f"Runbook - {runbook.get('runbook_type', {}).get('name', 'Unknown')}",
                    runbook
                )
                quality_reports.append(runbook_validation)
                if runbook_validation.get("requires_revision"):
                    requires_revision = True

            # Calculate overall quality score
            if quality_reports:
                avg_score = sum(r.get("score", 0) for r in quality_reports) / len(quality_reports)
            else:
                avg_score = 0.0

            quality_report = {
                "overall_score": avg_score,
                "document_reports": quality_reports,
                "requires_revision": requires_revision,
                "generated_at": datetime.utcnow().isoformat()
            }

            review_items = []
            if requires_revision:
                for report in quality_reports:
                    if report.get("requires_revision"):
                        review_items.append(
                            mark_for_review(
                                state,
                                item_type="documentation_quality",
                                item_id=f"doc_review_{report.get('document_type', 'unknown')}",
                                description=f"Documentation requires revision: {', '.join(report.get('issues', []))}",
                                priority="medium"
                            )
                        )

            decision = add_decision(
                state,
                decision_type="documentation_validation",
                description=f"Validated documentation quality: {avg_score:.2f} overall score",
                confidence=avg_score,
                reasoning="Assessed completeness, clarity, and accuracy of generated documentation",
                requires_approval=requires_revision
            )

            return {
                "outputs": {"documentation_quality_report": quality_report},
                "decisions": [decision],
                "requires_human_review": requires_revision,
                "review_items": review_items,
                "current_step": "validation_complete"
            }

        async def compile_documentation_package(state: EnablementState) -> Dict[str, Any]:
            """Compile all documentation into a final package."""
            outputs = state.get("outputs", {})
            decisions = state.get("decisions", [])

            # Calculate overall confidence
            avg_confidence = (
                sum(d.confidence for d in decisions) / len(decisions)
                if decisions else 0.5
            )

            documentation_package = {
                "api_documentation": outputs.get("api_documentation", {}),
                "user_guides": outputs.get("user_guides", []),
                "runbooks": outputs.get("runbooks", []),
                "quality_report": outputs.get("documentation_quality_report", {}),
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "confidence_score": avg_confidence,
                    "total_documents": (
                        1 +  # API docs
                        len(outputs.get("user_guides", [])) +
                        len(outputs.get("runbooks", []))
                    )
                }
            }

            decision = add_decision(
                state,
                decision_type="documentation_compilation",
                description="Compiled complete documentation package",
                confidence=avg_confidence,
                reasoning="Aggregated all documentation outputs"
            )

            return {
                "outputs": {"documentation_package": documentation_package},
                "decisions": [decision],
                "current_step": "complete"
            }

        def route_after_validation(state: EnablementState) -> str:
            """Route based on validation results."""
            if state.get("requires_human_review"):
                return "await_review"
            return "compile"

        async def await_human_review(state: EnablementState) -> Dict[str, Any]:
            """Wait for human review of documentation."""
            return {
                "current_step": "awaiting_human_review"
            }

        # Build the workflow
        graph = (builder
            .add_node("extract_ontology", extract_ontology_info)
            .add_node("generate_api_docs", generate_api_documentation)
            .add_node("generate_user_guides", generate_user_guides)
            .add_node("generate_runbooks", generate_runbooks)
            .add_node("validate", validate_documentation)
            .add_node("await_review", await_human_review)
            .add_node("compile", compile_documentation_package)
            .set_entry("extract_ontology")
            .add_edge("extract_ontology", "generate_api_docs")
            .add_edge("generate_api_docs", "generate_user_guides")
            .add_edge("generate_user_guides", "generate_runbooks")
            .add_edge("generate_runbooks", "validate")
            .add_conditional("validate", route_after_validation, {
                "await_review": "await_review",
                "compile": "compile"
            })
            .add_edge("await_review", "END")
            .add_edge("compile", "END")
            .build())

        return graph

    async def _validate_single_doc(
        self,
        doc_type: str,
        documentation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a single documentation artifact."""
        prompt = PromptLibrary.format(
            "validate_documentation",
            doc_type=doc_type,
            documentation=json.dumps(documentation, default=str)[:4000]  # Truncate for context window
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

        validation["document_type"] = doc_type
        return validation

    def get_tools(self) -> List[Any]:
        """Return list of tools this agent uses."""
        return []

    def _extract_json_from_response(self, response: str) -> Any:
        """Extract JSON from an LLM response that may contain other text."""
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
