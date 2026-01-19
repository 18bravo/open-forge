"""
Cypher statement generator for Apache AGE graph database.
Generates Cypher queries for creating graph nodes, edges, and constraints.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

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


class CypherGenerator:
    """Generates Apache AGE Cypher statements from ontology schemas."""

    def __init__(
        self,
        graph_name: str = "ontology_graph",
        include_comments: bool = True,
        generate_constraints: bool = True
    ):
        """
        Initialize the Cypher generator.

        Args:
            graph_name: Name of the Apache AGE graph.
            include_comments: Whether to include comments in output.
            generate_constraints: Whether to generate constraint statements.
        """
        self.graph_name = graph_name
        self.include_comments = include_comments
        self.generate_constraints = generate_constraints

    def generate(self, ontology_schema: OntologySchema) -> str:
        """
        Generate complete Cypher statements from an ontology schema.

        Args:
            ontology_schema: The ontology schema to generate Cypher for.

        Returns:
            Complete Cypher statements string.
        """
        statements: List[str] = []

        # Header comment
        if self.include_comments:
            statements.append(self._generate_header(ontology_schema))

        # Graph setup (for Apache AGE via SQL)
        statements.append(self._generate_graph_setup())
        statements.append("")

        # Generate node label setup comments/documentation
        if self.include_comments:
            statements.append("-- Node labels (types):")
            for ontology_type in ontology_schema.types:
                if not ontology_type.abstract:
                    statements.append(f"--   :{ontology_type.name}")
            statements.append("")

        # Generate relationship type documentation
        if self.include_comments and ontology_schema.relationships:
            statements.append("-- Relationship types:")
            for rel in ontology_schema.relationships:
                statements.append(f"--   :{rel.source_type} -[:{self._to_edge_type(rel.name)}]-> :{rel.target_type}")
            statements.append("")

        # Generate Cypher functions for creating nodes
        statements.append(self._generate_node_creation_functions(ontology_schema))
        statements.append("")

        # Generate Cypher functions for creating edges
        statements.append(self._generate_edge_creation_functions(ontology_schema))
        statements.append("")

        # Generate constraint statements if enabled
        if self.generate_constraints:
            constraints = self._generate_constraints(ontology_schema)
            if constraints:
                statements.append(constraints)

        return "\n".join(statements)

    def _generate_header(self, ontology_schema: OntologySchema) -> str:
        """Generate header comment."""
        return f"""-- ============================================================================
-- Apache AGE Cypher Statements for: {ontology_schema.name}
-- Version: {ontology_schema.version}
-- Generated at: {datetime.now().isoformat()}
-- Description: {ontology_schema.description or 'N/A'}
-- ============================================================================
"""

    def _generate_graph_setup(self) -> str:
        """Generate graph setup SQL for Apache AGE."""
        return f"""-- Graph Setup (run these SQL statements first)
-- LOAD 'age';
-- SET search_path = ag_catalog, "$user", public;
-- SELECT create_graph('{self.graph_name}');
"""

    def _generate_node_creation_functions(self, ontology_schema: OntologySchema) -> str:
        """Generate Cypher statements for creating nodes of each type."""
        statements: List[str] = []

        if self.include_comments:
            statements.append("-- ============================================================================")
            statements.append("-- Node Creation Cypher Templates")
            statements.append("-- ============================================================================")
            statements.append("")

        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            statements.append(self._generate_node_create_template(ontology_type))
            statements.append("")
            statements.append(self._generate_node_merge_template(ontology_type))
            statements.append("")
            statements.append(self._generate_node_find_template(ontology_type))
            statements.append("")

        return "\n".join(statements)

    def _generate_node_create_template(self, ontology_type: OntologyType) -> str:
        """Generate CREATE node template for a type."""
        label = ontology_type.name
        props = self._get_property_placeholders(ontology_type.properties)

        if self.include_comments:
            comment = f"-- Create {ontology_type.name} node\n"
            if ontology_type.description:
                comment += f"-- {ontology_type.description}\n"
        else:
            comment = ""

        cypher = f"""SELECT * FROM cypher('{self.graph_name}', $$
    CREATE (n:{label} {{{props}}})
    RETURN n
$$) as (node agtype);"""

        return comment + cypher

    def _generate_node_merge_template(self, ontology_type: OntologyType) -> str:
        """Generate MERGE node template for a type."""
        label = ontology_type.name
        key_prop = ontology_type.primary_key or "id"

        if self.include_comments:
            comment = f"-- Upsert {ontology_type.name} node (merge on {key_prop})\n"
        else:
            comment = ""

        props = self._get_property_placeholders(ontology_type.properties)

        cypher = f"""SELECT * FROM cypher('{self.graph_name}', $$
    MERGE (n:{label} {{{key_prop}: ${key_prop}}})
    SET n = {{{props}}}
    RETURN n
$$) as (node agtype);"""

        return comment + cypher

    def _generate_node_find_template(self, ontology_type: OntologyType) -> str:
        """Generate MATCH node template for a type."""
        label = ontology_type.name
        key_prop = ontology_type.primary_key or "id"

        if self.include_comments:
            comment = f"-- Find {ontology_type.name} by {key_prop}\n"
        else:
            comment = ""

        cypher = f"""SELECT * FROM cypher('{self.graph_name}', $$
    MATCH (n:{label} {{{key_prop}: ${key_prop}}})
    RETURN n
$$) as (node agtype);"""

        return comment + cypher

    def _generate_edge_creation_functions(self, ontology_schema: OntologySchema) -> str:
        """Generate Cypher statements for creating edges."""
        statements: List[str] = []

        if not ontology_schema.relationships:
            return ""

        if self.include_comments:
            statements.append("-- ============================================================================")
            statements.append("-- Edge Creation Cypher Templates")
            statements.append("-- ============================================================================")
            statements.append("")

        for rel in ontology_schema.relationships:
            statements.append(self._generate_edge_create_template(rel, ontology_schema))
            statements.append("")

            if rel.cardinality in [Cardinality.ONE_TO_MANY, Cardinality.MANY_TO_MANY]:
                statements.append(self._generate_edge_find_template(rel, ontology_schema))
                statements.append("")

        return "\n".join(statements)

    def _generate_edge_create_template(
        self,
        rel: Relationship,
        ontology_schema: OntologySchema
    ) -> str:
        """Generate CREATE edge template for a relationship."""
        source_type = ontology_schema.get_type(rel.source_type)
        target_type = ontology_schema.get_type(rel.target_type)

        if not source_type or not target_type:
            return ""

        source_key = source_type.primary_key or "id"
        target_key = target_type.primary_key or "id"
        edge_type = self._to_edge_type(rel.name)

        if self.include_comments:
            comment = f"-- Create {rel.name} relationship ({rel.source_type} -> {rel.target_type})\n"
            if rel.description:
                comment += f"-- {rel.description}\n"
        else:
            comment = ""

        # Include relationship properties if any
        if rel.properties:
            edge_props = " " + self._get_property_placeholders(rel.properties)
        else:
            edge_props = ""

        cypher = f"""SELECT * FROM cypher('{self.graph_name}', $$
    MATCH (a:{rel.source_type} {{{source_key}: $source_{source_key}}}),
          (b:{rel.target_type} {{{target_key}: $target_{target_key}}})
    CREATE (a)-[r:{edge_type}{{{edge_props}}}]->(b)
    RETURN r
$$) as (rel agtype);"""

        return comment + cypher

    def _generate_edge_find_template(
        self,
        rel: Relationship,
        ontology_schema: OntologySchema
    ) -> str:
        """Generate MATCH template to find edges and connected nodes."""
        source_type = ontology_schema.get_type(rel.source_type)

        if not source_type:
            return ""

        source_key = source_type.primary_key or "id"
        edge_type = self._to_edge_type(rel.name)

        if self.include_comments:
            comment = f"-- Find {rel.target_type} connected to {rel.source_type} via {rel.name}\n"
        else:
            comment = ""

        cypher = f"""SELECT * FROM cypher('{self.graph_name}', $$
    MATCH (a:{rel.source_type} {{{source_key}: $source_{source_key}}})-[r:{edge_type}]->(b:{rel.target_type})
    RETURN b, r
$$) as (target agtype, rel agtype);"""

        return comment + cypher

    def _generate_constraints(self, ontology_schema: OntologySchema) -> str:
        """Generate constraint statements (as SQL comments since AGE has limited constraint support)."""
        statements: List[str] = []

        if self.include_comments:
            statements.append("-- ============================================================================")
            statements.append("-- Constraints (for validation/documentation)")
            statements.append("-- Note: Apache AGE has limited native constraint support")
            statements.append("-- These constraints should be enforced at the application layer")
            statements.append("-- ============================================================================")
            statements.append("")

        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            type_constraints = self._get_type_constraints(ontology_type)
            if type_constraints:
                statements.append(f"-- Constraints for {ontology_type.name}:")
                statements.extend([f"--   {c}" for c in type_constraints])
                statements.append("")

        return "\n".join(statements)

    def _get_type_constraints(self, ontology_type: OntologyType) -> List[str]:
        """Get constraint descriptions for a type."""
        constraints: List[str] = []

        # Primary key uniqueness
        if ontology_type.primary_key:
            constraints.append(f"{ontology_type.primary_key} must be unique")

        # Property constraints
        for prop in ontology_type.properties:
            if prop.required:
                constraints.append(f"{prop.name} is required")

            for c in prop.constraints:
                if c.constraint_type == ConstraintType.UNIQUE:
                    constraints.append(f"{prop.name} must be unique")
                elif c.constraint_type == ConstraintType.MIN_VALUE and c.value is not None:
                    constraints.append(f"{prop.name} >= {c.value}")
                elif c.constraint_type == ConstraintType.MAX_VALUE and c.value is not None:
                    constraints.append(f"{prop.name} <= {c.value}")
                elif c.constraint_type == ConstraintType.PATTERN and c.value is not None:
                    constraints.append(f"{prop.name} must match pattern: {c.value}")

        return constraints

    def _get_property_placeholders(self, properties: List[Property]) -> str:
        """Generate property placeholder string for Cypher."""
        if not properties:
            return ""

        placeholders = [f"{p.name}: ${p.name}" for p in properties]
        return ", ".join(placeholders)

    def _to_edge_type(self, name: str) -> str:
        """Convert relationship name to edge type (uppercase with underscores)."""
        import re
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return s2.upper()

    def generate_node_create(
        self,
        ontology_type: OntologyType,
        properties: Dict[str, Any]
    ) -> str:
        """
        Generate a CREATE statement for a specific node with values.

        Args:
            ontology_type: The type of node to create.
            properties: Property values.

        Returns:
            Executable Cypher statement.
        """
        label = ontology_type.name
        props_str = self._format_properties(properties)

        return f"""SELECT * FROM cypher('{self.graph_name}', $$
    CREATE (n:{label} {props_str})
    RETURN n
$$) as (node agtype);"""

    def generate_node_merge(
        self,
        ontology_type: OntologyType,
        key_value: Any,
        properties: Dict[str, Any]
    ) -> str:
        """
        Generate a MERGE statement for a specific node with values.

        Args:
            ontology_type: The type of node to merge.
            key_value: Value of the primary key.
            properties: Property values.

        Returns:
            Executable Cypher statement.
        """
        label = ontology_type.name
        key_prop = ontology_type.primary_key or "id"
        key_str = self._format_value(key_value)
        props_str = self._format_properties(properties)

        return f"""SELECT * FROM cypher('{self.graph_name}', $$
    MERGE (n:{label} {{{key_prop}: {key_str}}})
    SET n = {props_str}
    RETURN n
$$) as (node agtype);"""

    def generate_edge_create(
        self,
        rel: Relationship,
        source_key_value: Any,
        target_key_value: Any,
        source_key_name: str = "id",
        target_key_name: str = "id",
        edge_properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a CREATE statement for an edge with values.

        Args:
            rel: The relationship to create.
            source_key_value: Value of the source node's key.
            target_key_value: Value of the target node's key.
            source_key_name: Name of the source node's key property.
            target_key_name: Name of the target node's key property.
            edge_properties: Optional properties for the edge.

        Returns:
            Executable Cypher statement.
        """
        edge_type = self._to_edge_type(rel.name)
        source_key_str = self._format_value(source_key_value)
        target_key_str = self._format_value(target_key_value)

        if edge_properties:
            edge_props = " " + self._format_properties(edge_properties)
        else:
            edge_props = ""

        return f"""SELECT * FROM cypher('{self.graph_name}', $$
    MATCH (a:{rel.source_type} {{{source_key_name}: {source_key_str}}}),
          (b:{rel.target_type} {{{target_key_name}: {target_key_str}}})
    CREATE (a)-[r:{edge_type}{edge_props}]->(b)
    RETURN r
$$) as (rel agtype);"""

    def generate_node_delete(
        self,
        ontology_type: OntologyType,
        key_value: Any
    ) -> str:
        """
        Generate a DELETE statement for a node.

        Args:
            ontology_type: The type of node to delete.
            key_value: Value of the primary key.

        Returns:
            Executable Cypher statement.
        """
        label = ontology_type.name
        key_prop = ontology_type.primary_key or "id"
        key_str = self._format_value(key_value)

        return f"""SELECT * FROM cypher('{self.graph_name}', $$
    MATCH (n:{label} {{{key_prop}: {key_str}}})
    DETACH DELETE n
$$) as (result agtype);"""

    def _format_properties(self, properties: Dict[str, Any]) -> str:
        """Format a properties dictionary as a Cypher property map."""
        if not properties:
            return "{}"

        formatted = []
        for key, value in properties.items():
            formatted.append(f"{key}: {self._format_value(value)}")

        return "{" + ", ".join(formatted) + "}"

    def _format_value(self, value: Any) -> str:
        """Format a value for Cypher."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            # Escape single quotes
            escaped = value.replace("'", "\\'")
            return f"'{escaped}'"
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return f"'{str(value)}'"

    def generate_traversal(
        self,
        start_type: str,
        start_key: str,
        start_value: Any,
        path_pattern: str,
        return_vars: List[str]
    ) -> str:
        """
        Generate a graph traversal query.

        Args:
            start_type: Starting node type.
            start_key: Key property name.
            start_value: Key property value.
            path_pattern: Cypher path pattern (e.g., "-[:OWNS]->(:Product)")
            return_vars: Variables to return.

        Returns:
            Executable Cypher statement.
        """
        start_val_str = self._format_value(start_value)
        return_str = ", ".join(return_vars)

        return f"""SELECT * FROM cypher('{self.graph_name}', $$
    MATCH (start:{start_type} {{{start_key}: {start_val_str}}}){path_pattern}
    RETURN {return_str}
$$) as ({', '.join(f'{v} agtype' for v in return_vars)});"""
