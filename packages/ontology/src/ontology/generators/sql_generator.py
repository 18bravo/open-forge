"""
SQL DDL generator for PostgreSQL from LinkML schemas.
Generates CREATE TABLE statements, indexes, and foreign key constraints.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

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


# Mapping from PropertyType to PostgreSQL types
PROPERTY_TYPE_TO_SQL: Dict[PropertyType, str] = {
    PropertyType.STRING: "TEXT",
    PropertyType.INTEGER: "BIGINT",
    PropertyType.FLOAT: "DOUBLE PRECISION",
    PropertyType.BOOLEAN: "BOOLEAN",
    PropertyType.DATETIME: "TIMESTAMP WITH TIME ZONE",
    PropertyType.DATE: "DATE",
    PropertyType.TIME: "TIME",
    PropertyType.UUID: "UUID",
    PropertyType.JSON: "JSONB",
    PropertyType.ARRAY: "JSONB",  # Arrays stored as JSONB
    PropertyType.ENUM: "TEXT",  # Enums with CHECK constraint
}


class SQLGenerator:
    """Generates PostgreSQL DDL from ontology schemas."""

    def __init__(
        self,
        schema_prefix: str = "ontology",
        include_comments: bool = True,
        include_timestamps: bool = True,
        include_audit_columns: bool = True
    ):
        """
        Initialize the SQL generator.

        Args:
            schema_prefix: PostgreSQL schema name to use.
            include_comments: Whether to include SQL comments.
            include_timestamps: Whether to add created_at/updated_at columns.
            include_audit_columns: Whether to add created_by/updated_by columns.
        """
        self.schema_prefix = schema_prefix
        self.include_comments = include_comments
        self.include_timestamps = include_timestamps
        self.include_audit_columns = include_audit_columns

    def generate(self, ontology_schema: OntologySchema) -> str:
        """
        Generate complete PostgreSQL DDL from an ontology schema.

        Args:
            ontology_schema: The ontology schema to generate SQL for.

        Returns:
            Complete SQL DDL string.
        """
        statements: List[str] = []

        # Header comment
        if self.include_comments:
            statements.append(self._generate_header(ontology_schema))

        # Create schema
        statements.append(f"CREATE SCHEMA IF NOT EXISTS {self.schema_prefix};")
        statements.append("")

        # Generate enum types
        enum_ddl = self._generate_enum_types(ontology_schema)
        if enum_ddl:
            statements.append(enum_ddl)
            statements.append("")

        # Generate tables for non-abstract types
        for ontology_type in ontology_schema.types:
            if not ontology_type.abstract:
                statements.append(self._generate_table(ontology_type, ontology_schema))
                statements.append("")

        # Generate junction tables for many-to-many relationships
        for rel in ontology_schema.relationships:
            if rel.cardinality == Cardinality.MANY_TO_MANY:
                statements.append(self._generate_junction_table(rel, ontology_schema))
                statements.append("")

        # Generate foreign key constraints
        fk_statements = self._generate_foreign_keys(ontology_schema)
        if fk_statements:
            statements.append(fk_statements)
            statements.append("")

        # Generate indexes
        index_statements = self._generate_indexes(ontology_schema)
        if index_statements:
            statements.append(index_statements)

        return "\n".join(statements)

    def _generate_header(self, ontology_schema: OntologySchema) -> str:
        """Generate header comment."""
        return f"""-- ============================================================================
-- Generated SQL DDL for: {ontology_schema.name}
-- Version: {ontology_schema.version}
-- Generated at: {datetime.now().isoformat()}
-- Description: {ontology_schema.description or 'N/A'}
-- ============================================================================
"""

    def _generate_enum_types(self, ontology_schema: OntologySchema) -> str:
        """Generate CREATE TYPE statements for enum properties."""
        enum_types: Dict[str, List[str]] = {}

        for ontology_type in ontology_schema.types:
            for prop in ontology_type.properties:
                if prop.property_type == PropertyType.ENUM and prop.enum_values:
                    enum_name = f"{ontology_type.name}_{prop.name}_enum"
                    enum_types[enum_name] = prop.enum_values

        if not enum_types:
            return ""

        statements: List[str] = []
        if self.include_comments:
            statements.append("-- Enum types")

        for enum_name, values in enum_types.items():
            values_str = ", ".join(f"'{v}'" for v in values)
            statements.append(
                f"CREATE TYPE {self.schema_prefix}.{enum_name} AS ENUM ({values_str});"
            )

        return "\n".join(statements)

    def _generate_table(
        self,
        ontology_type: OntologyType,
        ontology_schema: OntologySchema
    ) -> str:
        """Generate CREATE TABLE statement for an ontology type."""
        table_name = self._to_snake_case(ontology_type.name)
        full_table_name = f"{self.schema_prefix}.{table_name}"

        columns: List[str] = []

        # Generate columns for properties
        for prop in ontology_type.properties:
            column_def = self._generate_column(prop, ontology_type)
            columns.append(column_def)

        # Add timestamp columns
        if self.include_timestamps:
            columns.append("    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL")
            columns.append("    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL")

        # Add audit columns
        if self.include_audit_columns:
            columns.append("    created_by TEXT")
            columns.append("    updated_by TEXT")

        # Add foreign key columns for relationships
        for rel in ontology_schema.relationships:
            if rel.source_type == ontology_type.name:
                if rel.cardinality in [Cardinality.MANY_TO_ONE, Cardinality.ONE_TO_ONE]:
                    fk_column = self._generate_fk_column(rel, ontology_schema)
                    if fk_column:
                        columns.append(fk_column)

        # Build CREATE TABLE statement
        columns_str = ",\n".join(columns)

        statement = f"CREATE TABLE {full_table_name} (\n{columns_str}\n);"

        # Add table comment
        if self.include_comments and ontology_type.description:
            statement += f"\n\nCOMMENT ON TABLE {full_table_name} IS '{self._escape_sql(ontology_type.description)}';"

        return statement

    def _generate_column(self, prop: Property, ontology_type: OntologyType) -> str:
        """Generate a column definition for a property."""
        column_name = self._to_snake_case(prop.name)
        sql_type = self._get_sql_type(prop, ontology_type)

        parts = [f"    {column_name}", sql_type]

        # Add constraints
        constraint_parts = self._generate_column_constraints(prop, ontology_type)
        if constraint_parts:
            parts.append(constraint_parts)

        return " ".join(parts)

    def _get_sql_type(self, prop: Property, ontology_type: OntologyType) -> str:
        """Get the PostgreSQL type for a property."""
        if prop.property_type == PropertyType.ENUM:
            enum_name = f"{ontology_type.name}_{prop.name}_enum"
            return f"{self.schema_prefix}.{enum_name}"
        return PROPERTY_TYPE_TO_SQL.get(prop.property_type, "TEXT")

    def _generate_column_constraints(
        self,
        prop: Property,
        ontology_type: OntologyType
    ) -> str:
        """Generate column constraints."""
        constraints: List[str] = []

        # Primary key
        if prop.name == ontology_type.primary_key:
            constraints.append("PRIMARY KEY")

        # NOT NULL
        if prop.required:
            constraints.append("NOT NULL")

        # UNIQUE
        for c in prop.constraints:
            if c.constraint_type == ConstraintType.UNIQUE:
                constraints.append("UNIQUE")

        # DEFAULT
        if prop.default_value is not None:
            default_val = self._format_default_value(prop.default_value, prop.property_type)
            constraints.append(f"DEFAULT {default_val}")

        # CHECK constraints
        check_constraints = self._generate_check_constraints(prop)
        if check_constraints:
            constraints.append(check_constraints)

        return " ".join(constraints)

    def _generate_check_constraints(self, prop: Property) -> str:
        """Generate CHECK constraints for a property."""
        checks: List[str] = []
        column_name = self._to_snake_case(prop.name)

        for c in prop.constraints:
            if c.constraint_type == ConstraintType.MIN_VALUE and c.value is not None:
                checks.append(f"{column_name} >= {c.value}")
            elif c.constraint_type == ConstraintType.MAX_VALUE and c.value is not None:
                checks.append(f"{column_name} <= {c.value}")
            elif c.constraint_type == ConstraintType.MIN_LENGTH and c.value is not None:
                checks.append(f"LENGTH({column_name}) >= {c.value}")
            elif c.constraint_type == ConstraintType.MAX_LENGTH and c.value is not None:
                checks.append(f"LENGTH({column_name}) <= {c.value}")
            elif c.constraint_type == ConstraintType.PATTERN and c.value is not None:
                # PostgreSQL regex syntax
                checks.append(f"{column_name} ~ '{self._escape_sql(c.value)}'")

        if checks:
            return f"CHECK ({' AND '.join(checks)})"
        return ""

    def _generate_fk_column(
        self,
        rel: Relationship,
        ontology_schema: OntologySchema
    ) -> Optional[str]:
        """Generate foreign key column for a relationship."""
        target_type = ontology_schema.get_type(rel.target_type)
        if not target_type or not target_type.primary_key:
            return None

        # Get the primary key property to determine its type
        pk_prop = None
        for p in target_type.properties:
            if p.name == target_type.primary_key:
                pk_prop = p
                break

        if not pk_prop:
            return None

        fk_column = f"{self._to_snake_case(rel.name)}_id"
        sql_type = PROPERTY_TYPE_TO_SQL.get(pk_prop.property_type, "TEXT")

        constraint = ""
        if rel.required:
            constraint = " NOT NULL"

        return f"    {fk_column} {sql_type}{constraint}"

    def _generate_junction_table(
        self,
        rel: Relationship,
        ontology_schema: OntologySchema
    ) -> str:
        """Generate junction table for many-to-many relationship."""
        source_type = ontology_schema.get_type(rel.source_type)
        target_type = ontology_schema.get_type(rel.target_type)

        if not source_type or not target_type:
            return ""

        table_name = f"{self._to_snake_case(rel.source_type)}_{self._to_snake_case(rel.name)}"
        full_table_name = f"{self.schema_prefix}.{table_name}"

        source_fk = f"{self._to_snake_case(rel.source_type)}_id"
        target_fk = f"{self._to_snake_case(rel.target_type)}_id"

        columns: List[str] = [
            f"    {source_fk} TEXT NOT NULL",
            f"    {target_fk} TEXT NOT NULL",
        ]

        # Add relationship properties if any
        for prop in rel.properties:
            column_def = self._generate_column(prop, OntologyType(
                name=table_name,
                properties=[prop]
            ))
            columns.append(column_def)

        # Add timestamps
        if self.include_timestamps:
            columns.append("    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL")

        # Add primary key
        columns.append(f"    PRIMARY KEY ({source_fk}, {target_fk})")

        columns_str = ",\n".join(columns)

        return f"CREATE TABLE {full_table_name} (\n{columns_str}\n);"

    def _generate_foreign_keys(self, ontology_schema: OntologySchema) -> str:
        """Generate ALTER TABLE statements for foreign key constraints."""
        statements: List[str] = []

        if self.include_comments:
            statements.append("-- Foreign key constraints")

        for rel in ontology_schema.relationships:
            if rel.cardinality in [Cardinality.MANY_TO_ONE, Cardinality.ONE_TO_ONE]:
                source_table = f"{self.schema_prefix}.{self._to_snake_case(rel.source_type)}"
                target_table = f"{self.schema_prefix}.{self._to_snake_case(rel.target_type)}"
                fk_column = f"{self._to_snake_case(rel.name)}_id"

                target_type = ontology_schema.get_type(rel.target_type)
                if target_type and target_type.primary_key:
                    pk_column = self._to_snake_case(target_type.primary_key)
                    constraint_name = f"fk_{self._to_snake_case(rel.source_type)}_{self._to_snake_case(rel.name)}"

                    statements.append(
                        f"ALTER TABLE {source_table} "
                        f"ADD CONSTRAINT {constraint_name} "
                        f"FOREIGN KEY ({fk_column}) REFERENCES {target_table}({pk_column});"
                    )

            elif rel.cardinality == Cardinality.MANY_TO_MANY:
                junction_table = f"{self.schema_prefix}.{self._to_snake_case(rel.source_type)}_{self._to_snake_case(rel.name)}"
                source_table = f"{self.schema_prefix}.{self._to_snake_case(rel.source_type)}"
                target_table = f"{self.schema_prefix}.{self._to_snake_case(rel.target_type)}"

                source_type = ontology_schema.get_type(rel.source_type)
                target_type = ontology_schema.get_type(rel.target_type)

                if source_type and source_type.primary_key:
                    statements.append(
                        f"ALTER TABLE {junction_table} "
                        f"ADD CONSTRAINT fk_{self._to_snake_case(rel.source_type)} "
                        f"FOREIGN KEY ({self._to_snake_case(rel.source_type)}_id) "
                        f"REFERENCES {source_table}({self._to_snake_case(source_type.primary_key)});"
                    )

                if target_type and target_type.primary_key:
                    statements.append(
                        f"ALTER TABLE {junction_table} "
                        f"ADD CONSTRAINT fk_{self._to_snake_case(rel.target_type)} "
                        f"FOREIGN KEY ({self._to_snake_case(rel.target_type)}_id) "
                        f"REFERENCES {target_table}({self._to_snake_case(target_type.primary_key)});"
                    )

        return "\n".join(statements)

    def _generate_indexes(self, ontology_schema: OntologySchema) -> str:
        """Generate CREATE INDEX statements."""
        statements: List[str] = []

        if self.include_comments:
            statements.append("-- Indexes")

        for ontology_type in ontology_schema.types:
            if ontology_type.abstract:
                continue

            table_name = f"{self.schema_prefix}.{self._to_snake_case(ontology_type.name)}"

            # Create indexes for foreign key columns
            for rel in ontology_schema.relationships:
                if rel.source_type == ontology_type.name:
                    if rel.cardinality in [Cardinality.MANY_TO_ONE, Cardinality.ONE_TO_ONE]:
                        fk_column = f"{self._to_snake_case(rel.name)}_id"
                        index_name = f"idx_{self._to_snake_case(ontology_type.name)}_{fk_column}"
                        statements.append(
                            f"CREATE INDEX {index_name} ON {table_name}({fk_column});"
                        )

            # Create indexes for properties with constraints that suggest indexing
            for prop in ontology_type.properties:
                for c in prop.constraints:
                    if c.constraint_type == ConstraintType.UNIQUE:
                        column_name = self._to_snake_case(prop.name)
                        index_name = f"idx_{self._to_snake_case(ontology_type.name)}_{column_name}_unique"
                        statements.append(
                            f"CREATE UNIQUE INDEX {index_name} ON {table_name}({column_name});"
                        )
                        break

        # Create indexes on timestamp columns for efficient querying
        if self.include_timestamps:
            for ontology_type in ontology_schema.types:
                if ontology_type.abstract:
                    continue
                table_name = f"{self.schema_prefix}.{self._to_snake_case(ontology_type.name)}"
                statements.append(
                    f"CREATE INDEX idx_{self._to_snake_case(ontology_type.name)}_created_at "
                    f"ON {table_name}(created_at);"
                )

        return "\n".join(statements)

    def _format_default_value(self, value: Any, property_type: PropertyType) -> str:
        """Format a default value for SQL."""
        if value is None:
            return "NULL"
        if property_type == PropertyType.STRING:
            return f"'{self._escape_sql(str(value))}'"
        if property_type == PropertyType.BOOLEAN:
            return "TRUE" if value else "FALSE"
        if property_type in [PropertyType.INTEGER, PropertyType.FLOAT]:
            return str(value)
        if property_type == PropertyType.JSON:
            return f"'{self._escape_sql(str(value))}'::jsonb"
        return f"'{self._escape_sql(str(value))}'"

    def _to_snake_case(self, name: str) -> str:
        """Convert a name to snake_case."""
        import re
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insert underscore before uppercase letters followed by lowercase
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return s2.lower()

    def _escape_sql(self, value: str) -> str:
        """Escape a string for SQL."""
        return value.replace("'", "''")

    def generate_migration(
        self,
        from_schema: Optional[OntologySchema],
        to_schema: OntologySchema
    ) -> str:
        """
        Generate a migration SQL from one schema version to another.

        Args:
            from_schema: Previous schema version (None for initial migration).
            to_schema: Target schema version.

        Returns:
            Migration SQL string.
        """
        if from_schema is None:
            return self.generate(to_schema)

        statements: List[str] = []

        if self.include_comments:
            statements.append(f"-- Migration from {from_schema.version} to {to_schema.version}")
            statements.append(f"-- Generated at: {datetime.now().isoformat()}")
            statements.append("")

        from_types = {t.name: t for t in from_schema.types}
        to_types = {t.name: t for t in to_schema.types}

        # New types
        new_types = set(to_types.keys()) - set(from_types.keys())
        for type_name in new_types:
            statements.append(f"-- Adding new type: {type_name}")
            statements.append(self._generate_table(to_types[type_name], to_schema))
            statements.append("")

        # Removed types
        removed_types = set(from_types.keys()) - set(to_types.keys())
        for type_name in removed_types:
            table_name = f"{self.schema_prefix}.{self._to_snake_case(type_name)}"
            statements.append(f"-- Removing type: {type_name}")
            statements.append(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
            statements.append("")

        # Modified types
        common_types = set(from_types.keys()) & set(to_types.keys())
        for type_name in common_types:
            from_type = from_types[type_name]
            to_type = to_types[type_name]

            alter_statements = self._generate_type_alterations(from_type, to_type)
            if alter_statements:
                statements.append(f"-- Modifying type: {type_name}")
                statements.extend(alter_statements)
                statements.append("")

        return "\n".join(statements)

    def _generate_type_alterations(
        self,
        from_type: OntologyType,
        to_type: OntologyType
    ) -> List[str]:
        """Generate ALTER TABLE statements for type modifications."""
        statements: List[str] = []
        table_name = f"{self.schema_prefix}.{self._to_snake_case(to_type.name)}"

        from_props = {p.name: p for p in from_type.properties}
        to_props = {p.name: p for p in to_type.properties}

        # New properties
        for prop_name in set(to_props.keys()) - set(from_props.keys()):
            prop = to_props[prop_name]
            column_name = self._to_snake_case(prop_name)
            sql_type = PROPERTY_TYPE_TO_SQL.get(prop.property_type, "TEXT")
            statements.append(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type};")

        # Removed properties
        for prop_name in set(from_props.keys()) - set(to_props.keys()):
            column_name = self._to_snake_case(prop_name)
            statements.append(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {column_name};")

        return statements
