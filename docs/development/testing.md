# Testing Guide

This guide covers testing practices and strategies for Open Forge.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Types](#test-types)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Testing Agents](#testing-agents)
- [Testing Pipelines](#testing-pipelines)
- [CI/CD Integration](#cicd-integration)
- [Test Coverage](#test-coverage)

---

## Testing Philosophy

### Testing Pyramid

```
                    /\
                   /  \
                  / E2E \         <- Few, slow, high confidence
                 /------\
                /        \
               / Integration\     <- Medium, verify connections
              /--------------\
             /                \
            /    Unit Tests    \  <- Many, fast, isolated
           /--------------------\
```

| Level | Count | Speed | Scope |
|-------|-------|-------|-------|
| Unit | 100s | Fast (ms) | Single function/class |
| Integration | 10s | Medium (s) | Component interaction |
| E2E | Few | Slow (min) | Full workflow |

### Key Principles

1. **Test behavior, not implementation**
2. **Isolate units under test**
3. **Use meaningful assertions**
4. **Keep tests fast**
5. **Make tests deterministic**

---

## Test Types

### Unit Tests

Test individual functions and classes in isolation.

**Location:** `packages/*/tests/unit/`

```python
# packages/core/tests/unit/test_config.py

import pytest
from core.config import Settings

class TestSettings:
    def test_default_values(self):
        settings = Settings(ANTHROPIC_API_KEY="test")
        assert settings.environment == "development"
        assert settings.debug is False

    def test_environment_override(self):
        settings = Settings(
            ANTHROPIC_API_KEY="test",
            ENVIRONMENT="production"
        )
        assert settings.environment == "production"

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            Settings()  # Missing ANTHROPIC_API_KEY
```

### Integration Tests

Test interaction between components.

**Location:** `packages/*/tests/integration/`

```python
# tests/integration/test_core/test_database_connection.py

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.integration
class TestDatabaseConnection:
    @pytest.mark.asyncio
    async def test_connection(self, db_session: AsyncSession):
        result = await db_session.execute("SELECT 1")
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_create_engagement(self, db_session: AsyncSession):
        from core.models import Engagement

        engagement = Engagement(
            name="Test",
            objective="Test objective"
        )
        db_session.add(engagement)
        await db_session.commit()

        assert engagement.id is not None
```

### End-to-End Tests

Test complete workflows from API to database.

**Location:** `tests/e2e/`

```python
# tests/e2e/test_engagement_lifecycle.py

import pytest
from httpx import AsyncClient

@pytest.mark.e2e
class TestEngagementLifecycle:
    @pytest.mark.asyncio
    async def test_full_engagement_flow(self, client: AsyncClient):
        # Create engagement
        response = await client.post("/api/v1/engagements", json={
            "name": "E2E Test",
            "objective": "Test the full flow"
        })
        assert response.status_code == 201
        engagement_id = response.json()["id"]

        # Start discovery
        response = await client.post(
            f"/api/v1/engagements/{engagement_id}/start"
        )
        assert response.status_code == 200

        # Wait for discovery to complete
        import asyncio
        for _ in range(60):  # Max 60 seconds
            response = await client.get(
                f"/api/v1/engagements/{engagement_id}"
            )
            if response.json()["status"] == "discovery_complete":
                break
            await asyncio.sleep(1)

        # Verify discovery outputs
        assert response.json()["status"] == "discovery_complete"
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests
make test-int

# Run e2e tests
make e2e-test
```

### Pytest Options

```bash
# Run specific package
pytest packages/core/tests -v

# Run specific test file
pytest packages/core/tests/test_config.py -v

# Run specific test
pytest packages/core/tests/test_config.py::TestSettings::test_default_values -v

# Run tests matching pattern
pytest -k "test_database" -v

# Run with markers
pytest -m "integration" -v
pytest -m "not slow" -v

# Parallel execution
pytest -n auto

# Stop on first failure
pytest -x

# Show local variables in tracebacks
pytest -l

# Drop into debugger on failure
pytest --pdb
```

### With Coverage

```bash
# Generate coverage report
pytest --cov=packages --cov-report=html

# View report
open htmlcov/index.html

# Fail if coverage below threshold
pytest --cov=packages --cov-fail-under=80
```

---

## Writing Tests

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

class TestMyComponent:
    """Test suite for MyComponent."""

    # Fixtures for test setup
    @pytest.fixture
    def my_component(self):
        """Create a fresh component for each test."""
        return MyComponent()

    @pytest.fixture
    def mock_dependency(self):
        """Mock external dependency."""
        return Mock(spec=Dependency)

    # Test methods
    def test_basic_functionality(self, my_component):
        """Test that basic operation works."""
        result = my_component.do_something()
        assert result == expected_value

    def test_with_mock(self, my_component, mock_dependency):
        """Test with mocked dependency."""
        my_component.dependency = mock_dependency
        mock_dependency.fetch.return_value = {"data": "test"}

        result = my_component.process()

        mock_dependency.fetch.assert_called_once()
        assert result["processed_data"] == "test"

    @pytest.mark.asyncio
    async def test_async_operation(self, my_component):
        """Test async functionality."""
        result = await my_component.async_do_something()
        assert result is not None

    @pytest.mark.parametrize("input,expected", [
        ("a", 1),
        ("b", 2),
        ("c", 3),
    ])
    def test_parametrized(self, my_component, input, expected):
        """Test with multiple inputs."""
        result = my_component.transform(input)
        assert result == expected
```

### Fixtures

#### Shared Fixtures

```python
# conftest.py

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """Create database engine for test session."""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost/test",
        echo=False
    )
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    """Create fresh database session for each test."""
    async with AsyncSession(db_engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
def api_client():
    """Create test API client."""
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)

@pytest.fixture
async def async_api_client():
    """Create async test API client."""
    from httpx import AsyncClient
    from api.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

#### Factory Fixtures

```python
# conftest.py

@pytest.fixture
def engagement_factory(db_session):
    """Factory for creating test engagements."""
    async def _create_engagement(**kwargs):
        defaults = {
            "name": "Test Engagement",
            "objective": "Test objective",
            "status": "draft"
        }
        defaults.update(kwargs)

        engagement = Engagement(**defaults)
        db_session.add(engagement)
        await db_session.commit()
        return engagement

    return _create_engagement
```

### Mocking

#### Mock External Services

```python
import pytest
from unittest.mock import patch, AsyncMock

class TestAgentWithLLM:
    @pytest.mark.asyncio
    async def test_agent_execution(self):
        mock_response = AsyncMock()
        mock_response.content = "Generated response"

        with patch("langchain_anthropic.ChatAnthropic") as mock_llm:
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)

            agent = MyAgent(llm=mock_llm.return_value)
            result = await agent.execute(input_data)

            assert result.success
            mock_llm.return_value.ainvoke.assert_called_once()
```

#### Mock HTTP Requests

```python
import pytest
import httpx
from pytest_httpx import HTTPXMock

class TestAPIConnector:
    @pytest.mark.asyncio
    async def test_fetch_data(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="https://api.example.com/data",
            json={"key": "value"}
        )

        connector = APIConnector("https://api.example.com")
        result = await connector.fetch("/data")

        assert result == {"key": "value"}
```

### Assertions

```python
# Basic assertions
assert result == expected
assert result is not None
assert len(items) == 5
assert "key" in dictionary
assert result > 0

# Exception assertions
with pytest.raises(ValueError) as exc_info:
    function_that_raises()
assert "expected message" in str(exc_info.value)

# Approximate assertions
assert result == pytest.approx(3.14, rel=0.01)

# Collection assertions
assert set(result) == {"a", "b", "c"}
assert all(item > 0 for item in result)
```

---

## Testing Agents

### Mock LLM Responses

```python
# tests/unit/agents/test_ontology_designer.py

import pytest
from unittest.mock import AsyncMock, Mock
from agents.data_architect.ontology_designer_agent import OntologyDesignerAgent

class TestOntologyDesignerAgent:
    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.ainvoke = AsyncMock()
        return llm

    @pytest.fixture
    def agent(self, mock_llm):
        return OntologyDesignerAgent(llm=mock_llm)

    @pytest.mark.asyncio
    async def test_generate_ontology(self, agent, mock_llm):
        # Setup mock response
        mock_llm.ainvoke.return_value.content = """
        classes:
          Customer:
            attributes:
              name:
                range: string
        """

        # Execute
        result = await agent.execute({
            "requirements": "Need customer data model",
            "context": {}
        })

        # Verify
        assert result.success
        assert "Customer" in result.outputs["ontology"]
```

### Test Agent State Transitions

```python
class TestAgentWorkflow:
    @pytest.mark.asyncio
    async def test_state_transitions(self, agent):
        # Initial state
        state = agent.create_initial_state({
            "input": "test input"
        })
        assert state["current_step"] == "start"

        # After first node
        state = await agent.graph.ainvoke(state)
        assert state["current_step"] == "process"

        # After completion
        assert state.get("outputs") is not None
```

### Agent Framework Testing

```python
from agent_framework.testing import MockLLM, AgentTestHarness

class TestWithHarness:
    @pytest.fixture
    def harness(self):
        return AgentTestHarness(
            agent_class=MyAgent,
            mock_responses=[
                {"step": "analyze", "response": "Analysis result"},
                {"step": "generate", "response": "Generated output"}
            ]
        )

    @pytest.mark.asyncio
    async def test_agent_flow(self, harness):
        result = await harness.run({
            "input_field": "test input"
        })

        assert harness.steps_executed == ["analyze", "generate"]
        assert result.success
```

---

## Testing Pipelines

### Test Dagster Assets

```python
# tests/unit/pipelines/test_assets.py

import pytest
import polars as pl
from dagster import build_asset_context

from pipelines.assets.ingestion import raw_customers

class TestIngestionAssets:
    def test_raw_customers_asset(self):
        # Create test context
        context = build_asset_context()

        # Mock database resource
        mock_db = Mock()
        mock_db.query.return_value = pl.DataFrame({
            "customer_id": ["1", "2"],
            "email": ["a@b.com", "c@d.com"]
        })

        # Execute asset
        result = raw_customers(context, database=mock_db)

        # Verify
        assert len(result) == 2
        assert "customer_id" in result.columns
```

### Test Asset Materialization

```python
from dagster import materialize

class TestAssetMaterialization:
    def test_materialize_assets(self):
        result = materialize(
            [raw_customers, clean_customers],
            resources={
                "database": mock_database,
                "iceberg": mock_iceberg
            }
        )

        assert result.success
        assert result.output_for_node("raw_customers") is not None
```

### Test Jobs

```python
from dagster import execute_job, reconstructable

class TestJobs:
    def test_ingestion_job(self):
        result = execute_job(
            reconstructable(ingestion_job),
            run_config={
                "resources": {
                    "database": {"config": {"host": "localhost"}}
                }
            }
        )

        assert result.success
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml

name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run unit tests
        run: |
          pytest packages/*/tests/unit -v --cov=packages --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run integration tests
        run: pytest tests/integration -v -m integration
        env:
          DB_HOST: localhost
          REDIS_HOST: localhost
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml

repos:
  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: pytest packages/*/tests/unit -x -q
        language: system
        types: [python]
        pass_filenames: false
```

---

## Test Coverage

### Coverage Configuration

```toml
# pyproject.toml

[tool.coverage.run]
source = ["packages"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 80
```

### Generating Reports

```bash
# Run with coverage
pytest --cov=packages --cov-report=html --cov-report=xml

# View HTML report
open htmlcov/index.html

# Check coverage threshold
pytest --cov=packages --cov-fail-under=80
```

### Coverage Targets

| Package | Target | Current |
|---------|--------|---------|
| core | 90% | - |
| api | 85% | - |
| agents | 80% | - |
| pipelines | 75% | - |
| ontology | 85% | - |

---

## Related Documentation

- [Contributing Guide](./contributing.md)
- [Local Setup Guide](./local-setup.md)
- [Code Style Guide](./code-style.md)
- [Architecture Overview](./architecture.md)
