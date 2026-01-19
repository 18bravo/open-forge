"""
Open Forge Ontology Package

LinkML-based ontology management for data modeling.
Provides schema management, compilation, and code generation for multiple targets.

Example usage:
    >>> from ontology import OntologyCompiler, OutputFormat
    >>> compiler = OntologyCompiler()
    >>> result = compiler.compile("my_schema.yaml", formats=[OutputFormat.SQL, OutputFormat.PYDANTIC])
    >>> print(result.get_output(OutputFormat.SQL))
"""

from ontology.models import (
    PropertyType,
    Cardinality,
    ConstraintType,
    Constraint,
    Property,
    Relationship,
    OntologyType,
    OntologySchema,
    SchemaVersion,
    SchemaValidationError,
    SchemaValidationResult,
)

from ontology.schema import SchemaManager

from ontology.compiler import (
    OntologyCompiler,
    OutputFormat,
    CompilationResult,
    GeneratorConfig,
    compile_schema,
)

from ontology.generators import (
    SQLGenerator,
    CypherGenerator,
    PydanticGenerator,
    TypeScriptGenerator,
    GraphQLGenerator,
)

__all__ = [
    # Models
    "PropertyType",
    "Cardinality",
    "ConstraintType",
    "Constraint",
    "Property",
    "Relationship",
    "OntologyType",
    "OntologySchema",
    "SchemaVersion",
    "SchemaValidationError",
    "SchemaValidationResult",
    # Schema management
    "SchemaManager",
    # Compiler
    "OntologyCompiler",
    "OutputFormat",
    "CompilationResult",
    "GeneratorConfig",
    "compile_schema",
    # Generators
    "SQLGenerator",
    "CypherGenerator",
    "PydanticGenerator",
    "TypeScriptGenerator",
    "GraphQLGenerator",
]

__version__ = "0.1.0"
