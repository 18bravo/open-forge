"""
Code generation engine.
Orchestrates all generators to produce output files from ontology schemas.
"""
from typing import Dict, List, Optional, Type, Union
from pathlib import Path
from datetime import datetime
import json

from ontology.models import OntologySchema
from ontology.schema import SchemaManager

from codegen.models import GeneratorType, OutputFile, GenerationResult
from codegen.config import CodegenConfig
from codegen.generators.base import BaseGenerator
from codegen.generators.fastapi_generator import FastAPIGenerator
from codegen.generators.orm_generator import ORMGenerator
from codegen.generators.test_generator import TestGenerator
from codegen.generators.hooks_generator import HooksGenerator


# Registry of available generators
GENERATOR_REGISTRY: Dict[str, Type[BaseGenerator]] = {
    "fastapi": FastAPIGenerator,
    "orm": ORMGenerator,
    "tests": TestGenerator,
    "hooks": HooksGenerator,
}


class CodegenEngine:
    """
    Main code generation engine.

    Orchestrates multiple generators to produce a complete set of
    generated code from an ontology schema.
    """

    def __init__(
        self,
        config: Optional[CodegenConfig] = None,
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize the code generation engine.

        Args:
            config: Code generation configuration.
            template_dir: Custom template directory.
        """
        self.config = config or CodegenConfig()
        self.template_dir = template_dir
        self.schema_manager = SchemaManager()
        self._generators: Dict[str, BaseGenerator] = {}

        # Initialize enabled generators
        self._init_generators()

    def _init_generators(self) -> None:
        """Initialize all enabled generators."""
        for generator_name in self.config.get_enabled_generators():
            generator_name_lower = generator_name.lower()
            if generator_name_lower in GENERATOR_REGISTRY:
                generator_class = GENERATOR_REGISTRY[generator_name_lower]
                self._generators[generator_name_lower] = generator_class(
                    self.config,
                    self.template_dir,
                )

    def generate(
        self,
        schema: Union[OntologySchema, Path, str],
        generators: Optional[List[str]] = None,
    ) -> GenerationResult:
        """
        Generate code from an ontology schema.

        Args:
            schema: The schema to generate code from. Can be:
                - OntologySchema object
                - Path to a YAML file
                - YAML string
            generators: Optional list of generators to run.
                       If not specified, uses enabled generators from config.

        Returns:
            GenerationResult with all generated files.
        """
        errors: List[str] = []
        warnings: List[str] = []
        files: List[OutputFile] = []

        # Normalize schema
        try:
            ontology_schema = self._normalize_schema(schema)
        except Exception as e:
            return GenerationResult(
                schema_name="unknown",
                schema_version="unknown",
                errors=[f"Failed to load schema: {str(e)}"],
            )

        # Validate schema
        validation = self.schema_manager.validate_schema(ontology_schema)
        if not validation.is_valid:
            errors.extend([e.message for e in validation.errors])
        warnings.extend([w.message for w in validation.warnings])

        # Determine which generators to run
        if generators is None:
            generators_to_run = list(self._generators.keys())
        else:
            generators_to_run = [g.lower() for g in generators if g.lower() in self._generators]

        # Run each generator
        for gen_name in generators_to_run:
            generator = self._generators.get(gen_name)
            if generator:
                try:
                    gen_files = generator.generate(ontology_schema)
                    files.extend(gen_files)
                except Exception as e:
                    errors.append(f"Generator '{gen_name}' failed: {str(e)}")

        return GenerationResult(
            schema_name=ontology_schema.name,
            schema_version=ontology_schema.version,
            files=files,
            errors=errors,
            warnings=warnings,
        )

    def _normalize_schema(
        self,
        schema: Union[OntologySchema, Path, str],
    ) -> OntologySchema:
        """Normalize input to OntologySchema."""
        if isinstance(schema, OntologySchema):
            return schema

        if isinstance(schema, Path):
            linkml_schema = self.schema_manager.load_linkml_yaml(schema)
            return self.schema_manager.linkml_to_ontology_schema(linkml_schema)

        if isinstance(schema, str):
            # Check if it's a file path or YAML content
            if schema.strip().startswith(("id:", "name:", "classes:")):
                linkml_schema = self.schema_manager.load_linkml_from_string(schema)
            else:
                linkml_schema = self.schema_manager.load_linkml_yaml(Path(schema))
            return self.schema_manager.linkml_to_ontology_schema(linkml_schema)

        raise ValueError(f"Unsupported schema type: {type(schema)}")

    def generate_to_files(
        self,
        schema: Union[OntologySchema, Path, str],
        output_dir: Optional[Path] = None,
        generators: Optional[List[str]] = None,
    ) -> GenerationResult:
        """
        Generate code and write to files.

        Args:
            schema: The schema to generate code from.
            output_dir: Directory to write output files.
            generators: Optional list of generators to run.

        Returns:
            GenerationResult with generated files.
        """
        result = self.generate(schema, generators)

        if result.has_errors():
            return result

        # Determine output directory
        out_dir = output_dir or self.config.output_dir
        out_dir = Path(out_dir)

        # Clean output if configured
        if self.config.clean_output and out_dir.exists():
            import shutil
            shutil.rmtree(out_dir)

        # Write files
        if not self.config.dry_run:
            self._write_files(result.files, out_dir)
            self._write_metadata(result, out_dir)

        return result

    def _write_files(self, files: List[OutputFile], output_dir: Path) -> None:
        """Write generated files to disk."""
        for file in files:
            file_path = output_dir / file.path

            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file exists
            if file_path.exists() and not file.overwrite:
                continue

            # Write file
            with open(file_path, "w") as f:
                f.write(file.content)

    def _write_metadata(self, result: GenerationResult, output_dir: Path) -> None:
        """Write generation metadata."""
        metadata_path = output_dir / "codegen_metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        metadata = {
            "schema_name": result.schema_name,
            "schema_version": result.schema_version,
            "generated_at": result.generated_at.isoformat(),
            "files_generated": len(result.files),
            "files": [
                {
                    "path": str(f.path),
                    "generator": f.generator.value if hasattr(f.generator, 'value') else str(f.generator),
                }
                for f in result.files
            ],
            "warnings": result.warnings,
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def list_generators(self) -> List[str]:
        """List all available generators."""
        return list(GENERATOR_REGISTRY.keys())

    def get_enabled_generators(self) -> List[str]:
        """Get list of enabled generators."""
        return list(self._generators.keys())

    def add_generator(self, name: str, generator_class: Type[BaseGenerator]) -> None:
        """
        Add a custom generator.

        Args:
            name: Generator name.
            generator_class: Generator class.
        """
        GENERATOR_REGISTRY[name.lower()] = generator_class
        if self.config.is_generator_enabled(name):
            self._generators[name.lower()] = generator_class(
                self.config,
                self.template_dir,
            )


def generate_code(
    schema: Union[OntologySchema, Path, str],
    output_dir: Optional[Path] = None,
    config: Optional[CodegenConfig] = None,
    generators: Optional[List[str]] = None,
) -> GenerationResult:
    """
    Convenience function to generate code from a schema.

    Args:
        schema: The schema to generate code from.
        output_dir: Optional output directory.
        config: Optional configuration.
        generators: Optional list of generators to run.

    Returns:
        GenerationResult with generated files.

    Example:
        >>> result = generate_code(
        ...     "my_schema.yaml",
        ...     output_dir=Path("generated"),
        ...     generators=["fastapi", "orm"]
        ... )
        >>> print(f"Generated {len(result.files)} files")
    """
    engine = CodegenEngine(config=config)

    if output_dir:
        return engine.generate_to_files(schema, output_dir, generators)
    return engine.generate(schema, generators)
