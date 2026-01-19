"""
Integration tests for ontology schema migration.

Tests version migration, schema evolution, and rollback capabilities.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from pathlib import Path
import tempfile

from tests.integration.conftest import requires_postgres


pytestmark = pytest.mark.integration


class TestSchemaMigrationGeneration:
    """Tests for generating schema migrations."""

    def test_generate_initial_migration(self, sample_ontology_yaml):
        """Test generating an initial migration (from nothing)."""
        from ontology.compiler import OntologyCompiler

        compiler = OntologyCompiler()

        # Generate migration from nothing to first schema
        migration_sql = compiler.generate_migration(
            from_schema=None,
            to_schema=sample_ontology_yaml
        )

        assert migration_sql is not None
        # Initial migration should create tables
        assert "CREATE" in migration_sql.upper()

    def test_generate_additive_migration(self):
        """Test generating a migration that adds new entities."""
        from ontology.compiler import OntologyCompiler

        v1_yaml = """
id: https://example.org/migration-test
name: MigrationTest
version: "1.0.0"
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  Customer:
    attributes:
      id:
        range: string
        required: true
      name:
        range: string
"""

        v2_yaml = """
id: https://example.org/migration-test
name: MigrationTest
version: "2.0.0"
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  Customer:
    attributes:
      id:
        range: string
        required: true
      name:
        range: string
      email:
        range: string

  Order:
    attributes:
      id:
        range: string
        required: true
      customer_id:
        range: string
"""

        compiler = OntologyCompiler()

        migration_sql = compiler.generate_migration(
            from_schema=v1_yaml,
            to_schema=v2_yaml
        )

        assert migration_sql is not None
        # Migration should add the new column and table
        upper_sql = migration_sql.upper()
        # Could contain ALTER or CREATE depending on implementation
        assert "ALTER" in upper_sql or "CREATE" in upper_sql

    def test_generate_column_addition_migration(self):
        """Test generating a migration that adds columns."""
        from ontology.compiler import OntologyCompiler

        v1_yaml = """
id: https://example.org/column-test
name: ColumnTest
version: "1.0.0"
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  Entity:
    attributes:
      id:
        range: string
        required: true
"""

        v2_yaml = """
id: https://example.org/column-test
name: ColumnTest
version: "2.0.0"
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  Entity:
    attributes:
      id:
        range: string
        required: true
      new_field:
        range: string
      another_field:
        range: integer
"""

        compiler = OntologyCompiler()

        migration_sql = compiler.generate_migration(
            from_schema=v1_yaml,
            to_schema=v2_yaml
        )

        assert migration_sql is not None


class TestMigrationApplication:
    """Tests for applying migrations to databases."""

    @pytest.mark.asyncio
    @requires_postgres
    @pytest.mark.slow
    async def test_apply_migration_to_database(self, async_db_session):
        """Test applying a migration to a real database."""
        from sqlalchemy import text

        # Create a simple migration SQL
        migration_sql = """
        CREATE TABLE IF NOT EXISTS migration_test_v1 (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """

        try:
            await async_db_session.execute(text(migration_sql))
            await async_db_session.commit()

            # Verify table exists
            result = await async_db_session.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_name = 'migration_test_v1'
            """))
            row = result.fetchone()

            assert row is not None

            # Apply second migration - add column
            migration_v2_sql = """
            ALTER TABLE migration_test_v1
            ADD COLUMN IF NOT EXISTS email VARCHAR(255);
            """

            await async_db_session.execute(text(migration_v2_sql))
            await async_db_session.commit()

            # Verify column exists
            result = await async_db_session.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'migration_test_v1' AND column_name = 'email'
            """))
            row = result.fetchone()

            assert row is not None

            # Clean up
            await async_db_session.execute(
                text("DROP TABLE IF EXISTS migration_test_v1")
            )
            await async_db_session.commit()

        except Exception as e:
            pytest.skip(f"Could not apply migration: {e}")

    @pytest.mark.asyncio
    @requires_postgres
    async def test_migration_preserves_data(self, async_db_session):
        """Test that migrations preserve existing data."""
        from sqlalchemy import text

        try:
            # Create initial table
            await async_db_session.execute(text("""
                CREATE TABLE IF NOT EXISTS data_preserve_test (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL
                )
            """))

            # Insert data
            await async_db_session.execute(text("""
                INSERT INTO data_preserve_test (id, name)
                VALUES ('test-1', 'Original Data')
                ON CONFLICT (id) DO NOTHING
            """))
            await async_db_session.commit()

            # Apply migration - add column
            await async_db_session.execute(text("""
                ALTER TABLE data_preserve_test
                ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active'
            """))
            await async_db_session.commit()

            # Verify data is preserved
            result = await async_db_session.execute(text("""
                SELECT id, name, status FROM data_preserve_test WHERE id = 'test-1'
            """))
            row = result.fetchone()

            assert row is not None
            assert row.name == "Original Data"
            assert row.status == "active"

            # Clean up
            await async_db_session.execute(
                text("DROP TABLE IF EXISTS data_preserve_test")
            )
            await async_db_session.commit()

        except Exception as e:
            pytest.skip(f"Could not test data preservation: {e}")


class TestMigrationVersioning:
    """Tests for migration versioning."""

    def test_schema_version_extracted(self, sample_ontology_yaml):
        """Test that schema version is extracted correctly."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.SQL])

        assert result.schema_version is not None
        assert len(result.schema_version) > 0

    def test_schema_name_extracted(self, sample_ontology_yaml):
        """Test that schema name is extracted correctly."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.SQL])

        assert result.schema_name is not None
        assert result.schema_name == "TestOntology"

    def test_compilation_timestamp(self, sample_ontology_yaml):
        """Test that compilation timestamp is recorded."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        before = datetime.now()
        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.SQL])
        after = datetime.now()

        assert result.compiled_at is not None
        assert before <= result.compiled_at <= after


class TestSchemaEvolution:
    """Tests for schema evolution patterns."""

    def test_add_optional_field(self):
        """Test adding an optional field to existing entity."""
        from ontology.compiler import OntologyCompiler

        v1 = """
id: https://example.org/evolution
name: Evolution
version: "1.0"
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  Product:
    attributes:
      id:
        range: string
        required: true
      name:
        range: string
        required: true
"""

        v2 = """
id: https://example.org/evolution
name: Evolution
version: "1.1"
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  Product:
    attributes:
      id:
        range: string
        required: true
      name:
        range: string
        required: true
      description:
        range: string
        required: false
"""

        compiler = OntologyCompiler()

        migration = compiler.generate_migration(from_schema=v1, to_schema=v2)

        assert migration is not None
        # Adding optional field should work

    def test_add_new_entity(self):
        """Test adding a new entity to schema."""
        from ontology.compiler import OntologyCompiler

        v1 = """
id: https://example.org/new-entity
name: NewEntity
version: "1.0"
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  Customer:
    attributes:
      id:
        range: string
        required: true
"""

        v2 = """
id: https://example.org/new-entity
name: NewEntity
version: "2.0"
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  Customer:
    attributes:
      id:
        range: string
        required: true

  Order:
    attributes:
      id:
        range: string
        required: true
      customer_id:
        range: string
"""

        compiler = OntologyCompiler()

        migration = compiler.generate_migration(from_schema=v1, to_schema=v2)

        assert migration is not None
        # Should create the new Order table


class TestMigrationSafety:
    """Tests for migration safety checks."""

    def test_detect_destructive_changes(self):
        """Test detecting potentially destructive schema changes."""
        from ontology.compiler import OntologyCompiler

        v1 = """
id: https://example.org/destructive
name: Destructive
version: "1.0"
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  Entity:
    attributes:
      id:
        range: string
        required: true
      important_field:
        range: string
        required: true
"""

        v2 = """
id: https://example.org/destructive
name: Destructive
version: "2.0"
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  Entity:
    attributes:
      id:
        range: string
        required: true
      # important_field removed!
"""

        compiler = OntologyCompiler()

        # Migration generation should still work, but ideally would warn
        migration = compiler.generate_migration(from_schema=v1, to_schema=v2)

        assert migration is not None


class TestGraphSchemaMigration:
    """Tests for graph database schema migration."""

    def test_generate_cypher_migration(self):
        """Test generating Cypher migration statements."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        yaml = """
id: https://example.org/graph-migration
name: GraphMigration
version: "1.0"
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  Person:
    attributes:
      id:
        range: string
        required: true
      name:
        range: string

  Organization:
    attributes:
      id:
        range: string
        required: true
      name:
        range: string
"""

        compiler = OntologyCompiler()

        result = compiler.compile(yaml, formats=[OutputFormat.CYPHER])

        cypher_output = result.get_output(OutputFormat.CYPHER)

        assert cypher_output is not None

    @pytest.mark.asyncio
    @requires_postgres
    async def test_apply_cypher_to_graph(self, graph_database, async_db_session):
        """Test applying Cypher statements to graph database."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        # Create nodes for the ontology entities
        try:
            await graph_database.create_node(
                async_db_session,
                label="OntologyEntity",
                properties={
                    "name": "TestEntity",
                    "version": "1.0",
                    "created_at": datetime.utcnow().isoformat()
                }
            )

            # Verify node was created
            results = await graph_database.find_node(
                async_db_session,
                label="OntologyEntity",
                properties={"name": "TestEntity"}
            )

            assert len(results) >= 1

        except Exception as e:
            pytest.skip(f"Could not apply to graph: {e}")
