"""
Open Forge Code Generation Package.

This package provides code generation capabilities from ontology schemas,
producing FastAPI routes, SQLAlchemy ORM models, pytest tests, and React Query hooks.
"""
from codegen.engine import CodegenEngine, generate_code
from codegen.config import (
    CodegenConfig,
    FastAPIConfig,
    ORMConfig,
    TestConfig,
    HooksConfig,
)
from codegen.models import (
    GeneratorType,
    OutputFile,
    GenerationResult,
    EntityContext,
    TemplateContext,
)
from codegen.generators.base import BaseGenerator
from codegen.generators.fastapi_generator import FastAPIGenerator
from codegen.generators.orm_generator import ORMGenerator
from codegen.generators.test_generator import TestGenerator
from codegen.generators.hooks_generator import HooksGenerator

__version__ = "0.1.0"

__all__ = [
    # Engine
    "CodegenEngine",
    "generate_code",
    # Configuration
    "CodegenConfig",
    "FastAPIConfig",
    "ORMConfig",
    "TestConfig",
    "HooksConfig",
    # Models
    "GeneratorType",
    "OutputFile",
    "GenerationResult",
    "EntityContext",
    "TemplateContext",
    # Generators
    "BaseGenerator",
    "FastAPIGenerator",
    "ORMGenerator",
    "TestGenerator",
    "HooksGenerator",
]
