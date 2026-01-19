"""
Tests for code generators.
"""
import pytest
from pathlib import Path
from datetime import datetime

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
from codegen import (
    CodegenEngine,
    CodegenConfig,
    FastAPIConfig,
    ORMConfig,
    TestConfig,
    HooksConfig,
    GeneratorType,
    generate_code,
)
from codegen.generators.base import BaseGenerator
from codegen.generators.fastapi_generator import FastAPIGenerator
from codegen.generators.orm_generator import ORMGenerator
from codegen.generators.test_generator import TestGenerator
from codegen.generators.hooks_generator import HooksGenerator


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_schema() -> OntologySchema:
    """Create a sample ontology schema for testing."""
    return OntologySchema(
        name="TestSchema",
        version="1.0.0",
        description="A test schema for code generation",
        namespace="test",
        types=[
            OntologyType(
                name="User",
                description="A user in the system",
                primary_key="id",
                properties=[
                    Property(
                        name="id",
                        property_type=PropertyType.UUID,
                        required=True,
                        description="Unique identifier",
                    ),
                    Property(
                        name="email",
                        property_type=PropertyType.STRING,
                        required=True,
                        description="User email address",
                        constraints=[
                            Constraint(
                                constraint_type=ConstraintType.MAX_LENGTH,
                                value=255,
                            ),
                            Constraint(
                                constraint_type=ConstraintType.PATTERN,
                                value=r"^[\w\.-]+@[\w\.-]+\.\w+$",
                            ),
                        ],
                    ),
                    Property(
                        name="name",
                        property_type=PropertyType.STRING,
                        required=True,
                        description="Full name",
                    ),
                    Property(
                        name="age",
                        property_type=PropertyType.INTEGER,
                        required=False,
                        description="User age",
                        constraints=[
                            Constraint(
                                constraint_type=ConstraintType.MIN_VALUE,
                                value=0,
                            ),
                            Constraint(
                                constraint_type=ConstraintType.MAX_VALUE,
                                value=150,
                            ),
                        ],
                    ),
                    Property(
                        name="is_active",
                        property_type=PropertyType.BOOLEAN,
                        required=False,
                        default_value=True,
                        description="Whether the user is active",
                    ),
                    Property(
                        name="status",
                        property_type=PropertyType.ENUM,
                        required=True,
                        enum_values=["active", "inactive", "pending"],
                        description="User status",
                    ),
                    Property(
                        name="metadata",
                        property_type=PropertyType.JSON,
                        required=False,
                        description="Additional metadata",
                    ),
                ],
            ),
            OntologyType(
                name="Post",
                description="A blog post",
                primary_key="id",
                properties=[
                    Property(
                        name="id",
                        property_type=PropertyType.UUID,
                        required=True,
                    ),
                    Property(
                        name="title",
                        property_type=PropertyType.STRING,
                        required=True,
                        constraints=[
                            Constraint(
                                constraint_type=ConstraintType.MAX_LENGTH,
                                value=200,
                            ),
                        ],
                    ),
                    Property(
                        name="content",
                        property_type=PropertyType.STRING,
                        required=True,
                    ),
                    Property(
                        name="published_at",
                        property_type=PropertyType.DATETIME,
                        required=False,
                    ),
                    Property(
                        name="tags",
                        property_type=PropertyType.ARRAY,
                        array_item_type=PropertyType.STRING,
                        required=False,
                    ),
                ],
            ),
        ],
        relationships=[
            Relationship(
                name="author",
                source_type="Post",
                target_type="User",
                cardinality=Cardinality.MANY_TO_ONE,
                required=True,
                description="The author of the post",
                inverse_name="posts",
            ),
        ],
    )


@pytest.fixture
def config() -> CodegenConfig:
    """Create a test configuration."""
    return CodegenConfig(
        output_dir=Path("test_output"),
        generators=["fastapi", "orm", "tests", "hooks"],
        dry_run=True,
        fastapi=FastAPIConfig(
            include_tracing=True,
            include_auth=True,
        ),
        orm=ORMConfig(
            use_async=True,
            include_timestamps=True,
        ),
        tests=TestConfig(
            include_async_tests=True,
            include_factories=True,
        ),
        hooks=HooksConfig(
            use_client_directive=True,
            include_optimistic_updates=True,
        ),
    )


# =============================================================================
# Base Generator Tests
# =============================================================================

class TestBaseGenerator:
    """Tests for the BaseGenerator class."""

    def test_to_snake_case(self):
        """Test snake_case conversion."""
        assert BaseGenerator.to_snake_case("UserProfile") == "user_profile"
        assert BaseGenerator.to_snake_case("HTTPResponse") == "http_response"
        assert BaseGenerator.to_snake_case("simpleTest") == "simple_test"
        assert BaseGenerator.to_snake_case("already_snake") == "already_snake"

    def test_to_pascal_case(self):
        """Test PascalCase conversion."""
        assert BaseGenerator.to_pascal_case("user_profile") == "UserProfile"
        assert BaseGenerator.to_pascal_case("http_response") == "HttpResponse"
        assert BaseGenerator.to_pascal_case("simple-test") == "SimpleTest"

    def test_to_camel_case(self):
        """Test camelCase conversion."""
        assert BaseGenerator.to_camel_case("user_profile") == "userProfile"
        assert BaseGenerator.to_camel_case("UserProfile") == "userProfile"

    def test_pluralize(self):
        """Test pluralization."""
        assert BaseGenerator.pluralize("user") == "users"
        assert BaseGenerator.pluralize("post") == "posts"
        assert BaseGenerator.pluralize("entity") == "entities"
        assert BaseGenerator.pluralize("status") == "statuses"
        assert BaseGenerator.pluralize("person") == "people"
        assert BaseGenerator.pluralize("child") == "children"

    def test_singularize(self):
        """Test singularization."""
        assert BaseGenerator.singularize("users") == "user"
        assert BaseGenerator.singularize("entities") == "entity"
        assert BaseGenerator.singularize("people") == "person"
        assert BaseGenerator.singularize("children") == "child"


# =============================================================================
# FastAPI Generator Tests
# =============================================================================

class TestFastAPIGenerator:
    """Tests for the FastAPI generator."""

    def test_generate_produces_files(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that generator produces expected files."""
        generator = FastAPIGenerator(config)
        files = generator.generate(sample_schema)

        # Check we have expected files
        file_paths = [str(f.path) for f in files]

        assert any("schemas" in p for p in file_paths)
        assert any("user" in p.lower() for p in file_paths)
        assert any("post" in p.lower() for p in file_paths)

    def test_generate_schemas_content(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that generated schemas have expected content."""
        generator = FastAPIGenerator(config)
        files = generator.generate(sample_schema)

        # Find schemas file
        schemas_file = next((f for f in files if "schemas" in str(f.path)), None)
        assert schemas_file is not None

        content = schemas_file.content

        # Check for expected classes
        assert "UserCreate" in content
        assert "UserUpdate" in content
        assert "UserResponse" in content
        assert "PostCreate" in content
        assert "PostUpdate" in content
        assert "PaginatedResponse" in content

    def test_generate_routes_content(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that generated routes have expected content."""
        generator = FastAPIGenerator(config)
        files = generator.generate(sample_schema)

        # Find user route file
        user_route = next((f for f in files if "user" in str(f.path).lower() and "routers" in str(f.path)), None)
        assert user_route is not None

        content = user_route.content

        # Check for CRUD endpoints
        assert "@router.post" in content
        assert "@router.get" in content
        assert "@router.put" in content
        assert "@router.delete" in content

        # Check for tracing decorators (based on config)
        assert "@traced" in content

    def test_generator_type(self, config: CodegenConfig):
        """Test generator type is correct."""
        generator = FastAPIGenerator(config)
        assert generator.generator_type == GeneratorType.FASTAPI


# =============================================================================
# ORM Generator Tests
# =============================================================================

class TestORMGenerator:
    """Tests for the SQLAlchemy ORM generator."""

    def test_generate_produces_files(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that generator produces expected files."""
        generator = ORMGenerator(config)
        files = generator.generate(sample_schema)

        file_paths = [str(f.path) for f in files]

        assert any("base" in p for p in file_paths)
        assert any("user" in p.lower() for p in file_paths)
        assert any("post" in p.lower() for p in file_paths)
        assert any("__init__" in p for p in file_paths)

    def test_generate_base_content(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that base model has expected content."""
        generator = ORMGenerator(config)
        files = generator.generate(sample_schema)

        base_file = next((f for f in files if "base" in str(f.path)), None)
        assert base_file is not None

        content = base_file.content

        assert "DeclarativeBase" in content
        assert "TimestampMixin" in content
        assert "UUIDMixin" in content
        assert "AsyncSession" in content  # Async support

    def test_generate_model_content(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that model files have expected content."""
        generator = ORMGenerator(config)
        files = generator.generate(sample_schema)

        user_model = next((f for f in files if "user" in str(f.path).lower() and str(f.path).endswith(".py")), None)
        assert user_model is not None

        content = user_model.content

        assert "class User" in content
        assert "mapped_column" in content
        assert "Mapped[" in content

    def test_generator_type(self, config: CodegenConfig):
        """Test generator type is correct."""
        generator = ORMGenerator(config)
        assert generator.generator_type == GeneratorType.ORM


# =============================================================================
# Test Generator Tests
# =============================================================================

class TestTestGenerator:
    """Tests for the pytest test generator."""

    def test_generate_produces_files(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that generator produces expected files."""
        generator = TestGenerator(config)
        files = generator.generate(sample_schema)

        file_paths = [str(f.path) for f in files]

        assert any("conftest" in p for p in file_paths)
        assert any("factories" in p for p in file_paths)
        assert any("test_user" in p.lower() for p in file_paths)
        assert any("test_post" in p.lower() for p in file_paths)

    def test_generate_conftest_content(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that conftest has expected content."""
        generator = TestGenerator(config)
        files = generator.generate(sample_schema)

        conftest = next((f for f in files if "conftest" in str(f.path)), None)
        assert conftest is not None

        content = conftest.content

        assert "@pytest.fixture" in content
        assert "db_session" in content
        assert "authenticated_client" in content
        assert "AsyncClient" in content

    def test_generate_factories_content(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that factories have expected content."""
        generator = TestGenerator(config)
        files = generator.generate(sample_schema)

        factories = next((f for f in files if "factories" in str(f.path)), None)
        assert factories is not None

        content = factories.content

        assert "UserFactory" in content
        assert "PostFactory" in content
        assert "factory.LazyAttribute" in content or "LazyAttribute" in content

    def test_generate_test_content(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that test files have expected content."""
        generator = TestGenerator(config)
        files = generator.generate(sample_schema)

        test_file = next((f for f in files if "test_user" in str(f.path).lower()), None)
        assert test_file is not None

        content = test_file.content

        assert "test_create_user" in content
        assert "test_list_users" in content
        assert "test_get_user" in content
        assert "test_update_user" in content
        assert "test_delete_user" in content
        assert "@pytest.mark.asyncio" in content

    def test_generator_type(self, config: CodegenConfig):
        """Test generator type is correct."""
        generator = TestGenerator(config)
        assert generator.generator_type == GeneratorType.TESTS


# =============================================================================
# Hooks Generator Tests
# =============================================================================

class TestHooksGenerator:
    """Tests for the React Query hooks generator."""

    def test_generate_produces_files(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that generator produces expected files."""
        generator = HooksGenerator(config)
        files = generator.generate(sample_schema)

        file_paths = [str(f.path) for f in files]

        assert any("types.ts" in p for p in file_paths)
        assert any("generated.ts" in p for p in file_paths)
        assert any("use-user" in p.lower() for p in file_paths)
        assert any("use-post" in p.lower() for p in file_paths)

    def test_generate_types_content(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that TypeScript types have expected content."""
        generator = HooksGenerator(config)
        files = generator.generate(sample_schema)

        types_file = next((f for f in files if "types.ts" in str(f.path)), None)
        assert types_file is not None

        content = types_file.content

        assert "interface User" in content
        assert "interface UserCreate" in content
        assert "interface UserUpdate" in content
        assert "interface Post" in content
        assert "PaginatedResponse" in content

    def test_generate_hooks_content(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that hooks have expected content."""
        generator = HooksGenerator(config)
        files = generator.generate(sample_schema)

        hook_file = next((f for f in files if "use-user" in str(f.path).lower()), None)
        assert hook_file is not None

        content = hook_file.content

        assert "'use client'" in content
        assert "useQuery" in content
        assert "useMutation" in content
        assert "useUsers" in content
        assert "useUser" in content
        assert "useCreateUser" in content
        assert "useUpdateUser" in content
        assert "useDeleteUser" in content
        assert "userKeys" in content

    def test_generate_api_client_content(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that API client has expected content."""
        generator = HooksGenerator(config)
        files = generator.generate(sample_schema)

        api_file = next((f for f in files if "generated.ts" in str(f.path)), None)
        assert api_file is not None

        content = api_file.content

        assert "getUsers" in content
        assert "getUser" in content
        assert "createUser" in content
        assert "updateUser" in content
        assert "deleteUser" in content
        assert "apiRequest" in content

    def test_generator_type(self, config: CodegenConfig):
        """Test generator type is correct."""
        generator = HooksGenerator(config)
        assert generator.generator_type == GeneratorType.HOOKS


# =============================================================================
# Engine Tests
# =============================================================================

class TestCodegenEngine:
    """Tests for the CodegenEngine."""

    def test_engine_initialization(self, config: CodegenConfig):
        """Test engine initializes correctly."""
        engine = CodegenEngine(config)

        assert len(engine.get_enabled_generators()) == 4
        assert "fastapi" in engine.get_enabled_generators()
        assert "orm" in engine.get_enabled_generators()
        assert "tests" in engine.get_enabled_generators()
        assert "hooks" in engine.get_enabled_generators()

    def test_list_generators(self, config: CodegenConfig):
        """Test listing available generators."""
        engine = CodegenEngine(config)
        generators = engine.list_generators()

        assert "fastapi" in generators
        assert "orm" in generators
        assert "tests" in generators
        assert "hooks" in generators

    def test_generate_all(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test generating with all generators."""
        engine = CodegenEngine(config)
        result = engine.generate(sample_schema)

        assert not result.has_errors()
        assert len(result.files) > 0

        # Check we have files from all generators
        generators_used = set(f.generator for f in result.files)
        assert GeneratorType.FASTAPI in generators_used
        assert GeneratorType.ORM in generators_used
        assert GeneratorType.TESTS in generators_used
        assert GeneratorType.HOOKS in generators_used

    def test_generate_specific_generators(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test generating with specific generators."""
        engine = CodegenEngine(config)
        result = engine.generate(sample_schema, generators=["fastapi", "orm"])

        assert not result.has_errors()

        generators_used = set(f.generator for f in result.files)
        assert GeneratorType.FASTAPI in generators_used
        assert GeneratorType.ORM in generators_used
        assert GeneratorType.TESTS not in generators_used
        assert GeneratorType.HOOKS not in generators_used

    def test_result_metadata(self, sample_schema: OntologySchema, config: CodegenConfig):
        """Test that result contains correct metadata."""
        engine = CodegenEngine(config)
        result = engine.generate(sample_schema)

        assert result.schema_name == "TestSchema"
        assert result.schema_version == "1.0.0"
        assert result.generated_at is not None
        assert isinstance(result.generated_at, datetime)


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunction:
    """Tests for the generate_code convenience function."""

    def test_generate_code_basic(self, sample_schema: OntologySchema):
        """Test basic code generation."""
        config = CodegenConfig(dry_run=True)
        result = generate_code(sample_schema, config=config)

        assert not result.has_errors()
        assert len(result.files) > 0

    def test_generate_code_with_generators(self, sample_schema: OntologySchema):
        """Test code generation with specific generators."""
        config = CodegenConfig(dry_run=True)
        result = generate_code(
            sample_schema,
            config=config,
            generators=["fastapi"],
        )

        assert not result.has_errors()
        generators_used = set(f.generator for f in result.files)
        assert GeneratorType.FASTAPI in generators_used
        assert len(generators_used) == 1
