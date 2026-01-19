"""
Schema Validator Agent

Validates ontology schemas against requirements.
Checks for completeness and identifies potential issues.
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


SCHEMA_VALIDATOR_SYSTEM_PROMPT = """You are an expert Schema Validator Agent for Open Forge, an enterprise data platform.

Your role is to validate LinkML ontology schemas against requirements and best practices.

## Your Capabilities:
1. Validate schema syntax and structure
2. Check completeness against requirements
3. Identify potential issues and anti-patterns
4. Verify relationship integrity
5. Assess data type appropriateness

## Validation Categories:

### 1. Structural Validation
- Valid LinkML YAML syntax
- Required schema elements present (id, name, prefixes)
- Class definitions are complete
- Slot definitions have proper ranges

### 2. Completeness Validation
- All required entities from requirements are present
- All relationships are defined
- Properties have appropriate types
- Documentation is adequate

### 3. Semantic Validation
- Entity names are meaningful
- Relationships make logical sense
- Cardinality constraints are appropriate
- No circular dependencies (unless intended)

### 4. Best Practices
- Naming conventions followed (PascalCase for classes, snake_case for properties)
- Proper use of inheritance
- Appropriate use of enums for controlled vocabularies
- Clear descriptions for all elements

## Output Format:
Provide validation results in a structured format with:
- Overall status (VALID, INVALID, WARNINGS)
- List of errors (blocking issues)
- List of warnings (non-blocking issues)
- Recommendations for improvement
- Confidence score (0-1)
"""


class ValidationResult:
    """Structured validation result."""

    def __init__(
        self,
        status: str,
        errors: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]],
        recommendations: List[str],
        confidence: float
    ):
        self.status = status
        self.errors = errors
        self.warnings = warnings
        self.recommendations = recommendations
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "is_valid": self.status != "INVALID"
        }


class SchemaValidatorAgent(BaseOpenForgeAgent):
    """
    Agent that validates ontology schemas against requirements.

    This agent performs comprehensive validation of LinkML schemas including
    structural validation, completeness checks, semantic validation, and
    best practices assessment.
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
        return "schema_validator"

    @property
    def description(self) -> str:
        return "Validates ontology schemas against requirements, checking for completeness and identifying potential issues."

    @property
    def required_inputs(self) -> List[str]:
        return ["ontology_schema", "requirements"]

    @property
    def output_keys(self) -> List[str]:
        return ["validation_result", "errors", "warnings", "recommendations", "is_valid"]

    @property
    def state_class(self) -> Type[DataArchitectState]:
        return DataArchitectState

    def get_system_prompt(self) -> str:
        return SCHEMA_VALIDATOR_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools for schema validation."""
        return []  # LLM-only agent for now

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for schema validation."""
        graph = StateGraph(DataArchitectState)

        # Add nodes
        graph.add_node("validate_structure", self._validate_structure)
        graph.add_node("validate_completeness", self._validate_completeness)
        graph.add_node("validate_semantics", self._validate_semantics)
        graph.add_node("check_best_practices", self._check_best_practices)
        graph.add_node("compile_results", self._compile_results)

        # Define edges
        graph.set_entry_point("validate_structure")
        graph.add_edge("validate_structure", "validate_completeness")
        graph.add_edge("validate_completeness", "validate_semantics")
        graph.add_edge("validate_semantics", "check_best_practices")
        graph.add_edge("check_best_practices", "compile_results")
        graph.add_edge("compile_results", END)

        return graph

    async def _validate_structure(self, state: DataArchitectState) -> Dict[str, Any]:
        """Validate the structural integrity of the schema."""
        context = state.get("agent_context", {})
        schema = context.get("ontology_schema", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Perform structural validation on this LinkML schema.

Schema:
```yaml
{schema}
```

Check for:
1. Valid YAML syntax
2. Required top-level elements (id, name, prefixes)
3. Well-formed class definitions
4. Valid slot definitions with proper ranges
5. Proper enum definitions
6. Valid type references

Report any structural errors or issues found.
Format: List each issue with severity (ERROR/WARNING) and description.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="structural_validation",
            description="Validated schema structural integrity",
            confidence=0.90,
            reasoning="Checked YAML syntax and required LinkML elements"
        )

        return {
            "outputs": {"structural_validation": response.content},
            "decisions": [decision],
            "current_step": "validate_structure",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _validate_completeness(self, state: DataArchitectState) -> Dict[str, Any]:
        """Validate schema completeness against requirements."""
        context = state.get("agent_context", {})
        schema = context.get("ontology_schema", "")
        requirements = context.get("requirements", [])

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate the schema completeness against the requirements.

Schema:
```yaml
{schema}
```

Requirements:
{requirements}

Check that:
1. All entities mentioned in requirements are defined as classes
2. All relationships from requirements are present as slots
3. All required properties are defined
4. Documentation is adequate for all elements
5. No requirements are missing from the schema

Report any completeness gaps found.
Format: List each gap with severity (ERROR/WARNING) and description.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="completeness_validation",
            description="Validated schema completeness against requirements",
            confidence=0.85,
            reasoning="Verified all required entities, relationships, and properties are present"
        )

        return {
            "outputs": {"completeness_validation": response.content},
            "decisions": [decision],
            "current_step": "validate_completeness",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _validate_semantics(self, state: DataArchitectState) -> Dict[str, Any]:
        """Validate semantic correctness of the schema."""
        context = state.get("agent_context", {})
        schema = context.get("ontology_schema", "")
        domain_context = context.get("domain_context", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate the semantic correctness of the schema.

Schema:
```yaml
{schema}
```

Domain Context:
{domain_context}

Check that:
1. Entity names accurately represent their domain concepts
2. Relationships are logically correct
3. Cardinality constraints make sense
4. Data types are appropriate for properties
5. No circular dependencies (unless intended)
6. Inheritance hierarchies are meaningful

Report any semantic issues found.
Format: List each issue with severity (ERROR/WARNING) and description.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="semantic_validation",
            description="Validated schema semantic correctness",
            confidence=0.80,
            reasoning="Verified logical consistency of entities, relationships, and constraints"
        )

        return {
            "outputs": {"semantic_validation": response.content},
            "decisions": [decision],
            "current_step": "validate_semantics",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _check_best_practices(self, state: DataArchitectState) -> Dict[str, Any]:
        """Check schema against best practices."""
        context = state.get("agent_context", {})
        schema = context.get("ontology_schema", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Check the schema against LinkML and ontology design best practices.

Schema:
```yaml
{schema}
```

Check for:
1. Naming conventions (PascalCase for classes, snake_case for properties)
2. Proper use of inheritance and mixins
3. Appropriate use of enums for controlled vocabularies
4. Clear and consistent descriptions
5. Proper use of identifiers
6. Appropriate default values
7. Documentation quality

Report any best practice violations.
Format: List each issue with severity (ERROR/WARNING) and recommendation.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="best_practices_check",
            description="Checked schema against best practices",
            confidence=0.85,
            reasoning="Verified naming conventions, documentation, and design patterns"
        )

        return {
            "outputs": {"best_practices_check": response.content},
            "decisions": [decision],
            "current_step": "check_best_practices",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _compile_results(self, state: DataArchitectState) -> Dict[str, Any]:
        """Compile all validation results into final report."""
        outputs = state.get("outputs", {})

        structural = outputs.get("structural_validation", "")
        completeness = outputs.get("completeness_validation", "")
        semantic = outputs.get("semantic_validation", "")
        best_practices = outputs.get("best_practices_check", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Compile the validation results into a final comprehensive report.

Structural Validation:
{structural}

Completeness Validation:
{completeness}

Semantic Validation:
{semantic}

Best Practices Check:
{best_practices}

Create a final validation report with:
1. Overall status: VALID, INVALID, or WARNINGS
2. Summary of all errors (blocking issues that must be fixed)
3. Summary of all warnings (non-blocking issues to consider)
4. Prioritized list of recommendations
5. Overall confidence score (0-1)

Format as JSON with the following structure:
{{
    "status": "VALID|INVALID|WARNINGS",
    "errors": [
        {{"category": "...", "description": "...", "severity": "error", "location": "..."}}
    ],
    "warnings": [
        {{"category": "...", "description": "...", "severity": "warning", "location": "..."}}
    ],
    "recommendations": ["..."],
    "confidence": 0.0-1.0,
    "summary": "..."
}}""")
        ]

        response = await self.llm.ainvoke(messages)

        # Determine if human review is needed
        response_lower = response.content.lower()
        has_errors = "invalid" in response_lower or '"severity": "error"' in response_lower
        has_warnings = "warnings" in response_lower

        confidence = 0.95 if not has_errors else 0.70

        decision = add_decision(
            state,
            decision_type="validation_compilation",
            description="Compiled final validation report",
            confidence=confidence,
            reasoning="Combined all validation results into comprehensive report",
            requires_approval=has_errors
        )

        review_items = []
        if has_errors:
            review_items.append(mark_for_review(
                state,
                item_type="schema_validation",
                item_id="validation_errors",
                description="Schema has validation errors that need to be addressed",
                priority="high"
            ))
        elif has_warnings:
            review_items.append(mark_for_review(
                state,
                item_type="schema_validation",
                item_id="validation_warnings",
                description="Schema has warnings that may need review",
                priority="medium"
            ))

        return {
            "outputs": {
                "validation_result": response.content,
                "is_valid": not has_errors,
                "has_warnings": has_warnings
            },
            "validation_results": {
                "raw_report": response.content,
                "is_valid": not has_errors,
                "has_warnings": has_warnings
            },
            "decisions": [decision],
            "requires_human_review": has_errors,
            "review_items": review_items,
            "current_step": "compile_results",
            "messages": [Message(role="assistant", content=response.content)]
        }
