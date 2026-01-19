"""
Data Architect Cluster

Orchestrates the data architect agents for ontology design and transformation specification.
Manages iterative refinement workflow and produces final outputs.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from enum import Enum

from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.state_management import (
    DataArchitectState,
    Decision,
    Message,
    add_decision,
    mark_for_review,
    create_initial_state
)
from contracts.agent_interface import AgentInput, AgentOutput

from .ontology_designer_agent import OntologyDesignerAgent
from .schema_validator_agent import SchemaValidatorAgent
from .transformation_agent import TransformationDesignerAgent


class ClusterPhase(str, Enum):
    """Phases in the data architect workflow."""
    DESIGN = "design"
    VALIDATE = "validate"
    TRANSFORM = "transform"
    FINALIZE = "finalize"


class DataArchitectCluster:
    """
    Orchestrates the data architect agent cluster.

    This cluster manages the workflow for:
    1. Designing ontology schemas from requirements
    2. Validating schemas for completeness and correctness
    3. Designing data transformation pipelines
    4. Iterative refinement based on validation feedback

    The cluster produces:
    - LinkML-compatible ontology schema (YAML)
    - ETL specification for data transformation (YAML)
    - Validation reports
    - Design decisions and documentation
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

        # Initialize specialist agents
        self.ontology_designer = OntologyDesignerAgent(llm, memory, config)
        self.schema_validator = SchemaValidatorAgent(llm, memory, config)
        self.transformation_designer = TransformationDesignerAgent(llm, memory, config)

        self._graph: Optional[StateGraph] = None
        self._compiled_graph = None

    @property
    def name(self) -> str:
        return "data_architect_cluster"

    @property
    def description(self) -> str:
        return "Orchestrates ontology design, validation, and transformation specification"

    def get_agents(self) -> List[Any]:
        """Return list of agents in this cluster."""
        return [
            self.ontology_designer,
            self.schema_validator,
            self.transformation_designer
        ]

    def build_graph(self) -> StateGraph:
        """Build the cluster workflow graph."""
        graph = StateGraph(DataArchitectState)

        # Add nodes for each phase
        graph.add_node("design_ontology", self._design_ontology_phase)
        graph.add_node("validate_schema", self._validate_schema_phase)
        graph.add_node("handle_validation_feedback", self._handle_validation_feedback)
        graph.add_node("design_transformations", self._design_transformations_phase)
        graph.add_node("finalize_outputs", self._finalize_outputs)

        # Define workflow edges
        graph.set_entry_point("design_ontology")
        graph.add_edge("design_ontology", "validate_schema")
        graph.add_conditional_edges(
            "validate_schema",
            self._route_after_validation,
            {
                "refinement_needed": "handle_validation_feedback",
                "validation_passed": "design_transformations"
            }
        )
        graph.add_edge("handle_validation_feedback", "design_ontology")
        graph.add_edge("design_transformations", "finalize_outputs")
        graph.add_edge("finalize_outputs", END)

        return graph

    def compile(self):
        """Compile the graph for execution."""
        if self._compiled_graph is None:
            if self._graph is None:
                self._graph = self.build_graph()
            self._compiled_graph = self._graph.compile(checkpointer=self.memory)
        return self._compiled_graph

    async def run(self, input: AgentInput) -> AgentOutput:
        """Execute the cluster workflow."""
        # Validate input
        required_keys = ["requirements", "domain_context"]
        for key in required_keys:
            if key not in input.context:
                return AgentOutput(
                    agent_name=self.name,
                    timestamp=datetime.utcnow(),
                    success=False,
                    outputs={},
                    decisions=[],
                    confidence=0.0,
                    requires_human_review=False,
                    errors=[f"Missing required input: {key}"]
                )

        # Create initial state
        initial_state = self._create_initial_state(input)

        # Run the workflow
        compiled = self.compile()
        config = {"configurable": {"thread_id": input.engagement_id}}

        try:
            final_state = await compiled.ainvoke(initial_state, config)

            return AgentOutput(
                agent_name=self.name,
                timestamp=datetime.utcnow(),
                success=len(final_state.get("errors", [])) == 0,
                outputs=final_state.get("outputs", {}),
                decisions=[d.model_dump() for d in final_state.get("decisions", [])],
                confidence=self._calculate_confidence(final_state),
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
                    "description": f"Cluster execution failed: {str(e)}",
                    "priority": "high"
                }],
                errors=[str(e)]
            )

    def _create_initial_state(self, input: AgentInput) -> DataArchitectState:
        """Create initial state for the cluster workflow."""
        return DataArchitectState(
            engagement_id=input.engagement_id,
            phase=input.phase,
            messages=[],
            outputs={},
            decisions=[],
            current_step="start",
            requires_human_review=False,
            review_items=[],
            errors=[],
            agent_context={
                "requirements": input.context.get("requirements", []),
                "domain_context": input.context.get("domain_context", {}),
                "source_data_info": input.context.get("source_data_info", {}),
                "schema_name": input.context.get("schema_name", "OpenForgeOntology"),
                "schema_prefix": input.context.get("schema_prefix", "of"),
                "iteration_count": 0,
                "max_iterations": self.config.get("max_iterations", 3),
                "previous_outputs": input.previous_outputs or {},
                "human_inputs": input.human_inputs or []
            },
            ontology_draft=None,
            schema_definitions={},
            data_models=[],
            validation_results={}
        )

    async def _design_ontology_phase(self, state: DataArchitectState) -> Dict[str, Any]:
        """Execute the ontology design phase."""
        context = state.get("agent_context", {})

        # Create input for ontology designer
        designer_input = AgentInput(
            engagement_id=state["engagement_id"],
            phase=ClusterPhase.DESIGN.value,
            context={
                "requirements": context.get("requirements", []),
                "domain_context": context.get("domain_context", {}),
                "schema_name": context.get("schema_name", "OpenForgeOntology"),
                "schema_prefix": context.get("schema_prefix", "of")
            },
            previous_outputs=context.get("previous_outputs"),
            human_inputs=context.get("human_inputs")
        )

        # Run ontology designer
        result = await self.ontology_designer.run(designer_input)

        # Extract outputs
        ontology_schema = result.outputs.get("ontology_schema", "")

        decision = add_decision(
            state,
            decision_type="phase_completion",
            description="Completed ontology design phase",
            confidence=result.confidence,
            reasoning="Ontology designer agent completed successfully"
        )

        return {
            "outputs": {
                "ontology_schema": ontology_schema,
                "entity_definitions": result.outputs.get("entity_definitions", ""),
                "relationship_map": result.outputs.get("relationship_definitions", ""),
                "design_decisions": result.decisions
            },
            "ontology_draft": {"schema_yaml": ontology_schema},
            "decisions": [decision],
            "current_step": "design_ontology",
            "messages": [Message(
                role="system",
                content=f"Ontology design completed with confidence: {result.confidence}"
            )]
        }

    async def _validate_schema_phase(self, state: DataArchitectState) -> Dict[str, Any]:
        """Execute the schema validation phase."""
        context = state.get("agent_context", {})
        outputs = state.get("outputs", {})

        # Create input for schema validator
        validator_input = AgentInput(
            engagement_id=state["engagement_id"],
            phase=ClusterPhase.VALIDATE.value,
            context={
                "ontology_schema": outputs.get("ontology_schema", ""),
                "requirements": context.get("requirements", []),
                "domain_context": context.get("domain_context", {})
            }
        )

        # Run schema validator
        result = await self.schema_validator.run(validator_input)

        # Extract validation results
        is_valid = result.outputs.get("is_valid", False)
        validation_result = result.outputs.get("validation_result", "")

        decision = add_decision(
            state,
            decision_type="phase_completion",
            description="Completed schema validation phase",
            confidence=result.confidence,
            reasoning=f"Schema validation {'passed' if is_valid else 'found issues'}"
        )

        return {
            "outputs": {
                "validation_result": validation_result,
                "is_valid": is_valid,
                "has_warnings": result.outputs.get("has_warnings", False)
            },
            "validation_results": {
                "is_valid": is_valid,
                "report": validation_result
            },
            "decisions": [decision],
            "requires_human_review": result.requires_human_review,
            "review_items": result.review_items or [],
            "current_step": "validate_schema",
            "messages": [Message(
                role="system",
                content=f"Schema validation completed: {'VALID' if is_valid else 'INVALID'}"
            )]
        }

    async def _handle_validation_feedback(self, state: DataArchitectState) -> Dict[str, Any]:
        """Handle validation feedback and prepare for refinement."""
        context = state.get("agent_context", {})
        outputs = state.get("outputs", {})

        # Increment iteration count
        iteration_count = context.get("iteration_count", 0) + 1

        # Store validation feedback for next design iteration
        validation_feedback = outputs.get("validation_result", "")

        decision = add_decision(
            state,
            decision_type="refinement",
            description=f"Initiating ontology refinement (iteration {iteration_count})",
            confidence=0.75,
            reasoning="Validation identified issues that need to be addressed"
        )

        # Update context for next iteration
        updated_context = {
            **context,
            "iteration_count": iteration_count,
            "previous_outputs": {
                "ontology_schema": outputs.get("ontology_schema", ""),
                "validation_feedback": validation_feedback
            }
        }

        return {
            "agent_context": updated_context,
            "decisions": [decision],
            "current_step": "handle_validation_feedback",
            "messages": [Message(
                role="system",
                content=f"Starting refinement iteration {iteration_count}"
            )]
        }

    def _route_after_validation(self, state: DataArchitectState) -> str:
        """Route based on validation results."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})

        is_valid = outputs.get("is_valid", False)
        iteration_count = context.get("iteration_count", 0)
        max_iterations = context.get("max_iterations", 3)

        if is_valid:
            return "validation_passed"
        elif iteration_count < max_iterations:
            return "refinement_needed"
        else:
            # Max iterations reached, proceed anyway but flag for review
            return "validation_passed"

    async def _design_transformations_phase(self, state: DataArchitectState) -> Dict[str, Any]:
        """Execute the transformation design phase."""
        context = state.get("agent_context", {})
        outputs = state.get("outputs", {})

        # Create input for transformation designer
        transformation_input = AgentInput(
            engagement_id=state["engagement_id"],
            phase=ClusterPhase.TRANSFORM.value,
            context={
                "ontology_schema": outputs.get("ontology_schema", ""),
                "source_data_info": context.get("source_data_info", {}),
                "requirements": context.get("requirements", []),
                "spec_name": f"{context.get('schema_name', 'ontology')}_etl",
                "spec_version": "1.0.0"
            }
        )

        # Run transformation designer
        result = await self.transformation_designer.run(transformation_input)

        decision = add_decision(
            state,
            decision_type="phase_completion",
            description="Completed transformation design phase",
            confidence=result.confidence,
            reasoning="Transformation designer agent completed successfully"
        )

        return {
            "outputs": {
                "etl_specification": result.outputs.get("etl_specification", ""),
                "field_mappings": result.outputs.get("field_mappings", ""),
                "transformation_rules": result.outputs.get("transformation_rules", ""),
                "validation_rules": result.outputs.get("validation_rules", "")
            },
            "decisions": [decision],
            "requires_human_review": result.requires_human_review,
            "review_items": result.review_items or [],
            "current_step": "design_transformations",
            "messages": [Message(
                role="system",
                content=f"Transformation design completed with confidence: {result.confidence}"
            )]
        }

    async def _finalize_outputs(self, state: DataArchitectState) -> Dict[str, Any]:
        """Finalize and package all outputs."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        decisions = state.get("decisions", [])

        # Package final outputs
        final_outputs = {
            "ontology": {
                "schema_yaml": outputs.get("ontology_schema", ""),
                "entity_definitions": outputs.get("entity_definitions", ""),
                "relationship_map": outputs.get("relationship_map", "")
            },
            "transformation": {
                "etl_specification": outputs.get("etl_specification", ""),
                "field_mappings": outputs.get("field_mappings", ""),
                "transformation_rules": outputs.get("transformation_rules", ""),
                "validation_rules": outputs.get("validation_rules", "")
            },
            "validation": {
                "result": outputs.get("validation_result", ""),
                "is_valid": outputs.get("is_valid", False)
            },
            "metadata": {
                "schema_name": context.get("schema_name", "OpenForgeOntology"),
                "schema_prefix": context.get("schema_prefix", "of"),
                "iterations": context.get("iteration_count", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        # Calculate overall confidence
        decision_confidences = [d.confidence for d in decisions if hasattr(d, 'confidence')]
        overall_confidence = sum(decision_confidences) / len(decision_confidences) if decision_confidences else 0.0

        decision = add_decision(
            state,
            decision_type="phase_completion",
            description="Finalized all cluster outputs",
            confidence=overall_confidence,
            reasoning="All phases completed and outputs packaged"
        )

        # Determine if human review is needed
        is_valid = outputs.get("is_valid", False)
        has_warnings = outputs.get("has_warnings", False)
        needs_review = not is_valid or has_warnings

        review_items = []
        if needs_review:
            review_items.append(mark_for_review(
                state,
                item_type="cluster_outputs",
                item_id="final_review",
                description="Final outputs ready for review",
                priority="medium" if has_warnings else "high"
            ))

        return {
            "outputs": final_outputs,
            "decisions": [decision],
            "requires_human_review": needs_review,
            "review_items": review_items,
            "current_step": "finalize",
            "messages": [Message(
                role="system",
                content="Data architect cluster workflow completed"
            )]
        }

    def _calculate_confidence(self, state: DataArchitectState) -> float:
        """Calculate overall confidence from decisions."""
        decisions = state.get("decisions", [])
        if not decisions:
            return 0.0
        confidences = [d.confidence for d in decisions if hasattr(d, 'confidence')]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def _get_next_action(self, state: DataArchitectState) -> Optional[str]:
        """Determine suggested next action based on state."""
        if state.get("requires_human_review"):
            return "await_human_review"
        if state.get("errors"):
            return "handle_errors"
        return "proceed_to_app_builder"


# Convenience function for creating the cluster
def create_data_architect_cluster(
    llm: BaseChatModel,
    memory: Optional[MemorySaver] = None,
    config: Optional[Dict[str, Any]] = None
) -> DataArchitectCluster:
    """Create a configured DataArchitectCluster instance."""
    default_config = {
        "max_iterations": 3,
        "validation_threshold": 0.8
    }
    if config:
        default_config.update(config)
    return DataArchitectCluster(llm, memory, default_config)
