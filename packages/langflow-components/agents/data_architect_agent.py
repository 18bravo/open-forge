"""
Data Architect Agent Component for Langflow

Wraps the Open Forge Data Architect cluster as a Langflow component,
enabling visual workflow design for ontology design and transformation
specification.
"""
from typing import Any, Dict, List, Optional
import json

from langflow.custom import Component
from langflow.io import (
    MessageTextInput,
    StrInput,
    SecretStrInput,
    DictInput,
    Output,
    BoolInput,
    IntInput,
)
from langflow.schema import Message


class DataArchitectAgentComponent(Component):
    """
    Open Forge Data Architect Agent for Langflow.

    This component wraps the Data Architect cluster which coordinates:
    - Ontology Designer Agent
    - Schema Validator Agent
    - Transformation Designer Agent

    The Data Architect Agent analyzes requirements and produces:
    - LinkML-compatible ontology schema (YAML)
    - ETL specification for data transformation
    - Validation reports
    - Design decisions documentation
    """

    display_name = "Data Architect Agent"
    description = "Ontology design and data transformation specification agent cluster"
    icon = "database"
    name = "DataArchitectAgent"

    inputs = [
        MessageTextInput(
            name="input_text",
            display_name="Input",
            info="Design requirements or modification request",
            required=True,
        ),
        StrInput(
            name="engagement_id",
            display_name="Engagement ID",
            info="The Open Forge engagement context identifier",
            required=True,
        ),
        DictInput(
            name="requirements",
            display_name="Requirements",
            info="List of requirements from discovery phase",
            required=True,
            is_list=True,
        ),
        DictInput(
            name="domain_context",
            display_name="Domain Context",
            info="Domain-specific context and terminology",
            required=True,
        ),
        DictInput(
            name="source_data_info",
            display_name="Source Data Info",
            info="Information about source data systems (optional)",
            required=False,
        ),
        StrInput(
            name="schema_name",
            display_name="Schema Name",
            info="Name for the generated ontology schema",
            value="OpenForgeOntology",
            advanced=True,
        ),
        StrInput(
            name="schema_prefix",
            display_name="Schema Prefix",
            info="Prefix for schema identifiers",
            value="of",
            advanced=True,
        ),
        StrInput(
            name="openforge_api_url",
            display_name="Open Forge API URL",
            info="URL of the Open Forge API",
            value="http://localhost:8000",
            advanced=True,
        ),
        SecretStrInput(
            name="openforge_api_key",
            display_name="Open Forge API Key",
            info="API key for Open Forge authentication",
            advanced=True,
        ),
        IntInput(
            name="max_iterations",
            display_name="Max Iterations",
            info="Maximum refinement iterations for validation",
            value=3,
            advanced=True,
        ),
        IntInput(
            name="timeout_seconds",
            display_name="Timeout (seconds)",
            info="Maximum execution time in seconds",
            value=600,
            advanced=True,
        ),
    ]

    outputs = [
        Output(
            display_name="Architecture Output",
            name="architecture_output",
            method="run_architect",
        ),
        Output(
            display_name="Ontology Schema",
            name="ontology_schema",
            method="get_ontology_schema",
        ),
        Output(
            display_name="ETL Specification",
            name="etl_specification",
            method="get_etl_specification",
        ),
        Output(
            display_name="Validation Report",
            name="validation_report",
            method="get_validation_report",
        ),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._result: Optional[Dict[str, Any]] = None

    async def _execute_architect(self) -> Dict[str, Any]:
        """Execute the data architect cluster and cache results."""
        if self._result is not None:
            return self._result

        # Import here to avoid circular dependencies
        from agents.data_architect.cluster import DataArchitectCluster
        from contracts.agent_interface import AgentInput
        from langchain_anthropic import ChatAnthropic

        # Initialize LLM
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
        )

        # Create the data architect cluster
        cluster = DataArchitectCluster(
            llm=llm,
            config={"max_iterations": self.max_iterations},
        )

        # Build context from inputs
        context = {
            "requirements": self.requirements or [],
            "domain_context": self.domain_context or {},
            "source_data_info": self.source_data_info or {},
            "schema_name": self.schema_name,
            "schema_prefix": self.schema_prefix,
            "user_input": self.input_text,
        }

        # Create agent input
        agent_input = AgentInput(
            engagement_id=self.engagement_id,
            phase="data_architecture",
            context=context,
        )

        # Execute the cluster
        try:
            result = await cluster.run(agent_input)

            self._result = {
                "success": result.success,
                "outputs": result.outputs,
                "decisions": result.decisions,
                "confidence": result.confidence,
                "requires_human_review": result.requires_human_review,
                "review_items": result.review_items,
                "errors": result.errors,
                "next_suggested_action": result.next_suggested_action,
            }
        except Exception as e:
            self._result = {
                "success": False,
                "outputs": {},
                "decisions": [],
                "confidence": 0.0,
                "requires_human_review": True,
                "review_items": [
                    {
                        "type": "error",
                        "description": f"Data architecture execution failed: {str(e)}",
                        "priority": "high",
                    }
                ],
                "errors": [str(e)],
                "next_suggested_action": "handle_error",
            }

        return self._result

    async def run_architect(self) -> Message:
        """
        Execute the data architect agent cluster.

        Returns the complete architecture output including ontology schema,
        ETL specification, and validation results.
        """
        result = await self._execute_architect()

        # Format output as message
        if result["success"]:
            outputs = result["outputs"]
            content = json.dumps(
                {
                    "ontology": outputs.get("ontology", {}),
                    "transformation": outputs.get("transformation", {}),
                    "validation": outputs.get("validation", {}),
                    "metadata": outputs.get("metadata", {}),
                    "confidence": result["confidence"],
                    "decisions": result["decisions"],
                },
                indent=2,
                default=str,
            )
        else:
            content = json.dumps(
                {
                    "error": "Data architecture failed",
                    "errors": result["errors"],
                    "review_items": result["review_items"],
                },
                indent=2,
            )

        return Message(
            text=content,
            sender="DataArchitectAgent",
            sender_name="Data Architect Agent",
        )

    async def get_ontology_schema(self) -> Message:
        """Extract and return the ontology schema (YAML)."""
        result = await self._execute_architect()

        ontology = result["outputs"].get("ontology", {})
        schema_yaml = ontology.get("schema_yaml", "")

        return Message(
            text=schema_yaml if schema_yaml else json.dumps(ontology, indent=2),
            sender="DataArchitectAgent",
            sender_name="Data Architect Agent - Ontology Schema",
        )

    async def get_etl_specification(self) -> Message:
        """Extract and return the ETL specification."""
        result = await self._execute_architect()

        transformation = result["outputs"].get("transformation", {})
        etl_spec = transformation.get("etl_specification", "")

        return Message(
            text=etl_spec if etl_spec else json.dumps(transformation, indent=2),
            sender="DataArchitectAgent",
            sender_name="Data Architect Agent - ETL Specification",
        )

    async def get_validation_report(self) -> Message:
        """Extract and return the validation report."""
        result = await self._execute_architect()

        validation = result["outputs"].get("validation", {})

        return Message(
            text=json.dumps(validation, indent=2, default=str),
            sender="DataArchitectAgent",
            sender_name="Data Architect Agent - Validation Report",
        )
