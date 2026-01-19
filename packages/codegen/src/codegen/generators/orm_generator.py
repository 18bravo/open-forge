"""
SQLAlchemy ORM generator from ontology schemas.
Generates SQLAlchemy 2.0 models with relationships and async support.
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
from codegen.config import CodegenConfig, ORMConfig
from codegen.generators.base import BaseGenerator


class ORMGenerator(BaseGenerator):
    """
    Generates SQLAlchemy ORM models from ontology schemas.

    Produces:
    - SQLAlchemy 2.0 declarative models
    - Relationship mappings (one-to-one, one-to-many, many-to-many)
    - Async session support
    - Proper foreign key constraints
    """

    generator_type = GeneratorType.ORM

    def __init__(self, config: CodegenConfig, template_dir: Optional[Path] = None):
        super().__init__(config, template_dir)
        self.orm_config: ORMConfig = config.orm

    def generate(self, schema: OntologySchema) -> List[OutputFile]:
        """
        Generate SQLAlchemy ORM models from an ontology schema.

        Args:
            schema: The ontology schema to generate models for.

        Returns:
            List of generated output files.
        """
        files: List[OutputFile] = []

        # Build context for all entities
        entities = []
        for ontology_type in schema.types:
            if not ontology_type.abstract:
                entity_ctx = self.build_entity_context(ontology_type, schema)
                entity_ctx = self._enrich_entity_for_orm(entity_ctx, schema)
                entities.append(entity_ctx)

        # Generate base model file
        base_content = self._generate_base()
        files.append(OutputFile(
            path=Path("db/models/base.py"),
            content=base_content,
            generator=self.generator_type,
        ))

        # Generate model file for each entity
        for entity in entities:
            model_content = self._generate_model(entity, schema, entities)
            files.append(OutputFile(
                path=Path(f"db/models/{entity.name_snake}.py"),
                content=model_content,
                generator=self.generator_type,
            ))

        # Generate models index
        index_content = self._generate_index(entities)
        files.append(OutputFile(
            path=Path("db/models/__init__.py"),
            content=index_content,
            generator=self.generator_type,
        ))

        return files

    def _enrich_entity_for_orm(
        self,
        entity: EntityContext,
        schema: OntologySchema,
    ) -> EntityContext:
        """Enrich entity context with ORM-specific information."""
        # Find incoming relationships (where this entity is the target)
        incoming_rels = []
        for rel in schema.relationships:
            if rel.target_type == entity.name:
                incoming_rels.append(self._process_relationship(rel))

        # Add ORM-specific metadata
        entity.metadata["incoming_relationships"] = incoming_rels
        entity.metadata["table_name"] = f"{self.orm_config.table_prefix}{entity.name_snake}"
        entity.metadata["schema_name"] = self.orm_config.schema_name

        # Determine if this entity needs a junction table
        for rel in entity.relationships:
            if rel.get("cardinality") == "many_to_many":
                rel["junction_table"] = f"{entity.name_snake}_{rel['name_snake']}"

        return entity

    def _generate_base(self) -> str:
        """Generate base model file with common utilities."""
        context = {
            "config": self.orm_config,
            "generated_at": datetime.now().isoformat(),
        }
        return self.render_template("orm/base.py.j2", context)

    def _generate_model(
        self,
        entity: EntityContext,
        schema: OntologySchema,
        all_entities: List[EntityContext],
    ) -> str:
        """Generate SQLAlchemy model for an entity."""
        # Find related entity names for imports
        related_entities = set()
        for rel in entity.relationships:
            related_entities.add(rel["target_type"])
        for rel in entity.metadata.get("incoming_relationships", []):
            related_entities.add(rel["source_type"])
        related_entities.discard(entity.name)  # Remove self-references

        context = {
            "entity": entity,
            "schema_name": schema.name,
            "generated_at": datetime.now().isoformat(),
            "config": self.orm_config,
            "related_entities": list(related_entities),
            "all_entities": [e.name for e in all_entities],
        }

        return self.render_template("orm/model.py.j2", context)

    def _generate_index(self, entities: List[EntityContext]) -> str:
        """Generate models index file."""
        context = {
            "entities": entities,
            "generated_at": datetime.now().isoformat(),
            "config": self.orm_config,
        }
        return self.render_template("orm/index.py.j2", context)
