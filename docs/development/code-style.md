# Code Style Guide

This guide documents the coding standards and style conventions for Open Forge.

## Table of Contents

- [Python Style](#python-style)
- [TypeScript Style](#typescript-style)
- [Documentation Style](#documentation-style)
- [Git Conventions](#git-conventions)
- [Tooling Configuration](#tooling-configuration)

---

## Python Style

### General Principles

1. **Readability counts** - Code is read more often than written
2. **Explicit is better than implicit** - Be clear about intentions
3. **Simple is better than complex** - Avoid unnecessary complexity
4. **Consistency matters** - Follow established patterns

### Formatting

We use **Ruff** for formatting and linting:

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]  # Let formatter handle line length
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `ontology_compiler.py` |
| Classes | PascalCase | `OntologyCompiler` |
| Functions | snake_case | `compile_schema` |
| Variables | snake_case | `schema_name` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Type Variables | PascalCase with T | `InputT`, `OutputT` |

### Type Hints

**Always use type hints** for function signatures:

```python
# Good
def process_engagement(
    engagement_id: str,
    options: dict[str, Any] | None = None
) -> Engagement:
    ...

# Bad
def process_engagement(engagement_id, options=None):
    ...
```

Use typing imports for complex types:

```python
from typing import Any, Optional, TypeVar, Generic
from collections.abc import Sequence, Mapping, Iterator

# Modern syntax (Python 3.10+)
def get_items() -> list[str]:
    ...

def get_mapping() -> dict[str, int]:
    ...

def optional_value() -> str | None:
    ...
```

### Imports

Order imports using isort (handled by Ruff):

```python
# Standard library
import json
from datetime import datetime
from pathlib import Path

# Third-party
import httpx
import polars as pl
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Local imports
from core.config import settings
from core.database import get_session
```

### Classes

```python
class OntologyCompiler:
    """Compiles LinkML schemas to multiple output formats.

    This class takes LinkML schema definitions and generates
    SQL, GraphQL, Pydantic, and TypeScript outputs.

    Attributes:
        config: Compiler configuration options.
        output_dir: Directory for generated files.

    Example:
        >>> compiler = OntologyCompiler()
        >>> result = compiler.compile("schema.yaml")
        >>> print(result.get_output(OutputFormat.SQL))
    """

    def __init__(
        self,
        config: GeneratorConfig | None = None,
        output_dir: Path | None = None
    ) -> None:
        """Initialize the compiler.

        Args:
            config: Optional generator configuration.
            output_dir: Optional output directory path.
        """
        self.config = config or GeneratorConfig()
        self.output_dir = output_dir
        self._generators: dict[str, Generator] = {}

    def compile(
        self,
        schema: str | Path,
        formats: list[OutputFormat] | None = None
    ) -> CompilationResult:
        """Compile a schema to specified formats.

        Args:
            schema: Path to schema file or schema string.
            formats: Output formats to generate. Defaults to all.

        Returns:
            CompilationResult containing generated outputs.

        Raises:
            SchemaValidationError: If schema is invalid.
            CompilationError: If compilation fails.
        """
        ...
```

### Functions

```python
async def fetch_engagement(
    engagement_id: str,
    *,  # Force keyword arguments
    include_tasks: bool = False,
    include_approvals: bool = False,
) -> Engagement:
    """Fetch an engagement by ID.

    Args:
        engagement_id: The unique engagement identifier.
        include_tasks: Whether to include related tasks.
        include_approvals: Whether to include pending approvals.

    Returns:
        The engagement object with requested relations.

    Raises:
        NotFoundError: If engagement doesn't exist.
        DatabaseError: If database query fails.
    """
    ...
```

### Error Handling

```python
# Custom exceptions
class OpenForgeError(Exception):
    """Base exception for Open Forge."""
    pass

class NotFoundError(OpenForgeError):
    """Resource not found."""
    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} '{resource_id}' not found")

# Usage
async def get_engagement(engagement_id: str) -> Engagement:
    engagement = await db.get(Engagement, engagement_id)
    if not engagement:
        raise NotFoundError("engagement", engagement_id)
    return engagement

# Error handling
try:
    engagement = await get_engagement(engagement_id)
except NotFoundError:
    logger.warning(f"Engagement not found: {engagement_id}")
    raise HTTPException(status_code=404, detail="Engagement not found")
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Async Code

```python
# Prefer async for I/O operations
async def process_data(items: list[str]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks = [fetch_item(client, item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle results
    return [r for r in results if not isinstance(r, Exception)]

# Context managers for resources
async with get_session() as session:
    async with session.begin():
        session.add(entity)
```

### Data Classes and Pydantic

```python
from pydantic import BaseModel, Field, field_validator

class EngagementCreate(BaseModel):
    """Schema for creating an engagement."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Engagement name"
    )
    objective: str = Field(
        min_length=1,
        description="Main objective"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Engagement priority"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v.strip() != v:
            raise ValueError("Name cannot have leading/trailing whitespace")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Customer Analytics",
                "objective": "Build analytics dashboard"
            }
        }
    }
```

---

## TypeScript Style

### Formatting

We use **Prettier** and **ESLint**:

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

### Type Definitions

```typescript
// Always define interfaces for props
interface EngagementCardProps {
  engagement: Engagement;
  onUpdate: (engagement: Engagement) => void;
  isLoading?: boolean;
}

// Use type for unions/intersections
type EngagementStatus =
  | 'draft'
  | 'in_progress'
  | 'completed'
  | 'failed';

// Avoid `any` - use `unknown` if type is uncertain
function processData(data: unknown): ProcessedData {
  if (isValidData(data)) {
    return transform(data);
  }
  throw new Error('Invalid data');
}
```

### React Components

```typescript
// Functional components with explicit types
const EngagementCard: React.FC<EngagementCardProps> = ({
  engagement,
  onUpdate,
  isLoading = false,
}) => {
  const [isEditing, setIsEditing] = useState(false);

  const handleSave = useCallback(async () => {
    // Implementation
  }, [engagement.id]);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  return (
    <Card>
      <CardHeader>
        <h3>{engagement.name}</h3>
      </CardHeader>
      <CardContent>
        {/* Content */}
      </CardContent>
    </Card>
  );
};

export default EngagementCard;
```

### Hooks

```typescript
// Custom hooks with explicit return types
function useEngagement(id: string): {
  engagement: Engagement | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
} {
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchEngagement(id);
      setEngagement(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Unknown error'));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { engagement, isLoading, error, refetch };
}
```

---

## Documentation Style

### Docstrings

Use Google-style docstrings:

```python
def compile_schema(
    schema: str,
    formats: list[OutputFormat],
    strict: bool = True
) -> CompilationResult:
    """Compile a LinkML schema to multiple output formats.

    This function takes a LinkML schema definition and generates
    code in the specified output formats. It validates the schema
    first and reports any errors.

    Args:
        schema: The LinkML schema as a YAML string or file path.
        formats: List of output formats to generate.
        strict: Whether to fail on warnings. Defaults to True.

    Returns:
        A CompilationResult object containing:
            - outputs: Dict mapping format to generated code
            - errors: List of compilation errors
            - warnings: List of compilation warnings

    Raises:
        SchemaValidationError: If the schema is invalid.
        IOError: If the schema file cannot be read.

    Example:
        >>> result = compile_schema(
        ...     "my_schema.yaml",
        ...     [OutputFormat.SQL, OutputFormat.PYDANTIC]
        ... )
        >>> print(result.outputs[OutputFormat.SQL])
        CREATE TABLE ...

    Note:
        For large schemas, consider using the async version
        `compile_schema_async` for better performance.
    """
```

### Comments

```python
# Good: Explain WHY, not WHAT
# Cache the result to avoid repeated LLM calls for the same input
cached_result = cache.get(cache_key)

# Bad: Restates the code
# Get the cached result
cached_result = cache.get(cache_key)

# Good: Complex logic explanation
# We use a two-phase commit here because the database and
# message queue must be updated atomically. If either fails,
# we rollback both to maintain consistency.
async with db.begin():
    ...
```

### README Files

Each package should have a README:

```markdown
# Package Name

Brief description of what this package does.

## Installation

```bash
pip install package-name
```

## Usage

```python
from package import main_function

result = main_function()
```

## API Reference

### `main_function(arg1, arg2) -> Result`

Description of the function.

**Arguments:**
- `arg1` (str): Description
- `arg2` (int): Description

**Returns:**
- `Result`: Description

## Development

```bash
# Run tests
pytest tests/
```
```

---

## Git Conventions

### Commit Messages

Format:
```
<type>(<scope>): <short description>

<optional body>

<optional footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(agents): add ontology designer agent

Implements the ontology designer agent that generates LinkML
schemas from requirements documents.

- Uses Claude for schema generation
- Validates against existing data sources
- Supports incremental refinement

Closes #123
```

```
fix(api): handle null email in user creation

Previously, creating a user with null email would cause a 500 error.
Now we return a proper 422 validation error.
```

### Branch Names

```
feature/add-stakeholder-agent
fix/engagement-status-update
docs/api-authentication
refactor/database-connection-pool
```

### Pull Requests

Title format:
```
[TYPE] Short description

Examples:
[Feature] Add stakeholder analysis agent
[Fix] Correct engagement status transitions
[Docs] Update API authentication guide
```

---

## Tooling Configuration

### Ruff (Python)

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "W",   # pycodestyle warnings
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (formatter handles)
]

[tool.ruff.isort]
known-first-party = ["core", "api", "agents", "ontology", "pipelines"]

[tool.ruff.per-file-ignores]
"tests/*" = ["S101"]  # Allow assert in tests
```

### Mypy (Type Checking)

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
disallow_untyped_defs = true
warn_return_any = true
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### pytest

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["packages/*/tests", "tests"]
filterwarnings = [
    "ignore::DeprecationWarning",
]
markers = [
    "integration: mark test as integration test",
    "e2e: mark test as end-to-end test",
    "slow: mark test as slow",
]
```

### Pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.0]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### VS Code Settings

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",

  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },

  "[typescript][typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },

  "editor.rulers": [100],
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true
}
```

---

## Related Documentation

- [Contributing Guide](./contributing.md)
- [Testing Guide](./testing.md)
- [Local Setup Guide](./local-setup.md)
