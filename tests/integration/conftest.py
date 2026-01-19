"""
Shared pytest fixtures for Open Forge integration tests.

Provides fixtures for:
- PostgreSQL with Apache AGE (graph database)
- Redis for messaging and caching
- MinIO for S3-compatible storage
- Iceberg catalog
- Mock LLM services
- Test database sessions
"""
import os
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import json

import pytest
import pytest_asyncio
from pydantic import BaseModel


# =============================================================================
# Environment Configuration
# =============================================================================

def get_test_env() -> Dict[str, str]:
    """Get environment variables for testing."""
    return {
        # Database configuration
        "ENVIRONMENT": "test",
        "DATABASE__HOST": os.environ.get("TEST_DB_HOST", "localhost"),
        "DATABASE__PORT": os.environ.get("TEST_DB_PORT", "5432"),
        "DATABASE__NAME": os.environ.get("TEST_DB_NAME", "openforge_test"),
        "DATABASE__USER": os.environ.get("TEST_DB_USER", "foundry"),
        "DATABASE__PASSWORD": os.environ.get("TEST_DB_PASSWORD", "foundry_dev"),
        "DATABASE__POOL_SIZE": "5",
        # Redis configuration
        "REDIS__HOST": os.environ.get("TEST_REDIS_HOST", "localhost"),
        "REDIS__PORT": os.environ.get("TEST_REDIS_PORT", "6379"),
        # Iceberg configuration
        "ICEBERG__REST_URI": os.environ.get("TEST_ICEBERG_URI", "http://localhost:8181"),
        "ICEBERG__WAREHOUSE": "s3://foundry-lake/warehouse",
        "ICEBERG__S3_ENDPOINT": os.environ.get("TEST_S3_ENDPOINT", "http://localhost:9000"),
        "ICEBERG__S3_ACCESS_KEY": os.environ.get("TEST_S3_ACCESS_KEY", "minio"),
        "ICEBERG__S3_SECRET_KEY": os.environ.get("TEST_S3_SECRET_KEY", "minio123"),
        # LLM configuration (mock by default)
        "LLM__PROVIDER": "mock",
        "LLM__MODEL": "test-model",
        "LLM__API_KEY": "test-api-key",
        # Observability
        "OBSERVABILITY__SERVICE_NAME": "openforge-integration-tests",
        "OBSERVABILITY__OTLP_ENDPOINT": "http://localhost:4317",
        "DEBUG": "true",
    }


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    env_vars = get_test_env()
    original_env = {k: os.environ.get(k) for k in env_vars}

    # Set test environment
    os.environ.update(env_vars)

    yield env_vars

    # Restore original environment
    for k, v in original_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


# =============================================================================
# Event Loop Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Infrastructure Availability Checks
# =============================================================================

def is_postgres_available() -> bool:
    """Check if PostgreSQL is available for testing."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ.get("TEST_DB_HOST", "localhost"),
            port=int(os.environ.get("TEST_DB_PORT", "5432")),
            database=os.environ.get("TEST_DB_NAME", "openforge_test"),
            user=os.environ.get("TEST_DB_USER", "foundry"),
            password=os.environ.get("TEST_DB_PASSWORD", "foundry_dev"),
            connect_timeout=5
        )
        conn.close()
        return True
    except Exception:
        return False


def is_redis_available() -> bool:
    """Check if Redis is available for testing."""
    try:
        import redis
        r = redis.Redis(
            host=os.environ.get("TEST_REDIS_HOST", "localhost"),
            port=int(os.environ.get("TEST_REDIS_PORT", "6379")),
            socket_connect_timeout=5
        )
        r.ping()
        return True
    except Exception:
        return False


def is_minio_available() -> bool:
    """Check if MinIO is available for testing."""
    try:
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client(
            "s3",
            endpoint_url=os.environ.get("TEST_S3_ENDPOINT", "http://localhost:9000"),
            aws_access_key_id=os.environ.get("TEST_S3_ACCESS_KEY", "minio"),
            aws_secret_access_key=os.environ.get("TEST_S3_SECRET_KEY", "minio123"),
        )
        client.list_buckets()
        return True
    except Exception:
        return False


def is_iceberg_available() -> bool:
    """Check if Iceberg REST catalog is available for testing."""
    try:
        import requests
        response = requests.get(
            f"{os.environ.get('TEST_ICEBERG_URI', 'http://localhost:8181')}/v1/config",
            timeout=5
        )
        return response.status_code in (200, 404)  # 404 is ok, means catalog is running
    except Exception:
        return False


# Skip markers for infrastructure dependencies
requires_postgres = pytest.mark.skipif(
    not is_postgres_available(),
    reason="PostgreSQL not available. Start test infrastructure with docker-compose."
)

requires_redis = pytest.mark.skipif(
    not is_redis_available(),
    reason="Redis not available. Start test infrastructure with docker-compose."
)

requires_minio = pytest.mark.skipif(
    not is_minio_available(),
    reason="MinIO not available. Start test infrastructure with docker-compose."
)

requires_iceberg = pytest.mark.skipif(
    not is_iceberg_available(),
    reason="Iceberg REST catalog not available. Start test infrastructure with docker-compose."
)


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def async_db_session(test_env):
    """
    Create an async database session for testing.

    Creates a test transaction that is rolled back after each test.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

    db_url = (
        f"postgresql+asyncpg://{test_env['DATABASE__USER']}:{test_env['DATABASE__PASSWORD']}"
        f"@{test_env['DATABASE__HOST']}:{test_env['DATABASE__PORT']}/{test_env['DATABASE__NAME']}"
    )

    engine = create_async_engine(db_url, echo=False)

    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        # Start a transaction
        async with session.begin():
            yield session
            # Rollback after test
            await session.rollback()

    await engine.dispose()


@pytest_asyncio.fixture
async def graph_database(async_db_session):
    """
    Create a graph database instance for testing.

    Initializes the Apache AGE extension and creates a test graph.
    """
    from core.database.graph import GraphDatabase

    graph_db = GraphDatabase(graph_name="test_graph")

    try:
        await graph_db.initialize(async_db_session)
    except Exception as e:
        pytest.skip(f"Could not initialize graph database: {e}")

    yield graph_db

    # Clean up test graph
    try:
        from sqlalchemy import text
        await async_db_session.execute(
            text(f"SELECT drop_graph('test_graph', true)")
        )
        await async_db_session.commit()
    except Exception:
        pass  # Graph might not exist


# =============================================================================
# Redis Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def redis_client(test_env):
    """Create a Redis client for testing."""
    from redis.asyncio import Redis

    redis = Redis(
        host=test_env["REDIS__HOST"],
        port=int(test_env["REDIS__PORT"]),
        decode_responses=True
    )

    yield redis

    # Clean up test keys
    async for key in redis.scan_iter("openforge:test:*"):
        await redis.delete(key)

    await redis.close()


@pytest_asyncio.fixture
async def event_bus(redis_client):
    """Create an EventBus instance for testing."""
    from core.messaging.events import EventBus

    event_bus = EventBus()
    event_bus.redis = redis_client

    yield event_bus

    await event_bus.disconnect()


# =============================================================================
# S3/MinIO Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def s3_client(test_env):
    """Create an S3 client for testing with MinIO."""
    import boto3

    client = boto3.client(
        "s3",
        endpoint_url=test_env["ICEBERG__S3_ENDPOINT"],
        aws_access_key_id=test_env["ICEBERG__S3_ACCESS_KEY"],
        aws_secret_access_key=test_env["ICEBERG__S3_SECRET_KEY"],
    )

    # Create test bucket if it doesn't exist
    test_bucket = "openforge-integration-test"
    try:
        client.create_bucket(Bucket=test_bucket)
    except client.exceptions.BucketAlreadyExists:
        pass
    except client.exceptions.BucketAlreadyOwnedByYou:
        pass

    yield client

    # Clean up test objects
    try:
        response = client.list_objects_v2(Bucket=test_bucket)
        for obj in response.get("Contents", []):
            client.delete_object(Bucket=test_bucket, Key=obj["Key"])
    except Exception:
        pass


# =============================================================================
# Mock LLM Fixtures
# =============================================================================

class MockLLMResponse:
    """Mock LLM response object."""

    def __init__(self, content: str):
        self.content = content


class MockChatModel:
    """
    Mock chat model for testing agent workflows.

    Provides configurable responses for different prompt patterns.
    """

    def __init__(self, responses: Optional[Dict[str, str]] = None):
        self.responses = responses or {}
        self.default_response = '{"status": "ok", "result": "mock response"}'
        self.call_history = []

    async def ainvoke(self, messages, **kwargs):
        """Async invoke the mock model."""
        # Record the call
        self.call_history.append({
            "messages": messages,
            "kwargs": kwargs,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Find matching response
        last_message = messages[-1] if messages else None
        content = getattr(last_message, "content", "") if last_message else ""

        for pattern, response in self.responses.items():
            if pattern.lower() in content.lower():
                return MockLLMResponse(response)

        return MockLLMResponse(self.default_response)

    def invoke(self, messages, **kwargs):
        """Sync invoke (not typically used in async agents)."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.ainvoke(messages, **kwargs)
        )


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing agent interactions."""
    return MockChatModel(responses={
        "stakeholder": json.dumps({
            "stakeholders": [
                {"name": "Test User", "role": "Developer", "department": "Engineering"}
            ],
            "business_processes": [
                {"name": "Data Pipeline", "description": "ETL process"}
            ]
        }),
        "source": json.dumps({
            "discovered_sources": [
                {"name": "test_db", "type": "postgres", "tables": ["users", "orders"]}
            ]
        }),
        "requirement": json.dumps({
            "requirements": [
                {"id": "REQ-001", "description": "Data integration", "priority": "high"}
            ]
        }),
        "ontology": json.dumps({
            "entities": [
                {"name": "Customer", "attributes": ["id", "name", "email"]}
            ]
        }),
    })


@pytest.fixture
def mock_llm_with_custom_responses():
    """Factory fixture for creating mock LLMs with custom responses."""
    def _create_mock(responses: Dict[str, str]) -> MockChatModel:
        return MockChatModel(responses=responses)
    return _create_mock


# =============================================================================
# Agent Framework Fixtures
# =============================================================================

@pytest.fixture
def mock_memory_saver():
    """Create a mock memory saver for agent testing."""
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()


@pytest.fixture
def agent_input_factory():
    """Factory fixture for creating agent inputs."""
    from contracts.agent_interface import AgentInput

    def _create_input(
        engagement_id: str = "test-engagement-001",
        phase: str = "discovery",
        context: Optional[Dict[str, Any]] = None,
        previous_outputs: Optional[Dict[str, Any]] = None,
        human_inputs: Optional[list] = None,
    ) -> AgentInput:
        default_context = {
            "organization": "Test Organization",
            "project_description": "Test project for integration testing",
            "tech_stack": ["Python", "PostgreSQL", "Redis"],
        }

        return AgentInput(
            engagement_id=engagement_id,
            phase=phase,
            context={**default_context, **(context or {})},
            previous_outputs=previous_outputs,
            human_inputs=human_inputs or [],
        )

    return _create_input


# =============================================================================
# API Testing Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_client(test_env):
    """Create a test client for API testing."""
    from httpx import AsyncClient, ASGITransport
    from api.main import create_app

    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Create authentication headers for API tests."""
    return {
        "Authorization": "Bearer test-token",
        "X-Request-ID": "test-request-001",
    }


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_ontology_yaml():
    """Sample LinkML ontology YAML for testing."""
    return """
id: https://example.org/test-ontology
name: TestOntology
version: "1.0.0"
prefixes:
  linkml: https://w3id.org/linkml/
  test: https://example.org/test/

classes:
  Customer:
    description: A customer entity
    attributes:
      id:
        range: string
        required: true
        identifier: true
      name:
        range: string
        required: true
      email:
        range: string
      created_at:
        range: datetime

  Order:
    description: A customer order
    attributes:
      id:
        range: string
        required: true
        identifier: true
      customer_id:
        range: string
        required: true
      total_amount:
        range: decimal
      status:
        range: OrderStatus
      created_at:
        range: datetime

enums:
  OrderStatus:
    permissible_values:
      pending:
        description: Order is pending
      processing:
        description: Order is being processed
      completed:
        description: Order is complete
      cancelled:
        description: Order was cancelled
"""


@pytest.fixture
def sample_engagement_data():
    """Sample engagement data for testing."""
    return {
        "name": "Test Integration Engagement",
        "description": "An engagement for integration testing",
        "objective": "Verify all components work together",
        "priority": "high",
        "data_sources": [
            {
                "name": "test_postgres",
                "type": "postgres",
                "connection": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "test_db"
                }
            }
        ],
        "agent_config": {
            "discovery": {"enabled": True},
            "data_architect": {"enabled": True}
        },
        "tags": ["integration-test", "automated"],
        "requires_approval": False
    }


@pytest.fixture
def sample_approval_request():
    """Sample approval request data for testing."""
    return {
        "engagement_id": "test-engagement-001",
        "approval_type": "agent_action",
        "title": "Test Approval Request",
        "description": "A test approval for integration testing",
        "requested_by": "test-agent",
        "timeout_minutes": 30,
        "context_data": {
            "action": "create_table",
            "table_name": "test_table",
            "agent_confidence": 0.85
        }
    }


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Reset settings cache before each test."""
    try:
        from core.config import get_settings
        get_settings.cache_clear()
    except Exception:
        pass

    yield

    try:
        from core.config import get_settings
        get_settings.cache_clear()
    except Exception:
        pass


# =============================================================================
# Test Markers
# =============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_postgres: marks tests that need PostgreSQL"
    )
    config.addinivalue_line(
        "markers", "requires_redis: marks tests that need Redis"
    )
    config.addinivalue_line(
        "markers", "requires_minio: marks tests that need MinIO/S3"
    )
    config.addinivalue_line(
        "markers", "requires_iceberg: marks tests that need Iceberg catalog"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
