"""
Base generator class for code generation.
Provides common functionality for all generators.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path
import re

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ontology.models import (
    OntologySchema,
    OntologyType,
    Property,
    PropertyType,
    Relationship,
    Cardinality,
)
from codegen.models import (
    GeneratorType,
    OutputFile,
    EntityContext,
    TemplateContext,
)
from codegen.config import CodegenConfig


class BaseGenerator(ABC):
    """
    Abstract base class for code generators.

    Provides common utilities for:
    - Template loading and rendering
    - Name conversions (snake_case, PascalCase, etc.)
    - Type mappings
    - Entity context building
    """

    generator_type: GeneratorType

    def __init__(
        self,
        config: CodegenConfig,
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize the generator.

        Args:
            config: Code generation configuration.
            template_dir: Custom template directory. Defaults to package templates.
        """
        self.config = config

        # Set up template directory
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"
        self.template_dir = template_dir

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Register custom filters
        self._register_filters()

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters."""
        self.env.filters["snake_case"] = self.to_snake_case
        self.env.filters["pascal_case"] = self.to_pascal_case
        self.env.filters["camel_case"] = self.to_camel_case
        self.env.filters["pluralize"] = self.pluralize
        self.env.filters["singularize"] = self.singularize

    @abstractmethod
    def generate(self, schema: OntologySchema) -> List[OutputFile]:
        """
        Generate code from an ontology schema.

        Args:
            schema: The ontology schema to generate code for.

        Returns:
            List of generated output files.
        """
        pass

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a Jinja2 template with the given context.

        Args:
            template_name: Name of the template file.
            context: Template context dictionary.

        Returns:
            Rendered template string.
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def build_entity_context(
        self,
        ontology_type: OntologyType,
        schema: OntologySchema,
    ) -> EntityContext:
        """
        Build an EntityContext from an OntologyType.

        Args:
            ontology_type: The ontology type to process.
            schema: The full schema for relationship resolution.

        Returns:
            EntityContext with processed entity information.
        """
        # Process properties
        properties = []
        for prop in ontology_type.properties:
            properties.append(self._process_property(prop))

        # Process relationships
        relationships = []
        for rel in schema.relationships:
            if rel.source_type == ontology_type.name:
                relationships.append(self._process_relationship(rel))

        return EntityContext(
            name=ontology_type.name,
            name_snake=self.to_snake_case(ontology_type.name),
            name_plural=self.pluralize(ontology_type.name),
            name_plural_snake=self.to_snake_case(self.pluralize(ontology_type.name)),
            description=ontology_type.description,
            properties=properties,
            relationships=relationships,
            primary_key=ontology_type.primary_key,
            has_timestamps=True,  # Configurable per generator
            metadata=ontology_type.metadata,
        )

    def _process_property(self, prop: Property) -> Dict[str, Any]:
        """Process a property into a dictionary for template context."""
        return {
            "name": prop.name,
            "name_snake": self.to_snake_case(prop.name),
            "type": prop.property_type.value if isinstance(prop.property_type, PropertyType) else prop.property_type,
            "python_type": self.get_python_type(prop),
            "typescript_type": self.get_typescript_type(prop),
            "sqlalchemy_type": self.get_sqlalchemy_type(prop),
            "required": prop.required,
            "description": prop.description,
            "default": prop.default_value,
            "constraints": [
                {"type": c.constraint_type.value, "value": c.value}
                for c in prop.constraints
            ],
            "is_enum": prop.property_type == PropertyType.ENUM,
            "enum_values": prop.enum_values,
            "is_array": prop.property_type == PropertyType.ARRAY,
            "array_item_type": prop.array_item_type.value if prop.array_item_type else None,
        }

    def _process_relationship(self, rel: Relationship) -> Dict[str, Any]:
        """Process a relationship into a dictionary for template context."""
        cardinality = rel.cardinality.value if isinstance(rel.cardinality, Cardinality) else rel.cardinality
        return {
            "name": rel.name,
            "name_snake": self.to_snake_case(rel.name),
            "source_type": rel.source_type,
            "target_type": rel.target_type,
            "target_type_snake": self.to_snake_case(rel.target_type),
            "cardinality": cardinality,
            "is_many": cardinality in ["one_to_many", "many_to_many"],
            "is_required": rel.required,
            "description": rel.description,
            "inverse_name": rel.inverse_name,
        }

    def build_template_context(
        self,
        schema: OntologySchema,
        entities: Optional[List[EntityContext]] = None,
    ) -> TemplateContext:
        """
        Build a complete template context from a schema.

        Args:
            schema: The ontology schema.
            entities: Optional pre-built entity contexts.

        Returns:
            TemplateContext for template rendering.
        """
        if entities is None:
            entities = []
            for ontology_type in schema.types:
                if not ontology_type.abstract:
                    entities.append(self.build_entity_context(ontology_type, schema))

        return TemplateContext(
            schema_name=schema.name,
            schema_version=schema.version,
            namespace=schema.namespace,
            entities=entities,
        )

    # Type mapping methods
    def get_python_type(self, prop: Property) -> str:
        """Get Python type annotation for a property."""
        type_map = {
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
            PropertyType.ENUM: "str",
        }

        base_type = type_map.get(prop.property_type, "Any")

        if prop.property_type == PropertyType.ARRAY and prop.array_item_type:
            item_type = type_map.get(prop.array_item_type, "Any")
            base_type = f"List[{item_type}]"

        if not prop.required:
            return f"Optional[{base_type}]"

        return base_type

    def get_typescript_type(self, prop: Property) -> str:
        """Get TypeScript type for a property."""
        type_map = {
            PropertyType.STRING: "string",
            PropertyType.INTEGER: "number",
            PropertyType.FLOAT: "number",
            PropertyType.BOOLEAN: "boolean",
            PropertyType.DATETIME: "string",
            PropertyType.DATE: "string",
            PropertyType.TIME: "string",
            PropertyType.UUID: "string",
            PropertyType.JSON: "Record<string, unknown>",
            PropertyType.ARRAY: "unknown[]",
            PropertyType.ENUM: "string",
        }

        base_type = type_map.get(prop.property_type, "unknown")

        if prop.property_type == PropertyType.ARRAY and prop.array_item_type:
            item_type = type_map.get(prop.array_item_type, "unknown")
            base_type = f"{item_type}[]"

        if not prop.required:
            return f"{base_type} | null"

        return base_type

    def get_sqlalchemy_type(self, prop: Property) -> str:
        """Get SQLAlchemy type for a property."""
        type_map = {
            PropertyType.STRING: "String",
            PropertyType.INTEGER: "BigInteger",
            PropertyType.FLOAT: "Float",
            PropertyType.BOOLEAN: "Boolean",
            PropertyType.DATETIME: "DateTime(timezone=True)",
            PropertyType.DATE: "Date",
            PropertyType.TIME: "Time",
            PropertyType.UUID: "UUID",
            PropertyType.JSON: "JSONB",
            PropertyType.ARRAY: "JSONB",
            PropertyType.ENUM: "String",
        }
        return type_map.get(prop.property_type, "String")

    # Name conversion utilities
    @staticmethod
    def to_snake_case(name: str) -> str:
        """Convert a name to snake_case."""
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insert underscore before uppercase letters followed by lowercase
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        # Replace spaces and hyphens with underscores
        s3 = re.sub(r'[\s\-]+', '_', s2)
        return s3.lower()

    @staticmethod
    def to_pascal_case(name: str) -> str:
        """Convert a name to PascalCase."""
        # Split on underscores, spaces, or hyphens
        parts = re.split(r'[_\s\-]+', name)
        return "".join(part.capitalize() for part in parts)

    @staticmethod
    def to_camel_case(name: str) -> str:
        """Convert a name to camelCase."""
        pascal = BaseGenerator.to_pascal_case(name)
        if pascal:
            return pascal[0].lower() + pascal[1:]
        return ""

    @staticmethod
    def pluralize(name: str) -> str:
        """Simple English pluralization."""
        if not name:
            return name

        # Common irregular plurals
        irregulars = {
            "person": "people",
            "child": "children",
            "mouse": "mice",
            "goose": "geese",
            "man": "men",
            "woman": "women",
            "tooth": "teeth",
            "foot": "feet",
            "datum": "data",
            "analysis": "analyses",
            "crisis": "crises",
            "thesis": "theses",
            "phenomenon": "phenomena",
            "criterion": "criteria",
            "status": "statuses",
        }

        lower_name = name.lower()
        if lower_name in irregulars:
            # Preserve original case pattern
            result = irregulars[lower_name]
            if name[0].isupper():
                return result.capitalize()
            return result

        # Standard rules
        if name.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return name + 'es'
        elif name.endswith('y') and len(name) > 1 and name[-2] not in 'aeiou':
            return name[:-1] + 'ies'
        elif name.endswith('f'):
            return name[:-1] + 'ves'
        elif name.endswith('fe'):
            return name[:-2] + 'ves'
        else:
            return name + 's'

    @staticmethod
    def singularize(name: str) -> str:
        """Simple English singularization."""
        if not name:
            return name

        # Common irregular plurals (reverse)
        irregulars = {
            "people": "person",
            "children": "child",
            "mice": "mouse",
            "geese": "goose",
            "men": "man",
            "women": "woman",
            "teeth": "tooth",
            "feet": "foot",
            "data": "datum",
            "analyses": "analysis",
            "crises": "crisis",
            "theses": "thesis",
            "phenomena": "phenomenon",
            "criteria": "criterion",
            "statuses": "status",
        }

        lower_name = name.lower()
        if lower_name in irregulars:
            result = irregulars[lower_name]
            if name[0].isupper():
                return result.capitalize()
            return result

        # Standard rules
        if name.endswith('ies') and len(name) > 3:
            return name[:-3] + 'y'
        elif name.endswith('ves'):
            return name[:-3] + 'f'
        elif name.endswith('es') and len(name) > 2:
            if name[:-2].endswith(('s', 'x', 'z', 'ch', 'sh')):
                return name[:-2]
            return name[:-1]
        elif name.endswith('s') and not name.endswith('ss'):
            return name[:-1]

        return name
