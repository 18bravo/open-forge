"""
Pydantic model generator from LinkML schemas.
Generates Python Pydantic v2 models with full type hints and validation.
"""
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import re

from linkml_runtime.linkml_model import SchemaDefinition

from ontology.models import (
    OntologySchema,
    OntologyType,
    Property,
    PropertyType,
    Relationship,
    Cardinality,
    Constraint,
    ConstraintType,
)


# Mapping from PropertyType to Python type annotations
PROPERTY_TYPE_TO_PYTHON: Dict[PropertyType, str] = {
    PropertyType.STRING: "str",
    PropertyType.INTEGER: "int",
    PropertyType.FLOAT: "float",
    PropertyType.BOOLEAN: "bool",
    PropertyType.DATETIME: "datetime",
    PropertyType.DATE: "date",
    PropertyType.TIME: "time",
    PropertyType.UUID: "UUID",
    PropertyType.JSON: "Dict[str, Any]",
    PropertyType.ARRAY: "List",
    PropertyType.ENUM: "str",  # Will be replaced with actual Enum
}

# Imports needed for various types
TYPE_IMPORTS: Dict[PropertyType, str] = {
    PropertyType.DATETIME: "from datetime import datetime",
    PropertyType.DATE: "from datetime import date",
    PropertyType.TIME: "from datetime import time",
    PropertyType.UUID: "from uuid import UUID",
}


class PydanticGenerator:
    """Generates Python Pydantic models from ontology schemas."""

    def __init__(
        self,
        include_docstrings: bool = True,
        include_validators: bool = True,
        include_relationships: bool = True,
        base_class: str = "BaseModel",
        pydantic_version: int = 2
    ):
        """
        Initialize the Pydantic generator.

        Args:
            include_docstrings: Whether to include docstrings.
            include_validators: Whether to include field validators.
            include_relationships: Whether to include relationship fields.
            base_class: Base class name for generated models.
            pydantic_version: Pydantic version (1 or 2).
        """
        self.include_docstrings = include_docstrings
        self.include_validators = include_validators
        self.include_relationships = include_relationships
        self.base_class = base_class
        self.pydantic_version = pydantic_version

    def generate(self, ontology_schema: OntologySchema) -> str:
        """
        Generate Python code with Pydantic models from an ontology schema.

        Args:
            ontology_schema: The ontology schema to generate models for.

        Returns:
            Complete Python module string.
        """
        lines: List[str] = []

        # Header and imports
        lines.append(self._generate_header(ontology_schema))
        lines.append("")
        lines.append(self._generate_imports(ontology_schema))
        lines.append("")

        # Generate enums first
        enums = self._generate_enums(ontology_schema)
        if enums:
            lines.append(enums)
            lines.append("")

        # Generate base mixin classes for abstract types
        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                lines.append(self._generate_model(ontology_type, ontology_schema))
                lines.append("")

        # Generate concrete models
        for ontology_type in ontology_schema.types:
            if not ontology_type.abstract:
                lines.append(self._generate_model(ontology_type, ontology_schema))
                lines.append("")

        return "\n".join(lines)

    def _generate_header(self, ontology_schema: OntologySchema) -> str:
        """Generate module header."""
        return f'''"""
Pydantic models for: {ontology_schema.name}
Version: {ontology_schema.version}
Generated at: {datetime.now().isoformat()}
{f"Description: {ontology_schema.description}" if ontology_schema.description else ""}

This file is auto-generated. Do not edit directly.
"""'''

    def _generate_imports(self, ontology_schema: OntologySchema) -> str:
        """Generate import statements."""
        imports: Set[str] = set()

        # Standard library imports
        imports.add("from __future__ import annotations")
        imports.add("from typing import Any, Dict, List, Optional, Union")
        imports.add("from enum import Enum")

        # Pydantic imports
        if self.pydantic_version == 2:
            imports.add("from pydantic import BaseModel, Field, field_validator, model_validator")
        else:
            imports.add("from pydantic import BaseModel, Field, validator, root_validator")

        # Add type-specific imports
        for ontology_type in ontology_schema.types:
            for prop in ontology_type.properties:
                if prop.property_type in TYPE_IMPORTS:
                    imports.add(TYPE_IMPORTS[prop.property_type])

        # Sort imports
        sorted_imports = sorted(imports, key=lambda x: (
            0 if x.startswith("from __future__") else
            1 if x.startswith("from typing") else
            2 if x.startswith("from enum") else
            3 if x.startswith("from datetime") else
            4 if x.startswith("from uuid") else
            5 if x.startswith("from pydantic") else
            6
        ))

        return "\n".join(sorted_imports)

    def _generate_enums(self, ontology_schema: OntologySchema) -> str:
        """Generate Enum classes for enum properties."""
        enums: List[str] = []

        for ontology_type in ontology_schema.types:
            for prop in ontology_type.properties:
                if prop.property_type == PropertyType.ENUM and prop.enum_values:
                    enum_name = self._to_pascal_case(f"{ontology_type.name}_{prop.name}")
                    enum_def = self._generate_enum_class(enum_name, prop.enum_values, prop.description)
                    enums.append(enum_def)

        return "\n\n".join(enums)

    def _generate_enum_class(
        self,
        name: str,
        values: List[str],
        description: Optional[str]
    ) -> str:
        """Generate a single Enum class."""
        lines: List[str] = []
        lines.append(f"class {name}(str, Enum):")

        if self.include_docstrings and description:
            lines.append(f'    """{description}"""')

        for value in values:
            # Convert value to valid Python identifier
            identifier = self._to_snake_case(value).upper()
            lines.append(f'    {identifier} = "{value}"')

        return "\n".join(lines)

    def _generate_model(
        self,
        ontology_type: OntologyType,
        ontology_schema: OntologySchema
    ) -> str:
        """Generate a Pydantic model class."""
        lines: List[str] = []

        # Class definition
        base_classes = [self.base_class]
        if ontology_type.mixins:
            base_classes = ontology_type.mixins + base_classes

        bases_str = ", ".join(base_classes)
        lines.append(f"class {ontology_type.name}({bases_str}):")

        # Docstring
        if self.include_docstrings:
            doc = ontology_type.description or f"Model for {ontology_type.name}"
            lines.append(f'    """{doc}"""')
            lines.append("")

        # Fields
        fields = self._generate_fields(ontology_type, ontology_schema)
        if fields:
            lines.append(fields)
        else:
            lines.append("    pass")

        # Validators
        if self.include_validators:
            validators = self._generate_validators(ontology_type)
            if validators:
                lines.append("")
                lines.append(validators)

        # Model config
        config = self._generate_model_config(ontology_type)
        if config:
            lines.append("")
            lines.append(config)

        return "\n".join(lines)

    def _generate_fields(
        self,
        ontology_type: OntologyType,
        ontology_schema: OntologySchema
    ) -> str:
        """Generate field definitions for a model."""
        fields: List[str] = []

        for prop in ontology_type.properties:
            field_def = self._generate_field(prop, ontology_type)
            fields.append(field_def)

        # Add relationship fields if enabled
        if self.include_relationships:
            for rel in ontology_schema.relationships:
                if rel.source_type == ontology_type.name:
                    field_def = self._generate_relationship_field(rel)
                    fields.append(field_def)

        return "\n".join(fields)

    def _generate_field(self, prop: Property, ontology_type: OntologyType) -> str:
        """Generate a single field definition."""
        # Determine Python type
        python_type = self._get_python_type(prop, ontology_type)

        # Build Field() arguments
        field_args = self._get_field_args(prop)

        # Handle optional fields
        if not prop.required:
            if self.pydantic_version == 2:
                python_type = f"Optional[{python_type}]"
            else:
                python_type = f"Optional[{python_type}]"

        # Build the field definition
        if field_args:
            field_str = f"Field({', '.join(field_args)})"
            return f"    {prop.name}: {python_type} = {field_str}"
        elif not prop.required:
            return f"    {prop.name}: {python_type} = None"
        else:
            return f"    {prop.name}: {python_type}"

    def _get_python_type(self, prop: Property, ontology_type: OntologyType) -> str:
        """Get the Python type annotation for a property."""
        if prop.property_type == PropertyType.ENUM and prop.enum_values:
            enum_name = self._to_pascal_case(f"{ontology_type.name}_{prop.name}")
            return enum_name

        if prop.property_type == PropertyType.ARRAY:
            item_type = PROPERTY_TYPE_TO_PYTHON.get(
                prop.array_item_type or PropertyType.STRING,
                "Any"
            )
            return f"List[{item_type}]"

        return PROPERTY_TYPE_TO_PYTHON.get(prop.property_type, "Any")

    def _get_field_args(self, prop: Property) -> List[str]:
        """Get Field() arguments for a property."""
        args: List[str] = []

        # Default value
        if prop.default_value is not None:
            default_str = self._format_default_value(prop.default_value, prop.property_type)
            args.append(f"default={default_str}")
        elif not prop.required:
            args.append("default=None")

        # Description
        if prop.description:
            escaped_desc = prop.description.replace('"', '\\"')
            args.append(f'description="{escaped_desc}"')

        # Add constraints
        for constraint in prop.constraints:
            if constraint.constraint_type == ConstraintType.MIN_LENGTH and constraint.value is not None:
                args.append(f"min_length={constraint.value}")
            elif constraint.constraint_type == ConstraintType.MAX_LENGTH and constraint.value is not None:
                args.append(f"max_length={constraint.value}")
            elif constraint.constraint_type == ConstraintType.MIN_VALUE and constraint.value is not None:
                if self.pydantic_version == 2:
                    args.append(f"ge={constraint.value}")
                else:
                    args.append(f"ge={constraint.value}")
            elif constraint.constraint_type == ConstraintType.MAX_VALUE and constraint.value is not None:
                if self.pydantic_version == 2:
                    args.append(f"le={constraint.value}")
                else:
                    args.append(f"le={constraint.value}")
            elif constraint.constraint_type == ConstraintType.PATTERN and constraint.value is not None:
                args.append(f'pattern=r"{constraint.value}"')

        return args

    def _generate_relationship_field(self, rel: Relationship) -> str:
        """Generate a field for a relationship."""
        if rel.cardinality in [Cardinality.ONE_TO_MANY, Cardinality.MANY_TO_MANY]:
            type_str = f"List[{rel.target_type}]"
            default = "Field(default_factory=list"
        else:
            type_str = f"Optional[{rel.target_type}]"
            default = "Field(default=None"

        if rel.description:
            escaped_desc = rel.description.replace('"', '\\"')
            default += f', description="{escaped_desc}"'

        default += ")"

        return f"    {rel.name}: {type_str} = {default}"

    def _generate_validators(self, ontology_type: OntologyType) -> str:
        """Generate field validators."""
        validators: List[str] = []

        for prop in ontology_type.properties:
            validator_code = self._generate_property_validator(prop)
            if validator_code:
                validators.append(validator_code)

        return "\n\n".join(validators)

    def _generate_property_validator(self, prop: Property) -> Optional[str]:
        """Generate a validator for a property if needed."""
        checks: List[str] = []

        for constraint in prop.constraints:
            if constraint.constraint_type == ConstraintType.PATTERN and constraint.value:
                # Pattern validation
                pattern = constraint.value
                message = constraint.message or f"{prop.name} must match pattern {pattern}"
                checks.append(f'''        if v is not None and not re.match(r"{pattern}", v):
            raise ValueError("{message}")''')

        if not checks:
            return None

        if self.pydantic_version == 2:
            return f"""    @field_validator("{prop.name}")
    @classmethod
    def validate_{prop.name}(cls, v):
{chr(10).join(checks)}
        return v"""
        else:
            return f"""    @validator("{prop.name}")
    def validate_{prop.name}(cls, v):
{chr(10).join(checks)}
        return v"""

    def _generate_model_config(self, ontology_type: OntologyType) -> str:
        """Generate model configuration."""
        if self.pydantic_version == 2:
            return """    model_config = {
        "populate_by_name": True,
        "use_enum_values": True,
        "extra": "forbid",
    }"""
        else:
            return """    class Config:
        use_enum_values = True
        extra = "forbid"
        allow_population_by_field_name = True"""

    def _format_default_value(self, value: Any, property_type: PropertyType) -> str:
        """Format a default value for Python code."""
        if value is None:
            return "None"
        if property_type == PropertyType.STRING:
            return f'"{value}"'
        if property_type == PropertyType.BOOLEAN:
            return "True" if value else "False"
        if property_type in [PropertyType.INTEGER, PropertyType.FLOAT]:
            return str(value)
        if property_type == PropertyType.JSON:
            return repr(value)
        return repr(value)

    def _to_pascal_case(self, name: str) -> str:
        """Convert a name to PascalCase."""
        # Split on underscores and capitalize each part
        parts = name.split("_")
        return "".join(part.capitalize() for part in parts)

    def _to_snake_case(self, name: str) -> str:
        """Convert a name to snake_case."""
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        # Replace spaces and hyphens with underscores
        s3 = re.sub(r'[\s\-]+', '_', s2)
        return s3.lower()

    def generate_single_model(self, ontology_type: OntologyType) -> str:
        """
        Generate a single Pydantic model class.

        Args:
            ontology_type: The ontology type to generate.

        Returns:
            Python class definition string.
        """
        # Create a minimal schema to pass to _generate_model
        temp_schema = OntologySchema(
            name="temp",
            version="0.1.0",
            types=[ontology_type],
            relationships=[]
        )
        return self._generate_model(ontology_type, temp_schema)
