"""
Test generator from ontology schemas.
Generates pytest fixtures, test cases, and factory patterns.
"""
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

from ontology.models import (
    OntologySchema,
    OntologyType,
    Property,
    PropertyType,
)
from codegen.models import GeneratorType, OutputFile, EntityContext
from codegen.config import CodegenConfig, TestConfig
from codegen.generators.base import BaseGenerator


class TestGenerator(BaseGenerator):
    """
    Generates pytest tests from ontology schemas.

    Produces:
    - Pytest fixtures for database and API testing
    - Factory patterns for test data generation
    - CRUD test cases for each entity
    - Async test support
    """

    generator_type = GeneratorType.TESTS

    def __init__(self, config: CodegenConfig, template_dir: Optional[Path] = None):
        super().__init__(config, template_dir)
        self.test_config: TestConfig = config.tests

    def generate(self, schema: OntologySchema) -> List[OutputFile]:
        """
        Generate pytest tests from an ontology schema.

        Args:
            schema: The ontology schema to generate tests for.

        Returns:
            List of generated output files.
        """
        files: List[OutputFile] = []

        # Build context for all entities
        entities = []
        for ontology_type in schema.types:
            if not ontology_type.abstract:
                entity_ctx = self.build_entity_context(ontology_type, schema)
                entity_ctx = self._enrich_entity_for_tests(entity_ctx)
                entities.append(entity_ctx)

        # Generate conftest with fixtures
        if self.test_config.include_fixtures:
            conftest_content = self._generate_conftest(schema, entities)
            files.append(OutputFile(
                path=Path("tests/conftest.py"),
                content=conftest_content,
                generator=self.generator_type,
            ))

        # Generate factories
        if self.test_config.include_factories:
            factories_content = self._generate_factories(schema, entities)
            files.append(OutputFile(
                path=Path("tests/factories.py"),
                content=factories_content,
                generator=self.generator_type,
            ))

        # Generate test file for each entity
        for entity in entities:
            test_content = self._generate_tests(entity, schema)
            files.append(OutputFile(
                path=Path(f"tests/test_{entity.name_snake}.py"),
                content=test_content,
                generator=self.generator_type,
            ))

        return files

    def _enrich_entity_for_tests(self, entity: EntityContext) -> EntityContext:
        """Enrich entity context with test-specific information."""
        # Add sample values for each property
        for prop in entity.properties:
            prop["sample_value"] = self._get_sample_value(prop)
            prop["factory_value"] = self._get_factory_value(prop)

        return entity

    def _get_sample_value(self, prop: Dict[str, Any]) -> str:
        """Get a sample value for a property type (as Python literal)."""
        prop_type = prop.get("type", "string")
        prop_name = prop.get("name", "value")

        sample_values = {
            "string": f'f"test_{prop_name}_{{uuid4().hex[:8]}}"',
            "integer": "42",
            "float": "3.14",
            "boolean": "True",
            "datetime": "datetime.utcnow()",
            "date": "date.today()",
            "time": "time(12, 0, 0)",
            "uuid": "str(uuid4())",
            "json": '{"key": "value"}',
            "array": "[]",
            "enum": f'"{prop.get("enum_values", ["default"])[0]}"' if prop.get("enum_values") else '"default"',
        }

        return sample_values.get(prop_type, '"test_value"')

    def _get_factory_value(self, prop: Dict[str, Any]) -> str:
        """Get a factory-style generator for a property."""
        prop_type = prop.get("type", "string")
        prop_name = prop.get("name_snake", "value")

        factory_values = {
            "string": f'factory.LazyAttribute(lambda o: f"test_{prop_name}_{{fake.uuid4()[:8]}}")',
            "integer": "factory.Sequence(lambda n: n + 1)",
            "float": "factory.LazyFunction(lambda: round(fake.pyfloat(min_value=0, max_value=100), 2))",
            "boolean": "factory.LazyFunction(fake.boolean)",
            "datetime": "factory.LazyFunction(datetime.utcnow)",
            "date": "factory.LazyFunction(date.today)",
            "time": "factory.LazyFunction(lambda: time(12, 0, 0))",
            "uuid": "factory.LazyFunction(lambda: str(uuid4()))",
            "json": 'factory.LazyFunction(lambda: {"key": "value"})',
            "array": "factory.LazyFunction(list)",
        }

        if prop_type == "enum" and prop.get("enum_values"):
            values = prop["enum_values"]
            return f'factory.LazyFunction(lambda: fake.random_element({values!r}))'

        return factory_values.get(prop_type, 'factory.LazyAttribute(lambda o: "test")')

    def _generate_conftest(
        self,
        schema: OntologySchema,
        entities: List[EntityContext],
    ) -> str:
        """Generate conftest.py with shared fixtures."""
        context = {
            "schema_name": schema.name,
            "generated_at": datetime.now().isoformat(),
            "entities": entities,
            "config": self.test_config,
        }
        return self.render_template("tests/conftest.py.j2", context)

    def _generate_factories(
        self,
        schema: OntologySchema,
        entities: List[EntityContext],
    ) -> str:
        """Generate factory classes for test data."""
        context = {
            "schema_name": schema.name,
            "generated_at": datetime.now().isoformat(),
            "entities": entities,
            "config": self.test_config,
        }
        return self.render_template("tests/factories.py.j2", context)

    def _generate_tests(
        self,
        entity: EntityContext,
        schema: OntologySchema,
    ) -> str:
        """Generate test file for an entity."""
        context = {
            "entity": entity,
            "schema_name": schema.name,
            "generated_at": datetime.now().isoformat(),
            "config": self.test_config,
        }
        return self.render_template("tests/test_crud.py.j2", context)
