"""
Transformation Designer Agent

Designs data transformation pipelines.
Maps source data to ontology and creates ETL specifications.
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


TRANSFORMATION_DESIGNER_SYSTEM_PROMPT = """You are an expert Transformation Designer Agent for Open Forge, an enterprise data platform.

Your role is to design data transformation pipelines that map source data to ontology schemas.

## Your Capabilities:
1. Analyze source data structures and schemas
2. Map source fields to ontology properties
3. Design transformation logic for data type conversions
4. Create ETL (Extract, Transform, Load) specifications
5. Handle data quality and validation rules

## Transformation Design Principles:
1. Source-to-Target Mapping: Define clear mappings from source fields to ontology properties
2. Data Type Conversion: Specify transformations needed for type compatibility
3. Data Cleaning: Include rules for handling nulls, defaults, and invalid values
4. Relationship Resolution: Design how relationships between entities are established
5. Incremental Loading: Consider how updates and deletes are handled

## ETL Specification Format:
Use YAML-based specifications with the following structure:

```yaml
etl_specification:
  name: string
  version: string
  source:
    type: string (database, api, file, etc.)
    connection: object
    extraction:
      method: string
      incremental_key: string (optional)

  transformations:
    - name: string
      description: string
      input: string (source field or previous transform)
      output: string (target field)
      logic:
        type: string (direct_map, convert, lookup, calculate, etc.)
        parameters: object

  target:
    ontology_class: string
    mapping:
      - source: string
        target: string
        transformation: string (reference to transformation)

  validation:
    - rule: string
      action: string (reject, warn, default)

  error_handling:
    strategy: string
    retry_policy: object
```

## Design Best Practices:
1. Document all transformations clearly
2. Include data quality checks
3. Handle edge cases explicitly
4. Design for idempotency where possible
5. Consider performance implications
"""


class TransformationDesignerAgent(BaseOpenForgeAgent):
    """
    Agent that designs data transformation pipelines.

    This agent analyzes source data structures and ontology schemas to create
    comprehensive ETL specifications for data ingestion and transformation.
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
        return "transformation_designer"

    @property
    def description(self) -> str:
        return "Designs data transformation pipelines that map source data to ontology schemas and creates ETL specifications."

    @property
    def required_inputs(self) -> List[str]:
        return ["ontology_schema", "source_data_info"]

    @property
    def output_keys(self) -> List[str]:
        return ["etl_specification", "field_mappings", "transformation_rules", "validation_rules"]

    @property
    def state_class(self) -> Type[DataArchitectState]:
        return DataArchitectState

    def get_system_prompt(self) -> str:
        return TRANSFORMATION_DESIGNER_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools for transformation design."""
        return []  # LLM-only agent for now

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for transformation design."""
        graph = StateGraph(DataArchitectState)

        # Add nodes
        graph.add_node("analyze_sources", self._analyze_sources)
        graph.add_node("design_mappings", self._design_mappings)
        graph.add_node("design_transformations", self._design_transformations)
        graph.add_node("create_validation_rules", self._create_validation_rules)
        graph.add_node("generate_etl_spec", self._generate_etl_spec)
        graph.add_node("review_specification", self._review_specification)

        # Define edges
        graph.set_entry_point("analyze_sources")
        graph.add_edge("analyze_sources", "design_mappings")
        graph.add_edge("design_mappings", "design_transformations")
        graph.add_edge("design_transformations", "create_validation_rules")
        graph.add_edge("create_validation_rules", "generate_etl_spec")
        graph.add_edge("generate_etl_spec", "review_specification")
        graph.add_conditional_edges(
            "review_specification",
            self._should_refine,
            {
                "refine": "design_mappings",
                "complete": END
            }
        )

        return graph

    async def _analyze_sources(self, state: DataArchitectState) -> Dict[str, Any]:
        """Analyze source data structures."""
        context = state.get("agent_context", {})
        source_info = context.get("source_data_info", {})
        ontology_schema = context.get("ontology_schema", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Analyze the source data structures and compare with the target ontology.

Source Data Information:
{source_info}

Target Ontology Schema:
```yaml
{ontology_schema}
```

Provide analysis of:
1. Source data types and structures
2. Data quality observations
3. Potential mapping challenges
4. Required transformations (type conversions, aggregations, etc.)
5. Missing data or gaps

Format the analysis clearly with sections for each source.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="source_analysis",
            description="Analyzed source data structures",
            confidence=0.85,
            reasoning="Identified source fields, types, and transformation requirements"
        )

        return {
            "outputs": {"source_analysis": response.content},
            "decisions": [decision],
            "current_step": "analyze_sources",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _design_mappings(self, state: DataArchitectState) -> Dict[str, Any]:
        """Design field mappings from source to target."""
        context = state.get("agent_context", {})
        outputs = state.get("outputs", {})
        source_info = context.get("source_data_info", {})
        ontology_schema = context.get("ontology_schema", "")
        source_analysis = outputs.get("source_analysis", "")

        # Include refinement feedback if present
        refinement_feedback = outputs.get("refinement_feedback", "")
        feedback_prompt = f"\n\nRefinement feedback to address:\n{refinement_feedback}" if refinement_feedback else ""

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Design field mappings from source data to ontology properties.

Source Analysis:
{source_analysis}

Source Data Information:
{source_info}

Target Ontology:
```yaml
{ontology_schema}
```
{feedback_prompt}

For each ontology class, create mappings that specify:
1. Source field(s) -> Target property
2. Mapping type (direct, transform, lookup, calculate)
3. Required transformations
4. Handling for missing/null values
5. Notes on any complex mappings

Output as YAML mapping specification.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="mapping_design",
            description="Designed source-to-target field mappings",
            confidence=0.80,
            reasoning="Created mappings for all ontology properties from source fields"
        )

        return {
            "outputs": {"field_mappings": response.content},
            "decisions": [decision],
            "current_step": "design_mappings",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _design_transformations(self, state: DataArchitectState) -> Dict[str, Any]:
        """Design specific transformation rules."""
        outputs = state.get("outputs", {})
        mappings = outputs.get("field_mappings", "")
        source_analysis = outputs.get("source_analysis", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Design detailed transformation rules for the field mappings.

Field Mappings:
{mappings}

Source Analysis:
{source_analysis}

For each transformation, specify:
1. Transformation name and description
2. Input field(s)
3. Output field
4. Transformation logic:
   - Type conversion rules
   - String manipulation (trim, case, concat, etc.)
   - Date/time formatting
   - Numeric operations
   - Lookup/reference resolution
   - Aggregation logic
5. Error handling for invalid values

Output as YAML transformation specifications.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="transformation_design",
            description="Designed transformation rules",
            confidence=0.80,
            reasoning="Created detailed transformation logic for all field mappings"
        )

        return {
            "outputs": {"transformation_rules": response.content},
            "decisions": [decision],
            "current_step": "design_transformations",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _create_validation_rules(self, state: DataArchitectState) -> Dict[str, Any]:
        """Create data validation rules."""
        context = state.get("agent_context", {})
        outputs = state.get("outputs", {})
        ontology_schema = context.get("ontology_schema", "")
        mappings = outputs.get("field_mappings", "")
        transformations = outputs.get("transformation_rules", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Create data validation rules for the ETL pipeline.

Field Mappings:
{mappings}

Transformation Rules:
{transformations}

Target Ontology:
```yaml
{ontology_schema}
```

Design validation rules for:
1. Required field validation
2. Data type validation
3. Range/constraint validation
4. Referential integrity checks
5. Business rule validation
6. Duplicate detection

For each rule, specify:
- Rule name and description
- Validation logic
- Action on failure (reject, warn, default, transform)
- Error message template

Output as YAML validation specifications.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="validation_design",
            description="Created data validation rules",
            confidence=0.85,
            reasoning="Designed comprehensive validation rules for data quality"
        )

        return {
            "outputs": {"validation_rules": response.content},
            "decisions": [decision],
            "current_step": "create_validation_rules",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_etl_spec(self, state: DataArchitectState) -> Dict[str, Any]:
        """Generate the complete ETL specification."""
        context = state.get("agent_context", {})
        outputs = state.get("outputs", {})

        source_info = context.get("source_data_info", {})
        ontology_schema = context.get("ontology_schema", "")
        mappings = outputs.get("field_mappings", "")
        transformations = outputs.get("transformation_rules", "")
        validations = outputs.get("validation_rules", "")

        spec_name = context.get("spec_name", "data_ingestion")
        spec_version = context.get("spec_version", "1.0.0")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate the complete ETL specification combining all components.

Source Data Information:
{source_info}

Target Ontology:
```yaml
{ontology_schema}
```

Field Mappings:
{mappings}

Transformation Rules:
{transformations}

Validation Rules:
{validations}

Specification Metadata:
- Name: {spec_name}
- Version: {spec_version}

Generate a complete, production-ready ETL specification in YAML format including:
1. Metadata (name, version, description)
2. Source configuration
3. Extraction settings
4. All transformations with detailed logic
5. Target mappings by ontology class
6. Validation rules
7. Error handling configuration
8. Performance hints (batching, parallelism)
9. Monitoring/logging configuration

Ensure the specification is complete and ready for implementation.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="etl_spec_generation",
            description="Generated complete ETL specification",
            confidence=0.85,
            reasoning="Combined all components into production-ready ETL specification"
        )

        return {
            "outputs": {"etl_specification": response.content},
            "decisions": [decision],
            "current_step": "generate_etl_spec",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _review_specification(self, state: DataArchitectState) -> Dict[str, Any]:
        """Review the generated ETL specification."""
        context = state.get("agent_context", {})
        outputs = state.get("outputs", {})
        etl_spec = outputs.get("etl_specification", "")
        requirements = context.get("requirements", [])

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Review the generated ETL specification for completeness and correctness.

ETL Specification:
```yaml
{etl_spec}
```

Requirements:
{requirements}

Review for:
1. All source data is mapped
2. All ontology classes have complete mappings
3. Transformations are logically correct
4. Validation rules are comprehensive
5. Error handling is appropriate
6. Performance considerations are addressed

Provide:
1. Review status (APPROVED/NEEDS_REFINEMENT)
2. List of issues found (if any)
3. Recommendations for improvement
4. Confidence score (0-1)

Format as structured review report.""")
        ]

        response = await self.llm.ainvoke(messages)

        # Determine if refinement is needed
        response_lower = response.content.lower()
        needs_refinement = "needs_refinement" in response_lower or "issue" in response_lower.split("approved")[0] if "approved" in response_lower else "issue" in response_lower

        confidence = 0.90 if not needs_refinement else 0.70

        decision = add_decision(
            state,
            decision_type="specification_review",
            description="Reviewed ETL specification",
            confidence=confidence,
            reasoning=response.content[:500],
            requires_approval=needs_refinement
        )

        review_items = []
        if needs_refinement:
            review_items.append(mark_for_review(
                state,
                item_type="etl_specification",
                item_id="spec_review",
                description="ETL specification may need refinement",
                priority="medium"
            ))

        return {
            "outputs": {
                "specification_review": response.content,
                "needs_refinement": needs_refinement,
                "refinement_feedback": response.content if needs_refinement else ""
            },
            "decisions": [decision],
            "requires_human_review": needs_refinement,
            "review_items": review_items,
            "current_step": "review_specification",
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _should_refine(self, state: DataArchitectState) -> str:
        """Determine if specification needs refinement."""
        outputs = state.get("outputs", {})
        needs_refinement = outputs.get("needs_refinement", False)

        # Track iterations to prevent infinite loops
        iteration_count = state.get("agent_context", {}).get("iteration_count", 0)
        max_iterations = self.config.get("max_iterations", 3)

        if needs_refinement and iteration_count < max_iterations:
            return "refine"
        return "complete"
