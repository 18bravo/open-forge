"""
Integration tests for forge-core + api integration.

These tests verify that forge-core components are properly integrated
into the API application.
"""

import pytest
from datetime import timedelta

from api.dependencies import (
    init_auth_provider,
    close_auth_provider,
    init_event_bus,
    close_event_bus,
    init_storage,
    close_storage,
    init_rate_limiter,
    init_health_registry,
    get_auth_provider_instance,
    get_event_bus,
    get_storage,
    get_rate_limiter,
    get_circuit_breaker,
    get_health_registry,
    publish_event,
)
from forge_core.auth import JWTAuthProvider, User
from forge_core.events.backends.memory import InMemoryEventBus
from forge_core.events.bus import Event
from forge_core.gateway import RateLimitExceeded


class TestAuthIntegration:
    """Tests for auth provider integration."""

    @pytest.fixture(autouse=True)
    async def setup_auth(self):
        """Set up and tear down auth provider."""
        # Set test secret key
        import os
        os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"

        await init_auth_provider()
        yield
        await close_auth_provider()

    @pytest.mark.asyncio
    async def test_auth_provider_initialization(self):
        """Test that auth provider is properly initialized."""
        provider = get_auth_provider_instance()
        assert provider is not None
        assert isinstance(provider, JWTAuthProvider)

    @pytest.mark.asyncio
    async def test_create_and_authenticate_token(self):
        """Test creating and authenticating a JWT token."""
        provider = get_auth_provider_instance()

        # Create a token
        token = provider.create_access_token(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            roles=["admin", "developer"],
            permissions=["dataset:read", "pipeline:execute"],
        )

        # Authenticate with the token
        user = await provider.authenticate(token)

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert "admin" in user.roles
        assert "dataset:read" in user.permissions

    @pytest.mark.asyncio
    async def test_authorization_check(self):
        """Test authorization checks work correctly."""
        provider = get_auth_provider_instance()

        # Create admin user
        admin_token = provider.create_access_token(
            user_id="admin-1",
            username="admin",
            roles=["admin"],
            permissions=[],
        )
        admin = await provider.authenticate(admin_token)

        # Admin should have full access
        assert await provider.authorize(admin, "dataset", "delete")
        assert await provider.authorize(admin, "any", "action")

        # Create regular user
        user_token = provider.create_access_token(
            user_id="user-1",
            username="user",
            roles=["developer"],
            permissions=["dataset:read"],
        )
        user = await provider.authenticate(user_token)

        # User should only have granted permissions
        assert await provider.authorize(user, "dataset", "read")
        assert not await provider.authorize(user, "dataset", "delete")


class TestEventBusIntegration:
    """Tests for event bus integration."""

    @pytest.fixture(autouse=True)
    async def setup_event_bus(self):
        """Set up and tear down event bus."""
        await init_event_bus()
        yield
        await close_event_bus()

    @pytest.mark.asyncio
    async def test_event_bus_initialization(self):
        """Test that event bus is properly initialized."""
        bus = get_event_bus()
        assert bus is not None
        assert isinstance(bus, InMemoryEventBus)

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self):
        """Test publishing and subscribing to events."""
        bus = get_event_bus()
        received_events = []

        async def handler(event: Event):
            received_events.append(event)

        await bus.subscribe("test.topic", handler)

        # Publish event
        event = Event(
            topic="test.topic",
            type="test",
            payload={"message": "hello"},
        )
        await bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].payload["message"] == "hello"

    @pytest.mark.asyncio
    async def test_publish_event_helper(self):
        """Test the publish_event helper function."""
        bus = get_event_bus()
        received_events = []

        async def handler(event: Event):
            received_events.append(event)

        await bus.subscribe("engagement.created", handler)

        # Use helper function
        await publish_event(
            topic="engagement.created",
            event_type="created",
            payload={"engagement_id": "eng-123"},
        )

        assert len(received_events) == 1
        assert received_events[0].type == "created"


class TestStorageIntegration:
    """Tests for storage integration."""

    @pytest.fixture(autouse=True)
    async def setup_storage(self, tmp_path):
        """Set up and tear down storage."""
        await init_storage(str(tmp_path / "test-storage"))
        yield
        await close_storage()

    @pytest.mark.asyncio
    async def test_storage_initialization(self):
        """Test that storage is properly initialized."""
        storage = get_storage()
        assert storage is not None

    @pytest.mark.asyncio
    async def test_storage_put_and_get(self):
        """Test storing and retrieving objects."""
        storage = get_storage()

        # Store an object
        test_data = b"Hello, World!"
        await storage.put(
            key="test/file.txt",
            data=test_data,
            content_type="text/plain",
            metadata={"author": "test"},
        )

        # Retrieve the object
        data, metadata = await storage.get("test/file.txt")

        assert data == test_data
        assert metadata.get("author") == "test"

    @pytest.mark.asyncio
    async def test_storage_exists(self):
        """Test checking if objects exist."""
        storage = get_storage()

        # Object shouldn't exist initially
        assert not await storage.exists("nonexistent.txt")

        # Create object
        await storage.put("exists.txt", b"data")

        # Now it should exist
        assert await storage.exists("exists.txt")


class TestRateLimiterIntegration:
    """Tests for rate limiter integration."""

    @pytest.fixture(autouse=True)
    async def setup_rate_limiter(self):
        """Set up rate limiter."""
        await init_rate_limiter(requests_per_minute=10)
        yield

    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test that rate limiter is properly initialized."""
        limiter = get_rate_limiter()
        assert limiter is not None

    @pytest.mark.asyncio
    async def test_rate_limit_allows_requests(self):
        """Test that requests under the limit are allowed."""
        limiter = get_rate_limiter()

        # First request should be allowed
        result = await limiter.increment("test-user")
        assert result.allowed
        assert result.remaining == 9

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excess_requests(self):
        """Test that excess requests are blocked."""
        limiter = get_rate_limiter()

        # Make requests up to the limit
        for i in range(10):
            result = await limiter.increment("rate-test-user")
            assert result.allowed

        # Next request should be blocked
        result = await limiter.increment("rate-test-user")
        assert not result.allowed
        assert result.retry_after > 0


class TestCircuitBreakerIntegration:
    """Tests for circuit breaker integration."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_creation(self):
        """Test creating circuit breakers."""
        cb = get_circuit_breaker("test-service")
        assert cb is not None
        assert cb.name == "test-service"

    @pytest.mark.asyncio
    async def test_circuit_breaker_same_instance(self):
        """Test that same name returns same instance."""
        cb1 = get_circuit_breaker("shared-service")
        cb2 = get_circuit_breaker("shared-service")
        assert cb1 is cb2

    @pytest.mark.asyncio
    async def test_circuit_breaker_different_instances(self):
        """Test that different names return different instances."""
        cb1 = get_circuit_breaker("service-a")
        cb2 = get_circuit_breaker("service-b")
        assert cb1 is not cb2


class TestHealthRegistryIntegration:
    """Tests for health registry integration."""

    @pytest.fixture(autouse=True)
    def setup_health_registry(self):
        """Set up health registry."""
        init_health_registry()
        yield

    def test_health_registry_initialization(self):
        """Test that health registry is properly initialized."""
        registry = get_health_registry()
        assert registry is not None
