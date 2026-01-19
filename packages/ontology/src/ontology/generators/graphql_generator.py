"""
GraphQL schema generator from LinkML schemas.
Generates GraphQL SDL (Schema Definition Language) with types, queries, and mutations.
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


# Mapping from PropertyType to GraphQL scalar types
PROPERTY_TYPE_TO_GRAPHQL: Dict[PropertyType, str] = {
    PropertyType.STRING: "String",
    PropertyType.INTEGER: "Int",
    PropertyType.FLOAT: "Float",
    PropertyType.BOOLEAN: "Boolean",
    PropertyType.DATETIME: "DateTime",
    PropertyType.DATE: "Date",
    PropertyType.TIME: "Time",
    PropertyType.UUID: "ID",
    PropertyType.JSON: "JSON",
    PropertyType.ARRAY: "Array",  # Will be handled specially
    PropertyType.ENUM: "String",  # Will be replaced with actual enum
}


class GraphQLGenerator:
    """Generates GraphQL schema from ontology schemas."""

    def __init__(
        self,
        include_descriptions: bool = True,
        include_queries: bool = True,
        include_mutations: bool = True,
        include_subscriptions: bool = False,
        include_connections: bool = True,  # Relay-style connections
        include_filters: bool = True,
        custom_scalars: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the GraphQL generator.

        Args:
            include_descriptions: Whether to include descriptions.
            include_queries: Whether to generate query type.
            include_mutations: Whether to generate mutation type.
            include_subscriptions: Whether to generate subscription type.
            include_connections: Whether to generate Relay-style connections.
            include_filters: Whether to generate filter input types.
            custom_scalars: Custom scalar type definitions.
        """
        self.include_descriptions = include_descriptions
        self.include_queries = include_queries
        self.include_mutations = include_mutations
        self.include_subscriptions = include_subscriptions
        self.include_connections = include_connections
        self.include_filters = include_filters
        self.custom_scalars = custom_scalars or {}

    def generate(self, ontology_schema: OntologySchema) -> str:
        """
        Generate GraphQL schema from an ontology schema.

        Args:
            ontology_schema: The ontology schema to generate GraphQL for.

        Returns:
            Complete GraphQL SDL string.
        """
        sections: List[str] = []

        # Header
        sections.append(self._generate_header(ontology_schema))

        # Custom scalars
        sections.append(self._generate_scalars())

        # Enums
        enums = self._generate_enums(ontology_schema)
        if enums:
            sections.append(enums)

        # Interfaces for abstract types
        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                sections.append(self._generate_interface(ontology_type, ontology_schema))

        # Types
        for ontology_type in ontology_schema.types:
            if not ontology_type.abstract:
                sections.append(self._generate_type(ontology_type, ontology_schema))

        # Input types for mutations
        if self.include_mutations:
            sections.append(self._generate_input_types(ontology_schema))

        # Filter input types
        if self.include_filters:
            sections.append(self._generate_filter_types(ontology_schema))

        # Connection types for pagination
        if self.include_connections:
            sections.append(self._generate_connection_types(ontology_schema))

        # Query type
        if self.include_queries:
            sections.append(self._generate_query_type(ontology_schema))

        # Mutation type
        if self.include_mutations:
            sections.append(self._generate_mutation_type(ontology_schema))

        # Subscription type
        if self.include_subscriptions:
            sections.append(self._generate_subscription_type(ontology_schema))

        return "\n\n".join(filter(None, sections))

    def _generate_header(self, ontology_schema: OntologySchema) -> str:
        """Generate schema header comment."""
        return f'''"""
GraphQL Schema for: {ontology_schema.name}
Version: {ontology_schema.version}
Generated at: {datetime.now().isoformat()}
{f"Description: {ontology_schema.description}" if ontology_schema.description else ""}

This schema is auto-generated. Do not edit directly.
"""'''

    def _generate_scalars(self) -> str:
        """Generate custom scalar definitions."""
        scalars = [
            '"""ISO 8601 datetime string"""',
            "scalar DateTime",
            "",
            '"""ISO 8601 date string"""',
            "scalar Date",
            "",
            '"""ISO 8601 time string"""',
            "scalar Time",
            "",
            '"""Arbitrary JSON value"""',
            "scalar JSON",
        ]

        # Add any custom scalars
        for name, description in self.custom_scalars.items():
            scalars.append("")
            scalars.append(f'"""{description}"""')
            scalars.append(f"scalar {name}")

        return "\n".join(scalars)

    def _generate_enums(self, ontology_schema: OntologySchema) -> str:
        """Generate GraphQL enum definitions."""
        enums: List[str] = []

        for ontology_type in ontology_schema.types:
            for prop in ontology_type.properties:
                if prop.property_type == PropertyType.ENUM and prop.enum_values:
                    enum_name = self._to_pascal_case(f"{ontology_type.name}_{prop.name}")
                    enum_def = self._generate_enum(enum_name, prop.enum_values, prop.description)
                    enums.append(enum_def)

        return "\n\n".join(enums) if enums else ""

    def _generate_enum(
        self,
        name: str,
        values: List[str],
        description: Optional[str]
    ) -> str:
        """Generate a single enum definition."""
        lines: List[str] = []

        if self.include_descriptions and description:
            lines.append(f'"""{description}"""')

        lines.append(f"enum {name} {{")

        for value in values:
            identifier = self._to_constant_case(value)
            lines.append(f"  {identifier}")

        lines.append("}")

        return "\n".join(lines)

    def _generate_interface(
        self,
        ontology_type: OntologyType,
        ontology_schema: OntologySchema
    ) -> str:
        """Generate a GraphQL interface for an abstract type."""
        lines: List[str] = []

        if self.include_descriptions and ontology_type.description:
            lines.append(f'"""{ontology_type.description}"""')

        lines.append(f"interface {ontology_type.name} {{")

        # Fields
        for prop in ontology_type.properties:
            field = self._generate_field(prop, ontology_type)
            lines.append(f"  {field}")

        lines.append("}")

        return "\n".join(lines)

    def _generate_type(
        self,
        ontology_type: OntologyType,
        ontology_schema: OntologySchema
    ) -> str:
        """Generate a GraphQL type definition."""
        lines: List[str] = []

        if self.include_descriptions and ontology_type.description:
            lines.append(f'"""{ontology_type.description}"""')

        # Type declaration with implements clause
        implements = ""
        if ontology_type.mixins:
            implements = f" implements {' & '.join(ontology_type.mixins)}"

        lines.append(f"type {ontology_type.name}{implements} {{")

        # Fields for properties
        for prop in ontology_type.properties:
            field = self._generate_field(prop, ontology_type)
            lines.append(f"  {field}")

        # Fields for relationships
        for rel in ontology_schema.relationships:
            if rel.source_type == ontology_type.name:
                rel_field = self._generate_relationship_field(rel, ontology_schema)
                lines.append(f"  {rel_field}")

        lines.append("}")

        return "\n".join(lines)

    def _generate_field(self, prop: Property, ontology_type: OntologyType) -> str:
        """Generate a GraphQL field definition."""
        graphql_type = self._get_graphql_type(prop, ontology_type)

        # Handle required fields
        if prop.required:
            graphql_type = f"{graphql_type}!"

        # Description
        description = ""
        if self.include_descriptions and prop.description:
            description = f'"""{prop.description}"""\n  '

        return f"{description}{prop.name}: {graphql_type}"

    def _get_graphql_type(self, prop: Property, ontology_type: OntologyType) -> str:
        """Get the GraphQL type for a property."""
        if prop.property_type == PropertyType.ENUM and prop.enum_values:
            return self._to_pascal_case(f"{ontology_type.name}_{prop.name}")

        if prop.property_type == PropertyType.ARRAY:
            item_type = PROPERTY_TYPE_TO_GRAPHQL.get(
                prop.array_item_type or PropertyType.STRING,
                "String"
            )
            return f"[{item_type}]"

        return PROPERTY_TYPE_TO_GRAPHQL.get(prop.property_type, "String")

    def _generate_relationship_field(
        self,
        rel: Relationship,
        ontology_schema: OntologySchema
    ) -> str:
        """Generate a field for a relationship."""
        if self.include_connections and rel.cardinality in [Cardinality.ONE_TO_MANY, Cardinality.MANY_TO_MANY]:
            # Use connection type for to-many relationships
            graphql_type = f"{rel.target_type}Connection"
            args = "(first: Int, after: String, last: Int, before: String)"
        elif rel.cardinality in [Cardinality.ONE_TO_MANY, Cardinality.MANY_TO_MANY]:
            graphql_type = f"[{rel.target_type}!]"
            args = "(limit: Int, offset: Int)"
        else:
            graphql_type = rel.target_type
            args = ""

        if rel.required and rel.cardinality not in [Cardinality.ONE_TO_MANY, Cardinality.MANY_TO_MANY]:
            graphql_type = f"{graphql_type}!"

        description = ""
        if self.include_descriptions and rel.description:
            description = f'"""{rel.description}"""\n  '

        return f"{description}{rel.name}{args}: {graphql_type}"

    def _generate_input_types(self, ontology_schema: OntologySchema) -> str:
        """Generate input types for mutations."""
        inputs: List[str] = []

        inputs.append("# Input Types for Mutations")

        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            # Create input
            create_input = self._generate_create_input(ontology_type)
            inputs.append(create_input)

            # Update input
            update_input = self._generate_update_input(ontology_type)
            inputs.append(update_input)

        return "\n\n".join(inputs)

    def _generate_create_input(self, ontology_type: OntologyType) -> str:
        """Generate create input type."""
        lines: List[str] = []

        if self.include_descriptions:
            lines.append(f'"""Input for creating a {ontology_type.name}"""')

        lines.append(f"input Create{ontology_type.name}Input {{")

        for prop in ontology_type.properties:
            # Skip auto-generated fields
            if prop.name in ["id", "createdAt", "updatedAt"]:
                continue

            graphql_type = self._get_graphql_type(prop, ontology_type)
            if prop.required:
                graphql_type = f"{graphql_type}!"

            lines.append(f"  {prop.name}: {graphql_type}")

        lines.append("}")

        return "\n".join(lines)

    def _generate_update_input(self, ontology_type: OntologyType) -> str:
        """Generate update input type."""
        lines: List[str] = []

        if self.include_descriptions:
            lines.append(f'"""Input for updating a {ontology_type.name}"""')

        lines.append(f"input Update{ontology_type.name}Input {{")

        for prop in ontology_type.properties:
            # Skip auto-generated fields
            if prop.name in ["createdAt", "updatedAt"]:
                continue

            graphql_type = self._get_graphql_type(prop, ontology_type)

            # ID is required for updates
            if prop.name == "id":
                graphql_type = f"{graphql_type}!"

            lines.append(f"  {prop.name}: {graphql_type}")

        lines.append("}")

        return "\n".join(lines)

    def _generate_filter_types(self, ontology_schema: OntologySchema) -> str:
        """Generate filter input types for queries."""
        filters: List[str] = []

        filters.append("# Filter Input Types")

        # Generic filter operators
        filters.append("""
\"\"\"String filter operators\"\"\"
input StringFilter {
  eq: String
  ne: String
  contains: String
  startsWith: String
  endsWith: String
  in: [String!]
  notIn: [String!]
}

\"\"\"Integer filter operators\"\"\"
input IntFilter {
  eq: Int
  ne: Int
  gt: Int
  gte: Int
  lt: Int
  lte: Int
  in: [Int!]
  notIn: [Int!]
}

\"\"\"Float filter operators\"\"\"
input FloatFilter {
  eq: Float
  ne: Float
  gt: Float
  gte: Float
  lt: Float
  lte: Float
}

\"\"\"Boolean filter operators\"\"\"
input BooleanFilter {
  eq: Boolean
}

\"\"\"DateTime filter operators\"\"\"
input DateTimeFilter {
  eq: DateTime
  ne: DateTime
  gt: DateTime
  gte: DateTime
  lt: DateTime
  lte: DateTime
}
""")

        # Entity-specific filters
        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            filter_type = self._generate_entity_filter(ontology_type)
            filters.append(filter_type)

        return "\n".join(filters)

    def _generate_entity_filter(self, ontology_type: OntologyType) -> str:
        """Generate filter type for an entity."""
        lines: List[str] = []

        if self.include_descriptions:
            lines.append(f'"""Filter for {ontology_type.name} queries"""')

        lines.append(f"input {ontology_type.name}Filter {{")

        for prop in ontology_type.properties:
            filter_type = self._get_filter_type(prop.property_type)
            lines.append(f"  {prop.name}: {filter_type}")

        # AND/OR combinators
        lines.append(f"  AND: [{ontology_type.name}Filter!]")
        lines.append(f"  OR: [{ontology_type.name}Filter!]")

        lines.append("}")

        return "\n".join(lines)

    def _get_filter_type(self, property_type: PropertyType) -> str:
        """Get the appropriate filter type for a property type."""
        filter_map = {
            PropertyType.STRING: "StringFilter",
            PropertyType.INTEGER: "IntFilter",
            PropertyType.FLOAT: "FloatFilter",
            PropertyType.BOOLEAN: "BooleanFilter",
            PropertyType.DATETIME: "DateTimeFilter",
            PropertyType.DATE: "DateTimeFilter",
            PropertyType.UUID: "StringFilter",
            PropertyType.ENUM: "StringFilter",
        }
        return filter_map.get(property_type, "StringFilter")

    def _generate_connection_types(self, ontology_schema: OntologySchema) -> str:
        """Generate Relay-style connection types."""
        connections: List[str] = []

        connections.append("# Relay Connection Types")

        # PageInfo type
        connections.append("""
\"\"\"Page info for pagination\"\"\"
type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
""")

        # Connection and edge types for each entity
        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            name = ontology_type.name

            connection = f'''
\"\"\"Connection for {name} pagination\"\"\"
type {name}Connection {{
  edges: [{name}Edge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}}

\"\"\"Edge for {name} connection\"\"\"
type {name}Edge {{
  cursor: String!
  node: {name}!
}}
'''
            connections.append(connection)

        return "\n".join(connections)

    def _generate_query_type(self, ontology_schema: OntologySchema) -> str:
        """Generate the Query type."""
        lines: List[str] = []

        lines.append('"""Root Query type"""')
        lines.append("type Query {")

        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            name = ontology_type.name
            snake_name = self._to_camel_case(name)
            plural_name = self._pluralize(snake_name)

            # Single item query
            if self.include_descriptions:
                lines.append(f'  """Get a single {name} by ID"""')
            lines.append(f"  {snake_name}(id: ID!): {name}")

            # List query with connection
            if self.include_connections:
                if self.include_descriptions:
                    lines.append(f'  """List {name} with pagination"""')
                filter_arg = f", filter: {name}Filter" if self.include_filters else ""
                lines.append(f"  {plural_name}(first: Int, after: String, last: Int, before: String{filter_arg}): {name}Connection!")
            else:
                if self.include_descriptions:
                    lines.append(f'  """List {name}"""')
                filter_arg = f", filter: {name}Filter" if self.include_filters else ""
                lines.append(f"  {plural_name}(limit: Int, offset: Int{filter_arg}): [{name}!]!")

        lines.append("}")

        return "\n".join(lines)

    def _generate_mutation_type(self, ontology_schema: OntologySchema) -> str:
        """Generate the Mutation type."""
        lines: List[str] = []

        lines.append('"""Root Mutation type"""')
        lines.append("type Mutation {")

        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            name = ontology_type.name
            snake_name = self._to_camel_case(name)

            # Create mutation
            if self.include_descriptions:
                lines.append(f'  """Create a new {name}"""')
            lines.append(f"  create{name}(input: Create{name}Input!): {name}!")

            # Update mutation
            if self.include_descriptions:
                lines.append(f'  """Update an existing {name}"""')
            lines.append(f"  update{name}(input: Update{name}Input!): {name}!")

            # Delete mutation
            if self.include_descriptions:
                lines.append(f'  """Delete a {name}"""')
            lines.append(f"  delete{name}(id: ID!): Boolean!")

        lines.append("}")

        return "\n".join(lines)

    def _generate_subscription_type(self, ontology_schema: OntologySchema) -> str:
        """Generate the Subscription type."""
        lines: List[str] = []

        lines.append('"""Root Subscription type"""')
        lines.append("type Subscription {")

        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            name = ontology_type.name
            snake_name = self._to_camel_case(name)

            if self.include_descriptions:
                lines.append(f'  """Subscribe to {name} changes"""')
            lines.append(f"  {snake_name}Changed(id: ID): {name}ChangeEvent!")

        lines.append("}")
        lines.append("")

        # Change event type
        lines.append('"""Event type for entity changes"""')
        lines.append("enum ChangeType {")
        lines.append("  CREATED")
        lines.append("  UPDATED")
        lines.append("  DELETED")
        lines.append("}")
        lines.append("")

        # Generate change event types for each entity
        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            name = ontology_type.name
            lines.append(f'"""Change event for {name}"""')
            lines.append(f"type {name}ChangeEvent {{")
            lines.append("  type: ChangeType!")
            lines.append(f"  entity: {name}")
            lines.append("  timestamp: DateTime!")
            lines.append("}")
            lines.append("")

        return "\n".join(lines)

    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase."""
        parts = re.split(r'[_\s-]+', name)
        return "".join(part.capitalize() for part in parts)

    def _to_camel_case(self, name: str) -> str:
        """Convert to camelCase."""
        pascal = self._to_pascal_case(name)
        return pascal[0].lower() + pascal[1:] if pascal else ""

    def _to_constant_case(self, name: str) -> str:
        """Convert to CONSTANT_CASE."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        s3 = re.sub(r'[\s\-]+', '_', s2)
        return s3.upper()

    def _pluralize(self, name: str) -> str:
        """Simple pluralization."""
        if name.endswith("s"):
            return f"{name}es"
        if name.endswith("y"):
            return f"{name[:-1]}ies"
        return f"{name}s"
