"""
LinkML schema compiler that generates multiple output formats.
Orchestrates all generators to produce SQL, Cypher, Pydantic, TypeScript, and GraphQL.
"""
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

from linkml_runtime.linkml_model import SchemaDefinition

from ontology.models import OntologySchema
from ontology.schema import SchemaManager
from ontology.generators.sql_generator import SQLGenerator
from ontology.generators.cypher_generator import CypherGenerator
from ontology.generators.pydantic_generator import PydanticGenerator
from ontology.generators.typescript_generator import TypeScriptGenerator
from ontology.generators.graphql_generator import GraphQLGenerator


class OutputFormat(str, Enum):
    """Supported output formats."""
    SQL = "sql"
    CYPHER = "cypher"
    PYDANTIC = "pydantic"
    TYPESCRIPT = "typescript"
    GRAPHQL = "graphql"
    ALL = "all"


@dataclass
class CompilationResult:
    """Result of a schema compilation."""
    schema_name: str
    schema_version: str
    outputs: Dict[OutputFormat, str]
    compiled_at: datetime
    errors: List[str]
    warnings: List[str]

    def has_errors(self) -> bool:
        """Check if compilation had errors."""
        return len(self.errors) > 0

    def get_output(self, format: OutputFormat) -> Optional[str]:
        """Get output for a specific format."""
        return self.outputs.get(format)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "outputs": {k.value: v for k, v in self.outputs.items()},
            "compiled_at": self.compiled_at.isoformat(),
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class GeneratorConfig:
    """Configuration for individual generators."""
    # SQL generator options
    sql_schema_prefix: str = "ontology"
    sql_include_timestamps: bool = True
    sql_include_audit_columns: bool = True

    # Cypher generator options
    cypher_graph_name: str = "ontology_graph"
    cypher_generate_constraints: bool = True

    # Pydantic generator options
    pydantic_include_validators: bool = True
    pydantic_include_relationships: bool = True
    pydantic_base_class: str = "BaseModel"

    # TypeScript generator options
    typescript_include_jsdoc: bool = True
    typescript_use_strict_null_checks: bool = True
    typescript_generate_zod_schemas: bool = False

    # GraphQL generator options
    graphql_include_queries: bool = True
    graphql_include_mutations: bool = True
    graphql_include_subscriptions: bool = False
    graphql_include_connections: bool = True


class OntologyCompiler:
    """
    Compiles LinkML schemas into multiple target formats.

    This compiler takes a LinkML schema and generates:
    - SQL DDL for PostgreSQL
    - Cypher statements for Apache AGE graph
    - Python Pydantic models
    - TypeScript interfaces
    - GraphQL schema
    """

    def __init__(
        self,
        config: Optional[GeneratorConfig] = None,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize the compiler.

        Args:
            config: Configuration for generators.
            output_dir: Directory for output files.
        """
        self.config = config or GeneratorConfig()
        self.output_dir = Path(output_dir) if output_dir else None
        self.schema_manager = SchemaManager()

        # Initialize generators
        self._init_generators()

    def _init_generators(self) -> None:
        """Initialize all generators with configuration."""
        self.sql_generator = SQLGenerator(
            schema_prefix=self.config.sql_schema_prefix,
            include_timestamps=self.config.sql_include_timestamps,
            include_audit_columns=self.config.sql_include_audit_columns
        )

        self.cypher_generator = CypherGenerator(
            graph_name=self.config.cypher_graph_name,
            generate_constraints=self.config.cypher_generate_constraints
        )

        self.pydantic_generator = PydanticGenerator(
            include_validators=self.config.pydantic_include_validators,
            include_relationships=self.config.pydantic_include_relationships,
            base_class=self.config.pydantic_base_class
        )

        self.typescript_generator = TypeScriptGenerator(
            include_jsdoc=self.config.typescript_include_jsdoc,
            use_strict_null_checks=self.config.typescript_use_strict_null_checks,
            generate_zod_schemas=self.config.typescript_generate_zod_schemas
        )

        self.graphql_generator = GraphQLGenerator(
            include_queries=self.config.graphql_include_queries,
            include_mutations=self.config.graphql_include_mutations,
            include_subscriptions=self.config.graphql_include_subscriptions,
            include_connections=self.config.graphql_include_connections
        )

    def compile(
        self,
        schema: Union[OntologySchema, SchemaDefinition, Path, str],
        formats: Optional[List[OutputFormat]] = None
    ) -> CompilationResult:
        """
        Compile a schema into the specified output formats.

        Args:
            schema: The schema to compile. Can be:
                - OntologySchema object
                - LinkML SchemaDefinition object
                - Path to a YAML file
                - YAML string
            formats: List of output formats to generate. Defaults to all.

        Returns:
            CompilationResult with generated outputs.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Normalize schema to OntologySchema
        try:
            ontology_schema = self._normalize_schema(schema)
        except Exception as e:
            return CompilationResult(
                schema_name="unknown",
                schema_version="unknown",
                outputs={},
                compiled_at=datetime.now(),
                errors=[f"Failed to load schema: {str(e)}"],
                warnings=[]
            )

        # Validate schema
        validation_result = self.schema_manager.validate_schema(ontology_schema)
        if not validation_result.is_valid:
            errors.extend([e.message for e in validation_result.errors])
        warnings.extend([w.message for w in validation_result.warnings])

        # Determine formats to generate
        if formats is None or OutputFormat.ALL in formats:
            formats = [
                OutputFormat.SQL,
                OutputFormat.CYPHER,
                OutputFormat.PYDANTIC,
                OutputFormat.TYPESCRIPT,
                OutputFormat.GRAPHQL,
            ]

        # Generate outputs
        outputs: Dict[OutputFormat, str] = {}

        for format in formats:
            try:
                output = self._generate_format(ontology_schema, format)
                outputs[format] = output
            except Exception as e:
                errors.append(f"Failed to generate {format.value}: {str(e)}")

        result = CompilationResult(
            schema_name=ontology_schema.name,
            schema_version=ontology_schema.version,
            outputs=outputs,
            compiled_at=datetime.now(),
            errors=errors,
            warnings=warnings
        )

        # Write to output directory if configured
        if self.output_dir and not result.has_errors():
            self._write_outputs(result)

        return result

    def _normalize_schema(
        self,
        schema: Union[OntologySchema, SchemaDefinition, Path, str]
    ) -> OntologySchema:
        """Normalize input to OntologySchema."""
        if isinstance(schema, OntologySchema):
            return schema

        if isinstance(schema, SchemaDefinition):
            return self.schema_manager.linkml_to_ontology_schema(schema)

        if isinstance(schema, Path):
            linkml_schema = self.schema_manager.load_linkml_yaml(schema)
            return self.schema_manager.linkml_to_ontology_schema(linkml_schema)

        if isinstance(schema, str):
            # Check if it's a file path or YAML content
            if schema.strip().startswith(("id:", "name:", "classes:")):
                # It's YAML content
                linkml_schema = self.schema_manager.load_linkml_from_string(schema)
            else:
                # Assume it's a file path
                linkml_schema = self.schema_manager.load_linkml_yaml(Path(schema))
            return self.schema_manager.linkml_to_ontology_schema(linkml_schema)

        raise ValueError(f"Unsupported schema type: {type(schema)}")

    def _generate_format(
        self,
        ontology_schema: OntologySchema,
        format: OutputFormat
    ) -> str:
        """Generate a specific output format."""
        if format == OutputFormat.SQL:
            return self.sql_generator.generate(ontology_schema)
        elif format == OutputFormat.CYPHER:
            return self.cypher_generator.generate(ontology_schema)
        elif format == OutputFormat.PYDANTIC:
            return self.pydantic_generator.generate(ontology_schema)
        elif format == OutputFormat.TYPESCRIPT:
            return self.typescript_generator.generate(ontology_schema)
        elif format == OutputFormat.GRAPHQL:
            return self.graphql_generator.generate(ontology_schema)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _write_outputs(self, result: CompilationResult) -> None:
        """Write compilation outputs to files."""
        if not self.output_dir:
            return

        # Create output directory
        schema_dir = self.output_dir / result.schema_name / result.schema_version
        schema_dir.mkdir(parents=True, exist_ok=True)

        # File extensions for each format
        extensions = {
            OutputFormat.SQL: "sql",
            OutputFormat.CYPHER: "cypher",
            OutputFormat.PYDANTIC: "py",
            OutputFormat.TYPESCRIPT: "ts",
            OutputFormat.GRAPHQL: "graphql",
        }

        for format, output in result.outputs.items():
            ext = extensions.get(format, "txt")
            filename = f"{result.schema_name}.{ext}"
            filepath = schema_dir / filename

            with open(filepath, "w") as f:
                f.write(output)

        # Write metadata
        metadata_path = schema_dir / "compilation_metadata.json"
        with open(metadata_path, "w") as f:
            metadata = {
                "schema_name": result.schema_name,
                "schema_version": result.schema_version,
                "compiled_at": result.compiled_at.isoformat(),
                "formats_generated": [f.value for f in result.outputs.keys()],
                "warnings": result.warnings,
            }
            json.dump(metadata, f, indent=2)

    def compile_from_yaml(
        self,
        yaml_path: Union[str, Path],
        formats: Optional[List[OutputFormat]] = None
    ) -> CompilationResult:
        """
        Convenience method to compile from a YAML file.

        Args:
            yaml_path: Path to the LinkML YAML file.
            formats: Output formats to generate.

        Returns:
            CompilationResult with generated outputs.
        """
        return self.compile(Path(yaml_path), formats)

    def compile_to_files(
        self,
        schema: Union[OntologySchema, SchemaDefinition, Path, str],
        output_dir: Union[str, Path],
        formats: Optional[List[OutputFormat]] = None
    ) -> CompilationResult:
        """
        Compile a schema and write outputs to files.

        Args:
            schema: The schema to compile.
            output_dir: Directory to write output files.
            formats: Output formats to generate.

        Returns:
            CompilationResult with generated outputs.
        """
        old_output_dir = self.output_dir
        self.output_dir = Path(output_dir)

        try:
            result = self.compile(schema, formats)
        finally:
            self.output_dir = old_output_dir

        return result

    def generate_migration(
        self,
        from_schema: Optional[Union[OntologySchema, Path, str]],
        to_schema: Union[OntologySchema, Path, str]
    ) -> str:
        """
        Generate SQL migration between two schema versions.

        Args:
            from_schema: Previous schema version (None for initial).
            to_schema: Target schema version.

        Returns:
            SQL migration string.
        """
        from_ontology = self._normalize_schema(from_schema) if from_schema else None
        to_ontology = self._normalize_schema(to_schema)

        return self.sql_generator.generate_migration(from_ontology, to_ontology)


def compile_schema(
    schema: Union[OntologySchema, SchemaDefinition, Path, str],
    formats: Optional[List[OutputFormat]] = None,
    output_dir: Optional[Path] = None,
    config: Optional[GeneratorConfig] = None
) -> CompilationResult:
    """
    Convenience function to compile a schema.

    Args:
        schema: The schema to compile.
        formats: Output formats to generate.
        output_dir: Optional directory for output files.
        config: Optional generator configuration.

    Returns:
        CompilationResult with generated outputs.

    Example:
        >>> result = compile_schema("my_schema.yaml", formats=[OutputFormat.SQL, OutputFormat.PYDANTIC])
        >>> print(result.get_output(OutputFormat.SQL))
    """
    compiler = OntologyCompiler(config=config, output_dir=output_dir)
    return compiler.compile(schema, formats)
