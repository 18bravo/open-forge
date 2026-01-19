"""
TypeScript interface generator from LinkML schemas.
Generates TypeScript interfaces with full type definitions.
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


# Mapping from PropertyType to TypeScript types
PROPERTY_TYPE_TO_TS: Dict[PropertyType, str] = {
    PropertyType.STRING: "string",
    PropertyType.INTEGER: "number",
    PropertyType.FLOAT: "number",
    PropertyType.BOOLEAN: "boolean",
    PropertyType.DATETIME: "string",  # ISO datetime string
    PropertyType.DATE: "string",  # ISO date string
    PropertyType.TIME: "string",  # ISO time string
    PropertyType.UUID: "string",
    PropertyType.JSON: "Record<string, unknown>",
    PropertyType.ARRAY: "Array",
    PropertyType.ENUM: "string",  # Will be replaced with actual enum
}


class TypeScriptGenerator:
    """Generates TypeScript interfaces from ontology schemas."""

    def __init__(
        self,
        include_jsdoc: bool = True,
        include_readonly: bool = False,
        include_relationships: bool = True,
        use_strict_null_checks: bool = True,
        export_type: str = "interface",  # "interface" or "type"
        generate_zod_schemas: bool = False
    ):
        """
        Initialize the TypeScript generator.

        Args:
            include_jsdoc: Whether to include JSDoc comments.
            include_readonly: Whether to mark all properties as readonly.
            include_relationships: Whether to include relationship fields.
            use_strict_null_checks: Whether to use strict null checks (| null).
            export_type: Whether to use "interface" or "type" declarations.
            generate_zod_schemas: Whether to also generate Zod validation schemas.
        """
        self.include_jsdoc = include_jsdoc
        self.include_readonly = include_readonly
        self.include_relationships = include_relationships
        self.use_strict_null_checks = use_strict_null_checks
        self.export_type = export_type
        self.generate_zod_schemas = generate_zod_schemas

    def generate(self, ontology_schema: OntologySchema) -> str:
        """
        Generate TypeScript code from an ontology schema.

        Args:
            ontology_schema: The ontology schema to generate TypeScript for.

        Returns:
            Complete TypeScript module string.
        """
        lines: List[str] = []

        # Header
        lines.append(self._generate_header(ontology_schema))
        lines.append("")

        # Generate enums first
        enums = self._generate_enums(ontology_schema)
        if enums:
            lines.append(enums)
            lines.append("")

        # Generate interfaces for abstract types (as base interfaces)
        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                lines.append(self._generate_interface(ontology_type, ontology_schema))
                lines.append("")

        # Generate interfaces for concrete types
        for ontology_type in ontology_schema.types:
            if not ontology_type.abstract:
                lines.append(self._generate_interface(ontology_type, ontology_schema))
                lines.append("")

        # Generate utility types
        lines.append(self._generate_utility_types(ontology_schema))
        lines.append("")

        # Generate Zod schemas if enabled
        if self.generate_zod_schemas:
            lines.append(self._generate_zod_schemas(ontology_schema))
            lines.append("")

        return "\n".join(lines)

    def _generate_header(self, ontology_schema: OntologySchema) -> str:
        """Generate file header."""
        header = f"""/**
 * TypeScript interfaces for: {ontology_schema.name}
 * Version: {ontology_schema.version}
 * Generated at: {datetime.now().isoformat()}
 * {f"Description: {ontology_schema.description}" if ontology_schema.description else ""}
 *
 * This file is auto-generated. Do not edit directly.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
"""
        if self.generate_zod_schemas:
            header += "\nimport { z } from 'zod';\n"
        return header

    def _generate_enums(self, ontology_schema: OntologySchema) -> str:
        """Generate TypeScript enums for enum properties."""
        enums: List[str] = []

        for ontology_type in ontology_schema.types:
            for prop in ontology_type.properties:
                if prop.property_type == PropertyType.ENUM and prop.enum_values:
                    enum_name = self._to_pascal_case(f"{ontology_type.name}_{prop.name}")
                    enum_def = self._generate_enum(enum_name, prop.enum_values, prop.description)
                    enums.append(enum_def)

        return "\n\n".join(enums)

    def _generate_enum(
        self,
        name: str,
        values: List[str],
        description: Optional[str]
    ) -> str:
        """Generate a single TypeScript enum."""
        lines: List[str] = []

        if self.include_jsdoc and description:
            lines.append(f"/** {description} */")

        lines.append(f"export enum {name} {{")

        for value in values:
            # Convert to valid TypeScript identifier
            identifier = self._to_constant_case(value)
            lines.append(f'  {identifier} = "{value}",')

        lines.append("}")

        # Also generate a union type for flexibility
        union_values = " | ".join(f'"{v}"' for v in values)
        lines.append("")
        lines.append(f"export type {name}Value = {union_values};")

        return "\n".join(lines)

    def _generate_interface(
        self,
        ontology_type: OntologyType,
        ontology_schema: OntologySchema
    ) -> str:
        """Generate a TypeScript interface."""
        lines: List[str] = []

        # JSDoc comment
        if self.include_jsdoc:
            lines.append(self._generate_jsdoc(ontology_type))

        # Interface declaration
        extends = ""
        if ontology_type.mixins:
            extends = f" extends {', '.join(ontology_type.mixins)}"

        if self.export_type == "interface":
            lines.append(f"export interface {ontology_type.name}{extends} {{")
        else:
            if extends:
                lines.append(f"export type {ontology_type.name} = {' & '.join(ontology_type.mixins)} & {{")
            else:
                lines.append(f"export type {ontology_type.name} = {{")

        # Properties
        for prop in ontology_type.properties:
            prop_line = self._generate_property(prop, ontology_type)
            lines.append(f"  {prop_line}")

        # Relationship properties
        if self.include_relationships:
            for rel in ontology_schema.relationships:
                if rel.source_type == ontology_type.name:
                    rel_line = self._generate_relationship_property(rel)
                    lines.append(f"  {rel_line}")

        lines.append("}")

        return "\n".join(lines)

    def _generate_jsdoc(self, ontology_type: OntologyType) -> str:
        """Generate JSDoc comment for a type."""
        lines = ["/**"]

        if ontology_type.description:
            lines.append(f" * {ontology_type.description}")
        else:
            lines.append(f" * {ontology_type.name} entity")

        if ontology_type.abstract:
            lines.append(" * @abstract")

        lines.append(" */")
        return "\n".join(lines)

    def _generate_property(self, prop: Property, ontology_type: OntologyType) -> str:
        """Generate a property definition."""
        # Get TypeScript type
        ts_type = self._get_ts_type(prop, ontology_type)

        # Handle optionality
        optional = "?" if not prop.required else ""

        # Handle null union
        if not prop.required and self.use_strict_null_checks:
            ts_type = f"{ts_type} | null"

        # Handle readonly
        readonly = "readonly " if self.include_readonly else ""

        # JSDoc for property
        jsdoc = ""
        if self.include_jsdoc and prop.description:
            jsdoc = f"/** {prop.description} */\n  "

        return f"{jsdoc}{readonly}{prop.name}{optional}: {ts_type};"

    def _get_ts_type(self, prop: Property, ontology_type: OntologyType) -> str:
        """Get the TypeScript type for a property."""
        if prop.property_type == PropertyType.ENUM and prop.enum_values:
            enum_name = self._to_pascal_case(f"{ontology_type.name}_{prop.name}")
            return enum_name

        if prop.property_type == PropertyType.ARRAY:
            item_type = PROPERTY_TYPE_TO_TS.get(
                prop.array_item_type or PropertyType.STRING,
                "unknown"
            )
            return f"Array<{item_type}>"

        return PROPERTY_TYPE_TO_TS.get(prop.property_type, "unknown")

    def _generate_relationship_property(self, rel: Relationship) -> str:
        """Generate a property for a relationship."""
        if rel.cardinality in [Cardinality.ONE_TO_MANY, Cardinality.MANY_TO_MANY]:
            ts_type = f"Array<{rel.target_type}>"
        else:
            ts_type = rel.target_type
            if self.use_strict_null_checks and not rel.required:
                ts_type = f"{ts_type} | null"

        optional = "?" if not rel.required else ""
        readonly = "readonly " if self.include_readonly else ""

        jsdoc = ""
        if self.include_jsdoc and rel.description:
            jsdoc = f"/** {rel.description} */\n  "

        return f"{jsdoc}{readonly}{rel.name}{optional}: {ts_type};"

    def _generate_utility_types(self, ontology_schema: OntologySchema) -> str:
        """Generate utility types for the schema."""
        type_names = [t.name for t in ontology_schema.types if not t.abstract]

        lines: List[str] = []

        # Union of all entity types
        if type_names:
            lines.append("/** Union of all entity types */")
            union = " | ".join(type_names)
            lines.append(f"export type AnyEntity = {union};")
            lines.append("")

        # Type map
        lines.append("/** Map of type names to types */")
        lines.append("export interface TypeMap {")
        for name in type_names:
            lines.append(f"  {name}: {name};")
        lines.append("}")
        lines.append("")

        # Create/Update types (partial versions)
        lines.append("/** Partial types for create operations */")
        for name in type_names:
            lines.append(f"export type Create{name} = Omit<{name}, 'id'> & {{ id?: string }};")
        lines.append("")

        lines.append("/** Partial types for update operations */")
        for name in type_names:
            lines.append(f"export type Update{name} = Partial<{name}> & {{ id: string }};")

        return "\n".join(lines)

    def _generate_zod_schemas(self, ontology_schema: OntologySchema) -> str:
        """Generate Zod validation schemas."""
        lines: List[str] = []
        lines.append("// ============================================================================")
        lines.append("// Zod Validation Schemas")
        lines.append("// ============================================================================")
        lines.append("")

        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            lines.append(self._generate_zod_schema(ontology_type, ontology_schema))
            lines.append("")

        return "\n".join(lines)

    def _generate_zod_schema(
        self,
        ontology_type: OntologyType,
        ontology_schema: OntologySchema
    ) -> str:
        """Generate a Zod schema for a type."""
        lines: List[str] = []

        schema_name = f"{self._to_camel_case(ontology_type.name)}Schema"
        lines.append(f"export const {schema_name} = z.object({{")

        for prop in ontology_type.properties:
            zod_type = self._get_zod_type(prop, ontology_type)
            lines.append(f"  {prop.name}: {zod_type},")

        lines.append("});")

        # Export inferred type
        lines.append("")
        lines.append(f"export type {ontology_type.name}Validated = z.infer<typeof {schema_name}>;")

        return "\n".join(lines)

    def _get_zod_type(self, prop: Property, ontology_type: OntologyType) -> str:
        """Get the Zod type for a property."""
        # Base type
        base_type = self._get_zod_base_type(prop, ontology_type)

        # Add constraints
        constraints: List[str] = []

        for constraint in prop.constraints:
            if constraint.constraint_type == ConstraintType.MIN_LENGTH and constraint.value is not None:
                constraints.append(f".min({constraint.value})")
            elif constraint.constraint_type == ConstraintType.MAX_LENGTH and constraint.value is not None:
                constraints.append(f".max({constraint.value})")
            elif constraint.constraint_type == ConstraintType.MIN_VALUE and constraint.value is not None:
                constraints.append(f".min({constraint.value})")
            elif constraint.constraint_type == ConstraintType.MAX_VALUE and constraint.value is not None:
                constraints.append(f".max({constraint.value})")
            elif constraint.constraint_type == ConstraintType.PATTERN and constraint.value is not None:
                constraints.append(f".regex(/{constraint.value}/)")

        # Build full type
        full_type = base_type + "".join(constraints)

        # Handle optionality
        if not prop.required:
            full_type = f"{full_type}.optional().nullable()"

        return full_type

    def _get_zod_base_type(self, prop: Property, ontology_type: OntologyType) -> str:
        """Get the base Zod type for a property."""
        type_map = {
            PropertyType.STRING: "z.string()",
            PropertyType.INTEGER: "z.number().int()",
            PropertyType.FLOAT: "z.number()",
            PropertyType.BOOLEAN: "z.boolean()",
            PropertyType.DATETIME: "z.string().datetime()",
            PropertyType.DATE: "z.string().date()",
            PropertyType.TIME: "z.string().time()",
            PropertyType.UUID: "z.string().uuid()",
            PropertyType.JSON: "z.record(z.unknown())",
        }

        if prop.property_type == PropertyType.ENUM and prop.enum_values:
            values = ", ".join(f'"{v}"' for v in prop.enum_values)
            return f"z.enum([{values}])"

        if prop.property_type == PropertyType.ARRAY:
            item_type = type_map.get(prop.array_item_type or PropertyType.STRING, "z.unknown()")
            return f"z.array({item_type})"

        return type_map.get(prop.property_type, "z.unknown()")

    def _to_pascal_case(self, name: str) -> str:
        """Convert a name to PascalCase."""
        parts = re.split(r'[_\s-]+', name)
        return "".join(part.capitalize() for part in parts)

    def _to_camel_case(self, name: str) -> str:
        """Convert a name to camelCase."""
        pascal = self._to_pascal_case(name)
        return pascal[0].lower() + pascal[1:] if pascal else ""

    def _to_constant_case(self, name: str) -> str:
        """Convert a name to CONSTANT_CASE."""
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        # Replace spaces and hyphens
        s3 = re.sub(r'[\s\-]+', '_', s2)
        return s3.upper()

    def generate_api_types(self, ontology_schema: OntologySchema) -> str:
        """
        Generate API request/response types.

        Args:
            ontology_schema: The ontology schema.

        Returns:
            TypeScript code for API types.
        """
        lines: List[str] = []
        lines.append("// API Request/Response Types")
        lines.append("")

        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            name = ontology_type.name

            # List response
            lines.append(f"export interface {name}ListResponse {{")
            lines.append(f"  data: {name}[];")
            lines.append("  total: number;")
            lines.append("  page: number;")
            lines.append("  pageSize: number;")
            lines.append("}")
            lines.append("")

            # Single item response
            lines.append(f"export interface {name}Response {{")
            lines.append(f"  data: {name};")
            lines.append("}")
            lines.append("")

            # Query parameters
            lines.append(f"export interface {name}QueryParams {{")
            lines.append("  page?: number;")
            lines.append("  pageSize?: number;")
            lines.append("  sortBy?: string;")
            lines.append("  sortOrder?: 'asc' | 'desc';")
            lines.append("  filter?: Record<string, unknown>;")
            lines.append("}")
            lines.append("")

        return "\n".join(lines)
