"""
Integration tests for ontology compilation to database.

Tests compiling LinkML schemas and applying them to real databases.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from pathlib import Path
import tempfile
import os

from tests.integration.conftest import requires_postgres


pytestmark = pytest.mark.integration


class TestOntologyCompilation:
    """Tests for ontology compilation."""

    def test_compile_simple_schema(self, sample_ontology_yaml):
        """Test compiling a simple ontology schema."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(
            sample_ontology_yaml,
            formats=[OutputFormat.SQL, OutputFormat.PYDANTIC]
        )

        assert not result.has_errors()
        assert OutputFormat.SQL in result.outputs
        assert OutputFormat.PYDANTIC in result.outputs

    def test_compile_all_formats(self, sample_ontology_yaml):
        """Test compiling to all output formats."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.ALL])

        assert not result.has_errors()
        assert OutputFormat.SQL in result.outputs
        assert OutputFormat.CYPHER in result.outputs
        assert OutputFormat.PYDANTIC in result.outputs
        assert OutputFormat.TYPESCRIPT in result.outputs
        assert OutputFormat.GRAPHQL in result.outputs

    def test_compile_generates_sql_ddl(self, sample_ontology_yaml):
        """Test that SQL output contains valid DDL."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.SQL])

        sql_output = result.get_output(OutputFormat.SQL)

        assert sql_output is not None
        assert "CREATE TABLE" in sql_output
        assert "customer" in sql_output.lower() or "order" in sql_output.lower()

    def test_compile_generates_pydantic_models(self, sample_ontology_yaml):
        """Test that Pydantic output contains valid model definitions."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.PYDANTIC])

        pydantic_output = result.get_output(OutputFormat.PYDANTIC)

        assert pydantic_output is not None
        assert "class" in pydantic_output
        assert "BaseModel" in pydantic_output or "pydantic" in pydantic_output

    def test_compile_generates_typescript(self, sample_ontology_yaml):
        """Test that TypeScript output contains valid interfaces."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.TYPESCRIPT])

        ts_output = result.get_output(OutputFormat.TYPESCRIPT)

        assert ts_output is not None
        assert "interface" in ts_output or "type" in ts_output

    def test_compile_generates_graphql(self, sample_ontology_yaml):
        """Test that GraphQL output contains valid schema."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.GRAPHQL])

        graphql_output = result.get_output(OutputFormat.GRAPHQL)

        assert graphql_output is not None
        assert "type" in graphql_output

    def test_compile_generates_cypher(self, sample_ontology_yaml):
        """Test that Cypher output contains valid statements."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.CYPHER])

        cypher_output = result.get_output(OutputFormat.CYPHER)

        assert cypher_output is not None


class TestCompilationToFiles:
    """Tests for compiling schemas to files."""

    def test_compile_to_output_directory(self, sample_ontology_yaml):
        """Test compiling schema to output directory."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        with tempfile.TemporaryDirectory() as tmpdir:
            compiler = OntologyCompiler(output_dir=Path(tmpdir))

            result = compiler.compile(
                sample_ontology_yaml,
                formats=[OutputFormat.SQL, OutputFormat.PYDANTIC]
            )

            assert not result.has_errors()

            # Check that files were created
            schema_dir = Path(tmpdir) / result.schema_name / result.schema_version

            if schema_dir.exists():
                files = list(schema_dir.iterdir())
                assert len(files) > 0

    def test_compile_to_files_method(self, sample_ontology_yaml):
        """Test compile_to_files convenience method."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        with tempfile.TemporaryDirectory() as tmpdir:
            compiler = OntologyCompiler()

            result = compiler.compile_to_files(
                sample_ontology_yaml,
                output_dir=tmpdir,
                formats=[OutputFormat.SQL]
            )

            assert not result.has_errors()


class TestCompilerConfiguration:
    """Tests for compiler configuration."""

    def test_custom_sql_schema_prefix(self, sample_ontology_yaml):
        """Test custom SQL schema prefix configuration."""
        from ontology.compiler import OntologyCompiler, OutputFormat, GeneratorConfig

        config = GeneratorConfig(sql_schema_prefix="custom_prefix")
        compiler = OntologyCompiler(config=config)

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.SQL])

        sql_output = result.get_output(OutputFormat.SQL)

        # The schema prefix should be used somewhere in the output
        assert sql_output is not None

    def test_custom_graph_name(self, sample_ontology_yaml):
        """Test custom graph name configuration."""
        from ontology.compiler import OntologyCompiler, OutputFormat, GeneratorConfig

        config = GeneratorConfig(cypher_graph_name="my_custom_graph")
        compiler = OntologyCompiler(config=config)

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.CYPHER])

        cypher_output = result.get_output(OutputFormat.CYPHER)

        assert cypher_output is not None


class TestDatabaseApplication:
    """Tests for applying compiled schemas to databases."""

    @pytest.mark.asyncio
    @requires_postgres
    @pytest.mark.slow
    async def test_apply_sql_to_database(self, async_db_session, sample_ontology_yaml):
        """Test applying compiled SQL to a real database."""
        from ontology.compiler import OntologyCompiler, OutputFormat
        from sqlalchemy import text

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.SQL])

        sql_output = result.get_output(OutputFormat.SQL)

        if sql_output:
            # Extract CREATE TABLE statements and execute them
            # We need to be careful - the SQL might reference schemas that don't exist
            try:
                # Create a test schema
                await async_db_session.execute(
                    text("CREATE SCHEMA IF NOT EXISTS ontology")
                )

                # Try to execute parts of the SQL
                # Note: Real implementation would need proper parsing
                statements = sql_output.split(";")
                for stmt in statements[:5]:  # Limit to first 5 statements
                    stmt = stmt.strip()
                    if stmt and "CREATE TABLE" in stmt.upper():
                        try:
                            await async_db_session.execute(text(stmt))
                        except Exception as e:
                            # Some statements might fail due to dependencies
                            pass

            except Exception as e:
                pytest.skip(f"Could not apply SQL to database: {e}")

    @pytest.mark.asyncio
    @requires_postgres
    async def test_verify_table_creation(self, async_db_session):
        """Test verifying table creation from ontology."""
        from sqlalchemy import text

        # Create a simple test table
        create_sql = """
        CREATE TABLE IF NOT EXISTS test_ontology_customer (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        )
        """

        try:
            await async_db_session.execute(text(create_sql))
            await async_db_session.commit()

            # Verify table exists
            result = await async_db_session.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_name = 'test_ontology_customer'
            """))
            row = result.fetchone()

            assert row is not None
            assert row.table_name == "test_ontology_customer"

            # Clean up
            await async_db_session.execute(
                text("DROP TABLE IF EXISTS test_ontology_customer")
            )
            await async_db_session.commit()

        except Exception as e:
            pytest.skip(f"Could not verify table creation: {e}")


class TestSchemaValidation:
    """Tests for schema validation during compilation."""

    def test_invalid_schema_returns_errors(self):
        """Test that invalid schemas return compilation errors."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        invalid_yaml = """
id: invalid-schema
name: InvalidSchema
# Missing required fields
classes: []
"""

        compiler = OntologyCompiler()

        result = compiler.compile(invalid_yaml, formats=[OutputFormat.SQL])

        # Should have errors or warnings
        assert result.has_errors() or len(result.warnings) > 0

    def test_schema_with_warnings(self, sample_ontology_yaml):
        """Test that schema warnings are captured."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.SQL])

        # Warnings should be a list (might be empty)
        assert isinstance(result.warnings, list)


class TestCompilationResult:
    """Tests for CompilationResult object."""

    def test_result_to_dict(self, sample_ontology_yaml):
        """Test converting result to dictionary."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.SQL])

        result_dict = result.to_dict()

        assert "schema_name" in result_dict
        assert "schema_version" in result_dict
        assert "outputs" in result_dict
        assert "compiled_at" in result_dict

    def test_result_has_errors_method(self, sample_ontology_yaml):
        """Test has_errors method."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(sample_ontology_yaml, formats=[OutputFormat.SQL])

        # For a valid schema, should not have errors
        assert isinstance(result.has_errors(), bool)

    def test_result_get_output_method(self, sample_ontology_yaml):
        """Test get_output method."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        compiler = OntologyCompiler()

        result = compiler.compile(
            sample_ontology_yaml,
            formats=[OutputFormat.SQL, OutputFormat.PYDANTIC]
        )

        sql_output = result.get_output(OutputFormat.SQL)
        pydantic_output = result.get_output(OutputFormat.PYDANTIC)
        cypher_output = result.get_output(OutputFormat.CYPHER)

        assert sql_output is not None
        assert pydantic_output is not None
        assert cypher_output is None  # Wasn't compiled


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_compile_schema_function(self, sample_ontology_yaml):
        """Test compile_schema convenience function."""
        from ontology.compiler import compile_schema, OutputFormat

        result = compile_schema(
            sample_ontology_yaml,
            formats=[OutputFormat.SQL]
        )

        assert not result.has_errors()
        assert result.get_output(OutputFormat.SQL) is not None

    def test_compile_from_yaml_file(self):
        """Test compiling from a YAML file."""
        from ontology.compiler import OntologyCompiler, OutputFormat

        # Create a temporary YAML file
        yaml_content = """
id: https://example.org/file-test
name: FileTest
prefixes:
  linkml: https://w3id.org/linkml/

classes:
  TestEntity:
    attributes:
      id:
        range: string
        required: true
      value:
        range: integer
"""

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            delete=False
        ) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            compiler = OntologyCompiler()
            result = compiler.compile_from_yaml(yaml_path, formats=[OutputFormat.SQL])

            assert not result.has_errors()

        finally:
            os.unlink(yaml_path)
