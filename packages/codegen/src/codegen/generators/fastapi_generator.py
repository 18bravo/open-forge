"""
FastAPI route generator from ontology schemas.
Generates REST API endpoints with CRUD operations, Pydantic schemas, and OpenTelemetry tracing.
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
from codegen.config import CodegenConfig, FastAPIConfig
from codegen.generators.base import BaseGenerator


class FastAPIGenerator(BaseGenerator):
    """
    Generates FastAPI routes from ontology schemas.

    Produces:
    - REST API endpoints for CRUD operations
    - Pydantic request/response schemas
    - OpenTelemetry tracing decorators
    - Pagination for list endpoints
    """

    generator_type = GeneratorType.FASTAPI

    def __init__(self, config: CodegenConfig, template_dir: Optional[Path] = None):
        super().__init__(config, template_dir)
        self.fastapi_config: FastAPIConfig = config.fastapi

    def generate(self, schema: OntologySchema) -> List[OutputFile]:
        """
        Generate FastAPI routes and schemas from an ontology schema.

        Args:
            schema: The ontology schema to generate routes for.

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

        # Generate schemas file
        if self.fastapi_config.generate_schemas:
            schemas_content = self._generate_schemas(schema, entities)
            files.append(OutputFile(
                path=Path("api/schemas/generated.py"),
                content=schemas_content,
                generator=self.generator_type,
            ))

        # Generate routes for each entity
        for entity in entities:
            route_content = self._generate_route(entity, schema)
            files.append(OutputFile(
                path=Path(f"api/routers/{entity.name_snake}.py"),
                content=route_content,
                generator=self.generator_type,
            ))

        # Generate router index
        router_index = self._generate_router_index(entities)
        files.append(OutputFile(
            path=Path("api/routers/generated/__init__.py"),
            content=router_index,
            generator=self.generator_type,
        ))

        return files

    def _generate_schemas(
        self,
        schema: OntologySchema,
        entities: List[EntityContext],
    ) -> str:
        """Generate Pydantic schemas for all entities."""
        context = {
            "schema_name": schema.name,
            "schema_version": schema.version,
            "generated_at": datetime.now().isoformat(),
            "entities": [self._prepare_entity_for_schema(e) for e in entities],
            "config": self.fastapi_config,
        }

        return self.render_template("fastapi/schemas.py.j2", context)

    def _generate_route(
        self,
        entity: EntityContext,
        schema: OntologySchema,
    ) -> str:
        """Generate FastAPI route file for an entity."""
        context = {
            "entity": entity,
            "schema_name": schema.name,
            "generated_at": datetime.now().isoformat(),
            "config": self.fastapi_config,
            "has_relationships": len(entity.relationships) > 0,
        }

        return self.render_template("fastapi/route.py.j2", context)

    def _generate_router_index(self, entities: List[EntityContext]) -> str:
        """Generate router index file."""
        context = {
            "entities": entities,
            "generated_at": datetime.now().isoformat(),
        }

        return self.render_template("fastapi/router_index.py.j2", context)

    def _prepare_entity_for_schema(self, entity: EntityContext) -> Dict[str, Any]:
        """Prepare entity context for schema generation."""
        # Separate required and optional properties
        required_props = [p for p in entity.properties if p.get("required", False)]
        optional_props = [p for p in entity.properties if not p.get("required", False)]

        return {
            **entity.model_dump(),
            "required_properties": required_props,
            "optional_properties": optional_props,
            "has_enums": any(p.get("is_enum", False) for p in entity.properties),
        }
