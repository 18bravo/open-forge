"""
Pytest configuration and shared fixtures for forge-core tests.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator

import pytest

from forge_core.auth.user import User
from forge_core.config.settings import Environment, Settings
from forge_core.events.backends.memory import InMemoryEventBus
from forge_core.gateway.rate_limit import InMemoryRateLimiter, RateLimitConfig
from forge_core.storage.backends.local import LocalStorageBackend
from forge_core.storage.abstraction import StorageConfig, StorageProvider


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Get test settings."""
    return Settings(
        environment=Environment.TEST,
        debug=True,
    )


@pytest.fixture
def test_user() -> User:
    """Create a test user."""
    return User(
        id="test-user-123",
        email="test@example.com",
        name="Test User",
        roles=frozenset({"developer", "analyst"}),
        permissions=frozenset({"dataset:read", "dataset:write", "pipeline:execute"}),
        tenant_id="test-tenant",
    )


@pytest.fixture
def admin_user() -> User:
    """Create an admin test user."""
    return User(
        id="admin-user-456",
        email="admin@example.com",
        name="Admin User",
        roles=frozenset({"admin", "developer"}),
        permissions=frozenset({"*"}),
        tenant_id="test-tenant",
    )


@pytest.fixture
async def event_bus() -> AsyncGenerator[InMemoryEventBus, None]:
    """Create an in-memory event bus for testing."""
    bus = InMemoryEventBus()
    await bus.connect()
    yield bus
    await bus.disconnect()


@pytest.fixture
def rate_limiter() -> InMemoryRateLimiter:
    """Create an in-memory rate limiter for testing."""
    config = RateLimitConfig(
        requests=10,
        window=timedelta(seconds=60),
    )
    return InMemoryRateLimiter(config)


@pytest.fixture
async def local_storage(tmp_path) -> AsyncGenerator[LocalStorageBackend, None]:
    """Create a local storage backend for testing."""
    config = StorageConfig(
        provider=StorageProvider.LOCAL,
        bucket=str(tmp_path / "test-storage"),
    )
    storage = LocalStorageBackend(config)
    await storage.connect()
    yield storage
    await storage.disconnect()
