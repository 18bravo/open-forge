"""
Visual function builder support.

This module provides utilities for building logic functions
through a visual interface.
"""

from typing import Any

from forge_ai.logic.functions import (
    LogicFunction,
    OutputField,
    OutputFieldType,
    VariableBinding,
    VariableSource,
)


class FunctionBuilder:
    """
    Builder for creating logic functions programmatically.

    Provides a fluent interface for constructing logic functions,
    which can be used by visual builder UIs or programmatically.
    """

    def __init__(self, name: str, ontology_id: str):
        """
        Start building a new logic function.

        Args:
            name: The function name.
            ontology_id: The ontology ID this function belongs to.
        """
        self._function = LogicFunction(
            name=name,
            ontology_id=ontology_id,
            description="",
        )

    def description(self, description: str) -> "FunctionBuilder":
        """Set the function description."""
        self._function.description = description
        return self

    def model(self, model: str) -> "FunctionBuilder":
        """Set the LLM model to use."""
        self._function.model = model
        return self

    def temperature(self, temperature: float) -> "FunctionBuilder":
        """Set the temperature for generation."""
        self._function.temperature = temperature
        return self

    def max_tokens(self, max_tokens: int) -> "FunctionBuilder":
        """Set the maximum tokens for generation."""
        self._function.max_tokens = max_tokens
        return self

    def add_variable(
        self,
        name: str,
        source: VariableSource,
        *,
        object_type: str | None = None,
        property_path: str | None = None,
        description: str | None = None,
        required: bool = True,
        default_value: Any | None = None,
    ) -> "FunctionBuilder":
        """Add a variable binding to the function."""
        self._function.variables.append(
            VariableBinding(
                name=name,
                source=source,
                object_type=object_type,
                property_path=property_path,
                description=description,
                required=required,
                default_value=default_value,
            )
        )
        return self

    def add_input_variable(
        self,
        name: str,
        description: str | None = None,
        required: bool = True,
        default_value: Any | None = None,
    ) -> "FunctionBuilder":
        """Add a user input variable."""
        return self.add_variable(
            name=name,
            source=VariableSource.USER_INPUT,
            description=description,
            required=required,
            default_value=default_value,
        )

    def add_ontology_variable(
        self,
        name: str,
        object_type: str,
        property_path: str | None = None,
        description: str | None = None,
    ) -> "FunctionBuilder":
        """Add an ontology object variable."""
        return self.add_variable(
            name=name,
            source=VariableSource.ONTOLOGY_OBJECT,
            object_type=object_type,
            property_path=property_path,
            description=description,
        )

    def prompt(self, template: str) -> "FunctionBuilder":
        """Set the prompt template (supports Jinja2)."""
        self._function.prompt_template = template
        return self

    def add_output_field(
        self,
        name: str,
        field_type: OutputFieldType,
        description: str,
        *,
        required: bool = True,
        enum: list[str] | None = None,
        examples: list[Any] | None = None,
    ) -> "FunctionBuilder":
        """Add an output field to the schema."""
        self._function.output_schema.append(
            OutputField(
                name=name,
                type=field_type,
                description=description,
                required=required,
                enum=enum,
                examples=examples,
            )
        )
        return self

    def add_string_output(
        self,
        name: str,
        description: str,
        enum: list[str] | None = None,
    ) -> "FunctionBuilder":
        """Add a string output field."""
        return self.add_output_field(
            name=name,
            field_type=OutputFieldType.STRING,
            description=description,
            enum=enum,
        )

    def add_boolean_output(
        self,
        name: str,
        description: str,
    ) -> "FunctionBuilder":
        """Add a boolean output field."""
        return self.add_output_field(
            name=name,
            field_type=OutputFieldType.BOOLEAN,
            description=description,
        )

    def add_number_output(
        self,
        name: str,
        description: str,
    ) -> "FunctionBuilder":
        """Add a number output field."""
        return self.add_output_field(
            name=name,
            field_type=OutputFieldType.NUMBER,
            description=description,
        )

    def enable_rag(
        self,
        query_template: str | None = None,
        object_types: list[str] | None = None,
        top_k: int = 5,
    ) -> "FunctionBuilder":
        """Enable RAG retrieval for this function."""
        self._function.rag_enabled = True
        self._function.rag_query_template = query_template
        self._function.rag_object_types = object_types
        self._function.rag_top_k = top_k
        return self

    def include_schema(self, include: bool = True) -> "FunctionBuilder":
        """Set whether to include ontology schema in context."""
        self._function.include_schema = include
        return self

    def tags(self, *tags: str) -> "FunctionBuilder":
        """Add tags to the function."""
        self._function.tags.extend(tags)
        return self

    def category(self, category: str) -> "FunctionBuilder":
        """Set the function category."""
        self._function.category = category
        return self

    def created_by(self, user_id: str) -> "FunctionBuilder":
        """Set the creator of the function."""
        self._function.created_by = user_id
        return self

    def build(self) -> LogicFunction:
        """Build and return the logic function."""
        return self._function

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FunctionBuilder":
        """Create a builder from a dictionary (e.g., from JSON)."""
        builder = cls(
            name=data.get("name", ""),
            ontology_id=data.get("ontology_id", ""),
        )

        if "description" in data:
            builder.description(data["description"])
        if "model" in data:
            builder.model(data["model"])
        if "temperature" in data:
            builder.temperature(data["temperature"])
        if "prompt_template" in data:
            builder.prompt(data["prompt_template"])

        for var_data in data.get("variables", []):
            builder.add_variable(
                name=var_data["name"],
                source=VariableSource(var_data["source"]),
                object_type=var_data.get("object_type"),
                property_path=var_data.get("property_path"),
                description=var_data.get("description"),
                required=var_data.get("required", True),
                default_value=var_data.get("default_value"),
            )

        for field_data in data.get("output_schema", []):
            builder.add_output_field(
                name=field_data["name"],
                field_type=OutputFieldType(field_data["type"]),
                description=field_data["description"],
                required=field_data.get("required", True),
                enum=field_data.get("enum"),
                examples=field_data.get("examples"),
            )

        return builder


def create_classification_function(
    name: str,
    ontology_id: str,
    categories: list[str],
    description: str = "",
) -> LogicFunction:
    """
    Create a text classification function.

    Utility function for creating common classification tasks.
    """
    return (
        FunctionBuilder(name, ontology_id)
        .description(description or f"Classify text into: {', '.join(categories)}")
        .add_input_variable("text", "The text to classify")
        .prompt(
            f"""Classify the following text into one of these categories: {', '.join(categories)}

Text: {{{{ text }}}}

Respond with the classification."""
        )
        .add_string_output(
            "category",
            f"The category (one of: {', '.join(categories)})",
            enum=categories,
        )
        .add_number_output(
            "confidence",
            "Confidence score from 0.0 to 1.0",
        )
        .temperature(0.1)
        .build()
    )


def create_extraction_function(
    name: str,
    ontology_id: str,
    fields: list[tuple[str, str]],  # (field_name, description)
    description: str = "",
) -> LogicFunction:
    """
    Create an entity extraction function.

    Utility function for creating common extraction tasks.
    """
    builder = (
        FunctionBuilder(name, ontology_id)
        .description(description or "Extract structured information from text")
        .add_input_variable("text", "The text to extract from")
        .temperature(0.1)
    )

    field_list = "\n".join(f"- {name}: {desc}" for name, desc in fields)
    builder.prompt(
        f"""Extract the following information from the text:

{field_list}

Text: {{{{ text }}}}

Extract all available information."""
    )

    for field_name, field_desc in fields:
        builder.add_string_output(field_name, field_desc, required=False)

    return builder.build()
