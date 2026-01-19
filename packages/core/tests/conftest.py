"""
Pytest fixtures for core package tests.
"""
import os
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing."""
    env_vars = {
        "ENVIRONMENT": "test",
        "DATABASE__HOST": "localhost",
        "DATABASE__PORT": "5432",
        "DATABASE__NAME": "test_db",
        "DATABASE__USER": "test_user",
        "DATABASE__PASSWORD": "test_pass",
        "REDIS__HOST": "localhost",
        "REDIS__PORT": "6379",
        "ICEBERG__REST_URI": "http://localhost:8181",
        "ICEBERG__WAREHOUSE": "s3://test-bucket/warehouse",
        "ICEBERG__S3_ENDPOINT": "http://localhost:9000",
        "ICEBERG__S3_ACCESS_KEY": "minioadmin",
        "ICEBERG__S3_SECRET_KEY": "minioadmin",
        "LLM__PROVIDER": "anthropic",
        "LLM__MODEL": "claude-3-sonnet-20240229",
        "LLM__API_KEY": "test-api-key",
        "OBSERVABILITY__SERVICE_NAME": "test-service",
        "OBSERVABILITY__OTLP_ENDPOINT": "http://localhost:4317",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_async_session():
    """Create a mock async database session."""
    session = MagicMock()
    session.execute = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = MagicMock()
    redis.get = MagicMock(return_value=None)
    redis.set = MagicMock()
    redis.xadd = MagicMock(return_value="1234567890-0")
    redis.xread = MagicMock(return_value=[])
    return redis
