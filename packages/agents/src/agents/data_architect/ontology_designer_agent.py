"""
Ontology Designer Agent

Designs LinkML ontology schemas from requirements.
Defines entity types, relationships, and property definitions.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
from agent_framework.state_management import (
    DataArchitectState,
    Decision,
    Message,
    add_decision,
    mark_for_review
)


ONTOLOGY_DESIGNER_SYSTEM_PROMPT = """You are an expert Ontology Designer Agent for Open Forge, an enterprise data platform.

Your role is to design LinkML-compatible ontology schemas based on requirements and discovered data sources.

## Your Capabilities:
1. Design entity types (classes) with appropriate properties
2. Define relationships between entities (slots with ranges)
3. Create property definitions with proper types and constraints
4. Structure ontologies following LinkML best practices

## LinkML Schema Structure:
- Use `id` as the schema identifier
- Define `prefixes` for namespaces
- Create `classes` for entity types with:
  - `description`: Clear description of the entity
  - `attributes`: Properties with types (string, integer, boolean, date, etc.)
  - `slot_usage`: Customize inherited slots
- Define `slots` for shared properties
- Use `enums` for controlled vocabularies
- Specify `types` for custom data types

## Output Format:
Always output ontology designs as valid YAML that conforms to LinkML specification.
Include clear descriptions and documentation for all elements.

## Design Principles:
1. Start with core entities first
2. Add relationships after entities are defined
3. Use descriptive names (PascalCase for classes, snake_case for properties)
4. Include cardinality constraints where appropriate
5. Document all design decisions
"""


class OntologyDesignerAgent(BaseOpenForgeAgent):
    """
    Agent that designs LinkML ontology schemas from requirements.

    This agent analyzes requirements and data source information to create
    a comprehensive ontology including entity types, relationships, and
    property definitions in LinkML format.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        memory: Optional[MemorySaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(llm, memory, config)

    @property
    def name(self) -> str:
        return "ontology_designer"

    @property
    def description(self) -> str:
        return "Designs LinkML ontology schemas from requirements, defining entity types, relationships, and property definitions."

    @property
    def required_inputs(self) -> List[str]:
        return ["requirements", "domain_context"]

    @property
    def output_keys(self) -> List[str]:
        return ["ontology_schema", "entity_definitions", "relationship_map", "design_decisions"]

    @property
    def state_class(self) -> Type[DataArchitectState]:
        return DataArchitectState

    def get_system_prompt(self) -> str:
        return ONTOLOGY_DESIGNER_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools for ontology design."""
        return []  # LLM-only agent for now

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for ontology design."""
        graph = StateGraph(DataArchitectState)

        # Add nodes
        graph.add_node("analyze_requirements", self._analyze_requirements)
        graph.add_node("design_entities", self._design_entities)
        graph.add_node("design_relationships", self._design_relationships)
        graph.add_node("generate_linkml_schema", self._generate_linkml_schema)
        graph.add_node("validate_design", self._validate_design)

        # Define edges
        graph.set_entry_point("analyze_requirements")
        graph.add_edge("analyze_requirements", "design_entities")
        graph.add_edge("design_entities", "design_relationships")
        graph.add_edge("design_relationships", "generate_linkml_schema")
        graph.add_edge("generate_linkml_schema", "validate_design")
        graph.add_conditional_edges(
            "validate_design",
            self._should_refine,
            {
                "refine": "design_entities",
                "complete": END
            }
        )

        return graph

    async def _analyze_requirements(self, state: DataArchitectState) -> Dict[str, Any]:
        """Analyze requirements to identify ontology needs."""
        context = state.get("agent_context", {})
        requirements = context.get("requirements", [])
        domain_context = context.get("domain_context", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Analyze the following requirements and domain context to identify:
1. Core entity types needed
2. Key relationships between entities
3. Important properties for each entity type
4. Any constraints or validation rules

Requirements:
{requirements}

Domain Context:
{domain_context}

Provide your analysis in a structured format.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="requirements_analysis",
            description="Analyzed requirements to identify ontology needs",
            confidence=0.85,
            reasoning="Extracted entity types, relationships, and properties from requirements"
        )

        return {
            "outputs": {"requirements_analysis": response.content},
            "decisions": [decision],
            "current_step": "analyze_requirements",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _design_entities(self, state: DataArchitectState) -> Dict[str, Any]:
        """Design entity types (classes) for the ontology."""
        outputs = state.get("outputs", {})
        analysis = outputs.get("requirements_analysis", "")
        context = state.get("agent_context", {})

        # Include any feedback from validation
        validation_feedback = outputs.get("validation_feedback", "")
        feedback_prompt = f"\n\nPrevious validation feedback to address:\n{validation_feedback}" if validation_feedback else ""

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Based on the requirements analysis, design the entity types (classes) for the LinkML ontology.

Requirements Analysis:
{analysis}

Domain Context:
{context.get('domain_context', {})}
{feedback_prompt}

For each entity type, provide:
1. Class name (PascalCase)
2. Description
3. Properties/attributes with types
4. Required vs optional properties
5. Any constraints

Output the entity definitions in LinkML YAML format for the 'classes' section.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="entity_design",
            description="Designed entity types for ontology",
            confidence=0.80,
            reasoning="Created entity definitions based on requirements analysis"
        )

        return {
            "outputs": {"entity_definitions": response.content},
            "decisions": [decision],
            "current_step": "design_entities",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _design_relationships(self, state: DataArchitectState) -> Dict[str, Any]:
        """Design relationships between entities."""
        outputs = state.get("outputs", {})
        analysis = outputs.get("requirements_analysis", "")
        entities = outputs.get("entity_definitions", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Based on the entity definitions, design the relationships between entities.

Entity Definitions:
{entities}

Requirements Analysis:
{analysis}

For each relationship, specify:
1. Relationship name (snake_case)
2. Source entity (domain)
3. Target entity (range)
4. Cardinality (one-to-one, one-to-many, many-to-many)
5. Description
6. Whether it's required or optional

Output the relationship definitions as LinkML slots with appropriate ranges.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="relationship_design",
            description="Designed relationships between entities",
            confidence=0.80,
            reasoning="Created relationship definitions connecting entity types"
        )

        return {
            "outputs": {"relationship_definitions": response.content},
            "decisions": [decision],
            "current_step": "design_relationships",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_linkml_schema(self, state: DataArchitectState) -> Dict[str, Any]:
        """Generate the complete LinkML schema."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        entities = outputs.get("entity_definitions", "")
        relationships = outputs.get("relationship_definitions", "")

        schema_name = context.get("schema_name", "OpenForgeOntology")
        schema_prefix = context.get("schema_prefix", "of")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate the complete LinkML schema combining all designed elements.

Entity Definitions:
{entities}

Relationship Definitions:
{relationships}

Schema Configuration:
- Schema Name: {schema_name}
- Prefix: {schema_prefix}

Create a complete, valid LinkML YAML schema that includes:
1. Schema metadata (id, name, prefixes)
2. All classes with their attributes
3. All slots (shared properties and relationships)
4. Enums for any controlled vocabularies
5. Type definitions if needed

Ensure the schema is syntactically correct and follows LinkML best practices.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="schema_generation",
            description="Generated complete LinkML schema",
            confidence=0.85,
            reasoning="Combined entity and relationship definitions into complete schema"
        )

        return {
            "outputs": {"ontology_schema": response.content},
            "ontology_draft": {"schema_yaml": response.content},
            "decisions": [decision],
            "current_step": "generate_linkml_schema",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _validate_design(self, state: DataArchitectState) -> Dict[str, Any]:
        """Validate the generated schema design."""
        outputs = state.get("outputs", {})
        schema = outputs.get("ontology_schema", "")
        context = state.get("agent_context", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate the generated LinkML schema for completeness and correctness.

Generated Schema:
{schema}

Original Requirements:
{context.get('requirements', [])}

Check for:
1. All required entities are defined
2. All relationships are properly connected
3. Property types are appropriate
4. Cardinality constraints are correct
5. Schema follows LinkML syntax
6. Naming conventions are consistent

Provide:
1. Validation status (PASS/FAIL)
2. List of any issues found
3. Recommendations for improvement
4. Confidence score (0-1)""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse validation result to determine if refinement is needed
        response_lower = response.content.lower()
        needs_refinement = "fail" in response_lower or "issue" in response_lower

        confidence = 0.90 if not needs_refinement else 0.70

        decision = add_decision(
            state,
            decision_type="design_validation",
            description="Validated ontology schema design",
            confidence=confidence,
            reasoning=response.content[:500],
            requires_approval=needs_refinement
        )

        review_items = []
        if needs_refinement:
            review_items.append(mark_for_review(
                state,
                item_type="ontology_design",
                item_id="validation_issues",
                description="Ontology design has issues that may need review",
                priority="medium"
            ))

        return {
            "outputs": {
                "validation_result": response.content,
                "needs_refinement": needs_refinement,
                "validation_feedback": response.content if needs_refinement else ""
            },
            "decisions": [decision],
            "requires_human_review": needs_refinement,
            "review_items": review_items,
            "current_step": "validate_design",
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _should_refine(self, state: DataArchitectState) -> str:
        """Determine if design needs refinement."""
        outputs = state.get("outputs", {})
        needs_refinement = outputs.get("needs_refinement", False)

        # Track iterations to prevent infinite loops
        iteration_count = state.get("agent_context", {}).get("iteration_count", 0)
        max_iterations = self.config.get("max_iterations", 3)

        if needs_refinement and iteration_count < max_iterations:
            return "refine"
        return "complete"
