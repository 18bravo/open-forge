# Local Development Setup

This guide explains how to set up a local development environment for Open Forge.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Setup](#quick-setup)
- [Detailed Setup](#detailed-setup)
- [IDE Configuration](#ide-configuration)
- [Development Workflow](#development-workflow)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Installation |
|----------|---------|--------------|
| Python | 3.11+ | `brew install python@3.11` |
| Node.js | 18+ | `brew install node@18` |
| Docker | 24.0+ | [Docker Desktop](https://www.docker.com/products/docker-desktop) |
| Docker Compose | 2.20+ | Included with Docker Desktop |
| Git | 2.40+ | `brew install git` |

### Optional Tools

| Tool | Purpose | Installation |
|------|---------|--------------|
| pyenv | Python version management | `brew install pyenv` |
| nvm | Node version management | `brew install nvm` |
| direnv | Environment management | `brew install direnv` |
| pre-commit | Git hooks | `pip install pre-commit` |

### Verify Installation

```bash
# Check versions
python3 --version  # Should be 3.11+
node --version     # Should be 18+
docker --version   # Should be 24+
docker compose version  # Should be 2.20+
```

---

## Quick Setup

For the impatient, here's the fastest path to a working environment:

```bash
# Clone repository
git clone https://github.com/18bravo/open-forge.git
cd open-forge

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start infrastructure
make infra-up

# Run tests
make test

# You're ready to develop!
```

---

## Detailed Setup

### 1. Clone Repository

```bash
git clone https://github.com/18bravo/open-forge.git
cd open-forge
```

### 2. Python Environment

#### Using venv (Recommended)

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Verify
which python  # Should point to .venv
```

#### Using pyenv

```bash
# Install Python 3.11
pyenv install 3.11.7

# Set local version
pyenv local 3.11.7

# Create venv
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 4. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
```

**Required configuration:**

```bash
# .env
ENVIRONMENT=development
DEBUG=true

# Database (using Docker defaults)
DB_HOST=localhost
DB_PORT=5432
DB_USER=foundry
DB_PASSWORD=foundry_dev
DB_NAME=foundry

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# MinIO
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123

# Iceberg
ICEBERG_CATALOG_URI=http://localhost:8181
ICEBERG_WAREHOUSE=s3://foundry-lake/warehouse

# LLM (required for agent development)
ANTHROPIC_API_KEY=your_api_key_here
DEFAULT_LLM_MODEL=claude-sonnet-4-20250514

# Observability
OTLP_ENDPOINT=http://localhost:4317
SERVICE_NAME=open-forge-dev
```

### 5. Start Infrastructure

```bash
# Start all infrastructure services
make infra-up

# Wait for services to be healthy
make infra-test
```

This starts:
- PostgreSQL with Apache AGE (port 5432)
- Redis (port 6379)
- MinIO (ports 9000, 9001)
- Iceberg REST catalog (port 8181)
- Jaeger (port 16686)
- Dagster (port 3000)

### 6. Initialize Database

```bash
# Run migrations
python -m alembic upgrade head

# (Optional) Load sample data
python scripts/load_sample_data.py
```

### 7. Verify Setup

```bash
# Run unit tests
make test-unit

# Run integration tests (requires infra)
make test-int

# Run linting
make lint

# Run type checking
make typecheck
```

---

## IDE Configuration

### VS Code

Install recommended extensions:

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "ms-python.mypy-type-checker",
    "redhat.vscode-yaml",
    "esbenp.prettier-vscode"
  ]
}
```

Configure settings:

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.autoImportCompletions": true,

  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },

  "ruff.lint.args": ["--config", "pyproject.toml"],

  "yaml.schemas": {
    "https://json.schemastore.org/github-workflow.json": ".github/workflows/*.yml"
  }
}
```

### PyCharm

1. Open project in PyCharm
2. Configure interpreter:
   - **Settings > Project > Python Interpreter**
   - Select `.venv/bin/python`

3. Configure Ruff:
   - **Settings > Tools > File Watchers**
   - Add Ruff watcher

4. Enable pytest:
   - **Settings > Tools > Python Integrated Tools**
   - Set default test runner to pytest

---

## Development Workflow

### Running the API Server

```bash
# Start API server with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or use the makefile
make run-api
```

Access:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- GraphQL: http://localhost:8000/graphql

### Running Dagster

```bash
# Start Dagster UI
dagster dev -f packages/pipelines/src/pipelines/definitions.py

# Or use Docker
docker compose -f infrastructure/docker/docker-compose.yml up dagster-webserver
```

Access: http://localhost:3000

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests only (requires infra)
make test-int

# Specific package
pytest packages/core/tests -v

# Specific test file
pytest packages/core/tests/test_config.py -v

# With coverage
pytest --cov=packages --cov-report=html
```

### Code Quality

```bash
# Lint (check only)
make lint

# Lint (fix issues)
ruff check --fix packages/

# Format code
make format

# Type checking
make typecheck
```

---

## Common Tasks

### Adding a New Package

```bash
# Create package structure
mkdir -p packages/my_package/src/my_package
mkdir -p packages/my_package/tests

# Create __init__.py
touch packages/my_package/src/my_package/__init__.py

# Create pyproject.toml
cat > packages/my_package/pyproject.toml << EOF
[project]
name = "my_package"
version = "0.1.0"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0"]
EOF
```

### Adding a New Agent

```python
# packages/agents/src/agents/my_cluster/my_agent.py

from agent_framework.base_agent import BaseOpenForgeAgent
from langgraph.graph import StateGraph

class MyAgent(BaseOpenForgeAgent):
    @property
    def name(self) -> str:
        return "my_agent"

    @property
    def description(self) -> str:
        return "Description of what this agent does"

    @property
    def required_inputs(self) -> list[str]:
        return ["input_field"]

    @property
    def output_keys(self) -> list[str]:
        return ["output_field"]

    def get_system_prompt(self) -> str:
        return "You are a helpful agent..."

    def build_graph(self) -> StateGraph:
        # Build LangGraph workflow
        ...

    def get_tools(self) -> list:
        return []
```

### Adding a New API Endpoint

```python
# packages/api/src/api/routers/my_resource.py

from fastapi import APIRouter, HTTPException
from api.schemas.my_resource import MyResourceCreate, MyResourceResponse
from api.dependencies import DbSession, CurrentUser

router = APIRouter(prefix="/my-resources", tags=["My Resources"])

@router.post("", response_model=MyResourceResponse)
async def create_my_resource(
    resource: MyResourceCreate,
    db: DbSession,
    user: CurrentUser,
) -> MyResourceResponse:
    """Create a new resource."""
    # Implementation
    ...
```

Register in main app:

```python
# packages/api/src/api/main.py
from api.routers import my_resource

app.include_router(my_resource.router, prefix="/api/v1")
```

### Adding a New Database Migration

```bash
# Generate migration
alembic revision --autogenerate -m "Add my_table"

# Review generated migration
cat migrations/versions/xxx_add_my_table.py

# Apply migration
alembic upgrade head

# Rollback (if needed)
alembic downgrade -1
```

### Adding a New Dagster Asset

```python
# packages/pipelines/src/pipelines/assets/my_asset.py

from dagster import asset, AssetExecutionContext
import polars as pl

@asset(
    description="My new data asset",
    group_name="my_group",
    compute_kind="polars"
)
def my_asset(context: AssetExecutionContext) -> pl.DataFrame:
    """Process and return data."""
    context.log.info("Processing my asset")

    df = pl.DataFrame({"col": [1, 2, 3]})

    context.add_output_metadata({
        "row_count": len(df)
    })

    return df
```

---

## Troubleshooting

### Virtual Environment Issues

```bash
# Recreate venv
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Docker Issues

```bash
# Reset all containers and volumes
make infra-down
docker system prune -a --volumes
make infra-up
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker compose -f infrastructure/docker/docker-compose.yml ps postgres

# Check connection
docker compose -f infrastructure/docker/docker-compose.yml exec postgres \
  pg_isready -U foundry

# View logs
docker compose -f infrastructure/docker/docker-compose.yml logs postgres
```

### Import Errors

```bash
# Reinstall in development mode
pip install -e ".[dev]"

# Verify installation
pip list | grep open-forge
```

### Port Conflicts

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Pre-commit Hook Failures

```bash
# Run hooks manually to see errors
pre-commit run --all-files

# Update hooks
pre-commit autoupdate

# Skip hooks temporarily (use sparingly)
git commit --no-verify
```

---

## Related Documentation

- [Architecture Overview](./architecture.md)
- [Testing Guide](./testing.md)
- [Contributing Guide](./contributing.md)
- [Code Style Guide](./code-style.md)
