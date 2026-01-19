"""
Configuration for code generation.
Defines settings for each generator type.
"""
from typing import Optional, List
from pathlib import Path
from pydantic import BaseModel, Field


class FastAPIConfig(BaseModel):
    """Configuration for FastAPI route generation."""
    router_prefix: str = Field(default="/api/v1", description="Base router prefix")
    include_tracing: bool = Field(default=True, description="Include OpenTelemetry tracing")
    include_auth: bool = Field(default=True, description="Include authentication dependencies")
    include_pagination: bool = Field(default=True, description="Include pagination for list endpoints")
    default_page_size: int = Field(default=20, description="Default pagination page size")
    max_page_size: int = Field(default=100, description="Maximum pagination page size")
    generate_schemas: bool = Field(default=True, description="Generate Pydantic request/response schemas")
    schema_prefix: str = Field(default="", description="Prefix for schema class names")
    include_streaming: bool = Field(default=False, description="Include SSE streaming endpoints")


class ORMConfig(BaseModel):
    """Configuration for SQLAlchemy ORM generation."""
    schema_name: str = Field(default="public", description="Database schema name")
    table_prefix: str = Field(default="", description="Prefix for table names")
    include_timestamps: bool = Field(default=True, description="Include created_at/updated_at columns")
    include_soft_delete: bool = Field(default=False, description="Include soft delete support")
    use_async: bool = Field(default=True, description="Generate async-compatible models")
    include_relationships: bool = Field(default=True, description="Include SQLAlchemy relationships")
    generate_alembic: bool = Field(default=False, description="Generate Alembic migration")
    base_class: str = Field(default="Base", description="SQLAlchemy declarative base class name")


class TestConfig(BaseModel):
    """Configuration for test generation."""
    test_framework: str = Field(default="pytest", description="Test framework to use")
    include_factories: bool = Field(default=True, description="Include factory patterns for test data")
    include_fixtures: bool = Field(default=True, description="Include pytest fixtures")
    include_async_tests: bool = Field(default=True, description="Include async test support")
    coverage_target: float = Field(default=0.8, description="Target code coverage")
    mock_external_services: bool = Field(default=True, description="Mock external service calls")
    database_strategy: str = Field(
        default="transaction",
        description="Database isolation strategy: transaction, truncate, recreate"
    )


class HooksConfig(BaseModel):
    """Configuration for React Query hooks generation."""
    use_client_directive: bool = Field(default=True, description="Include 'use client' directive")
    api_import_path: str = Field(default="@/lib/api", description="Import path for API functions")
    include_optimistic_updates: bool = Field(default=True, description="Include optimistic update handling")
    include_error_handling: bool = Field(default=True, description="Include error handling")
    stale_time: Optional[int] = Field(default=None, description="Default stale time in ms")
    cache_time: Optional[int] = Field(default=None, description="Default cache time in ms")
    retry_count: int = Field(default=3, description="Default retry count for failed queries")


class CodegenConfig(BaseModel):
    """Main configuration for code generation."""
    output_dir: Path = Field(default=Path("generated"), description="Output directory")
    generators: List[str] = Field(
        default=["fastapi", "orm", "tests", "hooks"],
        description="List of generators to run"
    )
    clean_output: bool = Field(default=False, description="Clean output directory before generation")
    dry_run: bool = Field(default=False, description="Preview generation without writing files")

    # Generator-specific configs
    fastapi: FastAPIConfig = Field(default_factory=FastAPIConfig)
    orm: ORMConfig = Field(default_factory=ORMConfig)
    tests: TestConfig = Field(default_factory=TestConfig)
    hooks: HooksConfig = Field(default_factory=HooksConfig)

    def get_enabled_generators(self) -> List[str]:
        """Get list of enabled generators."""
        return self.generators

    def is_generator_enabled(self, generator: str) -> bool:
        """Check if a generator is enabled."""
        return generator.lower() in [g.lower() for g in self.generators]
