"""
Logic function definitions for no-code LLM functions.

This module defines the data models for no-code LLM functions that can be
created through a visual builder and executed without writing code.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class VariableSource(str, Enum):
    """Source of a variable binding."""

    ONTOLOGY_OBJECT = "ontology_object"
    ONTOLOGY_PROPERTY = "ontology_property"
    USER_INPUT = "user_input"
    CONSTANT = "constant"
    CONTEXT = "context"
    PREVIOUS_OUTPUT = "previous_output"


class OutputFieldType(str, Enum):
    """Type of an output field."""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class VariableBinding(BaseModel):
    """
    A variable binding for a logic function.

    Variables can be bound to ontology objects, user inputs, constants, etc.
    """

    name: str
    source: VariableSource
    object_type: str | None = None
    property_path: str | None = None
    description: str | None = None
    required: bool = True
    default_value: Any | None = None

    # For user input variables
    input_type: str = "string"
    input_validation: dict[str, Any] | None = None


class OutputField(BaseModel):
    """
    An output field definition for structured LLM output.

    Defines the schema for the JSON output the LLM should produce.
    """

    name: str
    type: OutputFieldType
    description: str
    required: bool = True
    enum: list[str] | None = None
    items: "OutputField | None" = None  # For array types
    properties: list["OutputField"] | None = None  # For object types
    examples: list[Any] | None = None


class PromptSection(BaseModel):
    """A section of the prompt template."""

    type: str  # 'text', 'variable', 'condition', 'loop'
    content: str | None = None
    variable: str | None = None
    condition: str | None = None
    items: list["PromptSection"] | None = None


class LogicFunction(BaseModel):
    """
    A no-code LLM function definition.

    Logic functions allow users to create reusable LLM operations
    without writing code, using a visual builder interface.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    ontology_id: str

    # Model configuration
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int | None = None

    # Variable bindings
    variables: list[VariableBinding] = Field(default_factory=list)

    # Prompt template (supports Jinja2)
    prompt_template: str = ""

    # Structured output schema
    output_schema: list[OutputField] = Field(default_factory=list)

    # Context configuration
    include_schema: bool = True
    rag_enabled: bool = False
    rag_query_template: str | None = None
    rag_object_types: list[str] | None = None
    rag_top_k: int = 5

    # Metadata
    created_by: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    published: bool = False

    # Tags and categorization
    tags: list[str] = Field(default_factory=list)
    category: str | None = None

    def get_json_schema(self) -> dict[str, Any]:
        """Convert output schema to JSON Schema format."""
        if not self.output_schema:
            return {"type": "object"}

        properties = {}
        required = []

        for field in self.output_schema:
            properties[field.name] = self._field_to_json_schema(field)
            if field.required:
                required.append(field.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def _field_to_json_schema(self, field: OutputField) -> dict[str, Any]:
        """Convert a single output field to JSON Schema."""
        schema: dict[str, Any] = {
            "type": field.type.value,
            "description": field.description,
        }

        if field.enum:
            schema["enum"] = field.enum

        if field.type == OutputFieldType.ARRAY and field.items:
            schema["items"] = self._field_to_json_schema(field.items)

        if field.type == OutputFieldType.OBJECT and field.properties:
            schema["properties"] = {
                p.name: self._field_to_json_schema(p) for p in field.properties
            }
            schema["required"] = [p.name for p in field.properties if p.required]

        if field.examples:
            schema["examples"] = field.examples

        return schema


@dataclass
class LogicFunctionResult:
    """Result of executing a logic function."""

    success: bool
    output: dict[str, Any] | None = None
    error: str | None = None

    # Execution metadata
    function_id: str = ""
    function_version: int = 1
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    executed_at: datetime = field(default_factory=datetime.utcnow)

    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Performance
    latency_ms: float = 0.0

    # Resolved variables (for debugging)
    resolved_variables: dict[str, Any] = field(default_factory=dict)

    # Raw response (for debugging)
    raw_response: str | None = None


class LogicFunctionStore:
    """
    Abstract store for logic functions.

    Stub implementation - would be backed by a database in production.
    """

    def __init__(self):
        self._functions: dict[str, LogicFunction] = {}

    async def save(self, function: LogicFunction) -> None:
        """Save a logic function."""
        function.updated_at = datetime.utcnow()
        self._functions[function.id] = function

    async def get(self, function_id: str) -> LogicFunction | None:
        """Get a logic function by ID."""
        return self._functions.get(function_id)

    async def list(
        self,
        ontology_id: str | None = None,
        published_only: bool = False,
        limit: int = 100,
    ) -> list[LogicFunction]:
        """List logic functions."""
        results = list(self._functions.values())

        if ontology_id:
            results = [f for f in results if f.ontology_id == ontology_id]
        if published_only:
            results = [f for f in results if f.published]

        return results[:limit]

    async def delete(self, function_id: str) -> bool:
        """Delete a logic function."""
        if function_id in self._functions:
            del self._functions[function_id]
            return True
        return False
