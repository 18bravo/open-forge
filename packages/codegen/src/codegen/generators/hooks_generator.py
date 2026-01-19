"""
React Query hooks generator from ontology schemas.
Generates useQuery/useMutation hooks for type-safe API access.
"""
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

from ontology.models import (
    OntologySchema,
    OntologyType,
    Property,
    PropertyType,
    Relationship,
    Cardinality,
)
from codegen.models import GeneratorType, OutputFile, EntityContext
from codegen.config import CodegenConfig, HooksConfig
from codegen.generators.base import BaseGenerator


class HooksGenerator(BaseGenerator):
    """
    Generates React Query hooks from ontology schemas.

    Produces:
    - useQuery hooks for fetching entities
    - useMutation hooks for CRUD operations
    - Query key factories for cache management
    - TypeScript types for request/response data
    """

    generator_type = GeneratorType.HOOKS

    def __init__(self, config: CodegenConfig, template_dir: Optional[Path] = None):
        super().__init__(config, template_dir)
        self.hooks_config: HooksConfig = config.hooks

    def generate(self, schema: OntologySchema) -> List[OutputFile]:
        """
        Generate React Query hooks from an ontology schema.

        Args:
            schema: The ontology schema to generate hooks for.

        Returns:
            List of generated output files.
        """
        files: List[OutputFile] = []

        # Build context for all entities
        entities = []
        for ontology_type in schema.types:
            if not ontology_type.abstract:
                entity_ctx = self.build_entity_context(ontology_type, schema)
                entities.append(entity_ctx)

        # Generate TypeScript types
        types_content = self._generate_types(schema, entities)
        files.append(OutputFile(
            path=Path("lib/api/types.ts"),
            content=types_content,
            generator=self.generator_type,
        ))

        # Generate API client functions
        api_content = self._generate_api_client(schema, entities)
        files.append(OutputFile(
            path=Path("lib/api/generated.ts"),
            content=api_content,
            generator=self.generator_type,
        ))

        # Generate hook file for each entity
        for entity in entities:
            hook_content = self._generate_hooks(entity, schema)
            files.append(OutputFile(
                path=Path(f"lib/hooks/use-{entity.name_snake.replace('_', '-')}.ts"),
                content=hook_content,
                generator=self.generator_type,
            ))

        # Generate hooks index
        index_content = self._generate_index(entities)
        files.append(OutputFile(
            path=Path("lib/hooks/generated/index.ts"),
            content=index_content,
            generator=self.generator_type,
        ))

        return files

    def _generate_types(
        self,
        schema: OntologySchema,
        entities: List[EntityContext],
    ) -> str:
        """Generate TypeScript type definitions."""
        context = {
            "schema_name": schema.name,
            "generated_at": datetime.now().isoformat(),
            "entities": entities,
            "config": self.hooks_config,
        }
        return self.render_template("hooks/types.ts.j2", context)

    def _generate_api_client(
        self,
        schema: OntologySchema,
        entities: List[EntityContext],
    ) -> str:
        """Generate API client functions."""
        context = {
            "schema_name": schema.name,
            "generated_at": datetime.now().isoformat(),
            "entities": entities,
            "config": self.hooks_config,
        }
        return self.render_template("hooks/api.ts.j2", context)

    def _generate_hooks(
        self,
        entity: EntityContext,
        schema: OntologySchema,
    ) -> str:
        """Generate React Query hooks for an entity."""
        context = {
            "entity": entity,
            "schema_name": schema.name,
            "generated_at": datetime.now().isoformat(),
            "config": self.hooks_config,
        }
        return self.render_template("hooks/use_entity.ts.j2", context)

    def _generate_index(self, entities: List[EntityContext]) -> str:
        """Generate hooks index file."""
        context = {
            "entities": entities,
            "generated_at": datetime.now().isoformat(),
        }
        return self.render_template("hooks/index.ts.j2", context)
