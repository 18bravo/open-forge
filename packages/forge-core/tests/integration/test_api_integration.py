"""
Integration tests simulating how forge-core components would be used in an API application.

These tests verify the full integration flow of:
- JWT Authentication
- Event Bus
- Storage
- Rate Limiting
- Circuit Breaker
"""

import os
import pytest
from datetime import timedelta

from forge_core.auth import (
    JWTAuthProvider,
    JWTConfig,
    AuthProviderConfig,
    AuthProviderType,
    User,
    configure_auth,
    get_current_user,
)
from forge_core.events.backends.memory import InMemoryEventBus
from forge_core.events.bus import Event
from forge_core.storage import StorageConfig
from forge_core.storage.abstraction import StorageProvider
from forge_core.storage.backends.local import LocalStorageBackend
from forge_core.gateway import (
    RateLimitConfig,
    CircuitBreakerConfig,
    HealthCheckRegistry,
)
from forge_core.gateway.rate_limit import InMemoryRateLimiter
from forge_core.gateway.circuit_breaker import DefaultCircuitBreaker


# Set up test environment
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-integration-tests")


class TestFullAuthFlow:
    """Test the complete authentication flow as used in an API."""

    @pytest.fixture
    def jwt_provider(self) -> JWTAuthProvider:
        """Create a JWT provider for testing."""
        auth_config = AuthProviderConfig(
            provider_type=AuthProviderType.INTERNAL,
            issuer="open-forge-test",
            client_id="api-test",
        )
        jwt_config = JWTConfig(
            secret_key="test-secret-key-for-integration-tests",
            algorithm="HS256",
            access_token_expire_minutes=30,
        )
        return JWTAuthProvider(auth_config, jwt_config)

    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, jwt_provider: JWTAuthProvider) -> None:
        """Test complete authentication flow: create token -> authenticate -> authorize."""
        # 1. Create access token (like during login)
        access_token = jwt_provider.create_access_token(
            user_id="user-12345",
            username="john.doe",
            email="john@example.com",
            name="John Doe",
            roles=["developer", "analyst"],
            permissions=["dataset:read", "dataset:update", "pipeline:execute"],
            tenant_id="acme-corp",
        )

        # 2. Authenticate (like during API request)
        user = await jwt_provider.authenticate(access_token)

        # Verify user properties
        assert user.id == "user-12345"
        assert user.email == "john@example.com"
        assert user.name == "John Doe"
        assert "developer" in user.roles
        assert "analyst" in user.roles
        assert "dataset:read" in user.permissions
        assert user.tenant_id == "acme-corp"

        # 3. Authorize various actions
        # Should be allowed
        assert await jwt_provider.authorize(user, "dataset", "read")
        assert await jwt_provider.authorize(user, "dataset", "update")
        assert await jwt_provider.authorize(user, "pipeline", "execute")

        # Should be denied
        assert not await jwt_provider.authorize(user, "dataset", "delete")
        assert not await jwt_provider.authorize(user, "admin", "manage")

    @pytest.mark.asyncio
    async def test_refresh_token_flow(self, jwt_provider: JWTAuthProvider) -> None:
        """Test token refresh flow."""
        # Create initial tokens
        refresh_token = jwt_provider.create_refresh_token(
            user_id="user-123",
            username="testuser",
            roles=["user"],
            permissions=["read"],
        )

        # Refresh tokens
        new_access, new_refresh = await jwt_provider.refresh_token(refresh_token)

        # Verify new access token works
        user = await jwt_provider.authenticate(new_access)
        assert user.id == "user-123"

    @pytest.mark.asyncio
    async def test_admin_bypass(self, jwt_provider: JWTAuthProvider) -> None:
        """Test that admin users bypass permission checks."""
        token = jwt_provider.create_access_token(
            user_id="admin-1",
            username="superadmin",
            roles=["admin"],
            permissions=[],  # No explicit permissions
        )
        admin = await jwt_provider.authenticate(token)

        # Admin should have access to everything
        assert await jwt_provider.authorize(admin, "anything", "everything")
        assert await jwt_provider.authorize(admin, "dataset", "delete")
        assert await jwt_provider.authorize(admin, "system", "destroy")


class TestEventDrivenWorkflow:
    """Test event-driven workflow patterns."""

    @pytest.fixture
    async def event_bus(self) -> InMemoryEventBus:
        """Create and connect event bus."""
        bus = InMemoryEventBus(source="integration-test")
        await bus.connect()
        yield bus
        await bus.disconnect()

    @pytest.mark.asyncio
    async def test_event_workflow(self, event_bus: InMemoryEventBus) -> None:
        """Test a typical event-driven workflow."""
        events_log = []

        # Set up subscribers for different event types
        async def audit_handler(event: Event) -> None:
            events_log.append(("audit", event))

        async def notification_handler(event: Event) -> None:
            events_log.append(("notification", event))

        async def analytics_handler(event: Event) -> None:
            events_log.append(("analytics", event))

        # Subscribe to different patterns
        await event_bus.subscribe("engagement.**", audit_handler)
        await event_bus.subscribe("engagement.created", notification_handler)
        await event_bus.subscribe("engagement.*", analytics_handler)

        # Simulate engagement creation
        await event_bus.publish(Event(
            topic="engagement.created",
            type="created",
            payload={
                "engagement_id": "eng-123",
                "name": "Project Alpha",
                "created_by": "user-1",
            },
        ))

        # Verify all handlers were called
        assert len(events_log) == 3
        handlers_called = [h[0] for h in events_log]
        assert "audit" in handlers_called
        assert "notification" in handlers_called
        assert "analytics" in handlers_called

    @pytest.mark.asyncio
    async def test_pattern_matching(self, event_bus: InMemoryEventBus) -> None:
        """Test event pattern matching."""
        received = []

        async def handler(event: Event) -> None:
            received.append(event.topic)

        await event_bus.subscribe("data.*", handler)

        # These should match
        await event_bus.publish(Event(topic="data.created", type="created", payload={}))
        await event_bus.publish(Event(topic="data.updated", type="updated", payload={}))

        # This should NOT match (two levels)
        await event_bus.publish(Event(topic="data.deep.nested", type="nested", payload={}))

        assert len(received) == 2
        assert "data.created" in received
        assert "data.updated" in received


class TestStorageWorkflow:
    """Test storage workflow patterns."""

    @pytest.fixture
    async def storage(self, tmp_path) -> LocalStorageBackend:
        """Create and connect storage backend."""
        config = StorageConfig(
            provider=StorageProvider.LOCAL,
            bucket=str(tmp_path / "test-storage"),
        )
        storage = LocalStorageBackend(config)
        await storage.connect()
        yield storage
        await storage.disconnect()

    @pytest.mark.asyncio
    async def test_file_lifecycle(self, storage: LocalStorageBackend) -> None:
        """Test complete file lifecycle: create -> read -> update -> delete."""
        # Create
        await storage.put(
            key="documents/report.txt",
            data=b"Initial report content",
            content_type="text/plain",
            metadata={"author": "test", "version": "1"},
        )

        # Read
        data, metadata = await storage.get("documents/report.txt")
        assert data == b"Initial report content"
        assert metadata.get("author") == "test"

        # Update
        await storage.put(
            key="documents/report.txt",
            data=b"Updated report content",
            content_type="text/plain",
            metadata={"author": "test", "version": "2"},
        )

        data, metadata = await storage.get("documents/report.txt")
        assert data == b"Updated report content"
        assert metadata.get("version") == "2"

        # Delete
        await storage.delete("documents/report.txt")
        assert not await storage.exists("documents/report.txt")

    @pytest.mark.asyncio
    async def test_list_objects(self, storage: LocalStorageBackend) -> None:
        """Test listing objects with prefix."""
        # Create multiple objects
        for i in range(5):
            await storage.put(f"data/file_{i}.csv", f"content {i}".encode())

        await storage.put("other/file.txt", b"other content")

        # List with prefix
        data_files = []
        async for key in storage.list("data/"):
            data_files.append(key)

        assert len(data_files) == 5
        for key in data_files:
            assert key.startswith("data/")


class TestGatewayPatterns:
    """Test API gateway patterns."""

    @pytest.mark.asyncio
    async def test_rate_limiting_workflow(self) -> None:
        """Test rate limiting for API endpoints."""
        config = RateLimitConfig(
            requests=5,
            window=timedelta(minutes=1),
            key_prefix="api",
        )
        limiter = InMemoryRateLimiter(config)

        # Simulate API requests
        user_key = "user:123"

        # First 5 requests should succeed
        for i in range(5):
            result = await limiter.increment(user_key)
            assert result.allowed, f"Request {i+1} should be allowed"
            assert result.remaining == 4 - i

        # 6th request should be blocked
        result = await limiter.increment(user_key)
        assert not result.allowed
        assert result.retry_after > 0

        # Different user should still be able to make requests
        result = await limiter.increment("user:456")
        assert result.allowed

    @pytest.mark.asyncio
    async def test_circuit_breaker_workflow(self) -> None:
        """Test circuit breaker for external service calls."""
        from forge_core.gateway.circuit_breaker import CircuitState

        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout=timedelta(seconds=1),
        )
        cb = DefaultCircuitBreaker("external-api", config)

        # Simulate successful calls
        for _ in range(2):
            cb.record_success()

        # Circuit should still be closed
        assert cb.state == CircuitState.CLOSED

        # Simulate failures to trip the circuit
        for _ in range(3):
            cb.record_failure(Exception("Simulated failure"))

        # Circuit should now be open
        assert cb.state == CircuitState.OPEN

    def test_health_check_aggregation(self) -> None:
        """Test health check aggregation."""
        from forge_core.gateway.health import ServiceHealth, HealthStatus

        registry = HealthCheckRegistry()

        # Register health checks using the decorator pattern
        @registry.register("database")
        async def db_check() -> ServiceHealth:
            return ServiceHealth(name="database", status=HealthStatus.HEALTHY)

        @registry.register("cache")
        async def cache_check() -> ServiceHealth:
            return ServiceHealth(name="cache", status=HealthStatus.HEALTHY)

        @registry.register("external-api")
        async def external_api_check() -> ServiceHealth:
            return ServiceHealth(name="external-api", status=HealthStatus.UNHEALTHY)

        # Verify all checks are registered
        assert "database" in registry._checks
        assert "cache" in registry._checks
        assert "external-api" in registry._checks


class TestIntegrationScenario:
    """Test a complete integration scenario combining multiple components."""

    @pytest.mark.asyncio
    async def test_api_request_lifecycle(self, tmp_path) -> None:
        """
        Simulate a complete API request lifecycle:
        1. Authenticate user
        2. Check rate limit
        3. Process request (with event emission)
        4. Store result
        """
        # Set up components
        jwt_config = JWTConfig(
            secret_key="test-secret",
            algorithm="HS256",
        )
        auth_config = AuthProviderConfig(
            provider_type=AuthProviderType.INTERNAL,
            issuer="test",
            client_id="test",
        )
        auth_provider = JWTAuthProvider(auth_config, jwt_config)

        rate_config = RateLimitConfig(
            requests=100,
            window=timedelta(minutes=1),
        )
        rate_limiter = InMemoryRateLimiter(rate_config)

        event_bus = InMemoryEventBus()
        await event_bus.connect()

        storage_config = StorageConfig(
            provider=StorageProvider.LOCAL,
            bucket=str(tmp_path / "storage"),
        )
        storage = LocalStorageBackend(storage_config)
        await storage.connect()

        events_received = []

        async def event_handler(event: Event) -> None:
            events_received.append(event)

        await event_bus.subscribe("request.*", event_handler)

        # Simulate request lifecycle

        # 1. Create and authenticate token
        token = auth_provider.create_access_token(
            user_id="user-1",
            username="testuser",
            permissions=["data:write"],
        )
        user = await auth_provider.authenticate(token)
        assert user.id == "user-1"

        # 2. Check rate limit
        rate_result = await rate_limiter.increment(f"user:{user.id}")
        assert rate_result.allowed

        # 3. Check authorization
        authorized = await auth_provider.authorize(user, "data", "write")
        assert authorized

        # 4. Process request and emit event
        await event_bus.publish(Event(
            topic="request.processed",
            type="processed",
            payload={"user_id": user.id, "action": "data:write"},
        ))

        # 5. Store result
        await storage.put(
            key=f"results/{user.id}/output.json",
            data=b'{"status": "success"}',
            content_type="application/json",
        )

        # Verify
        assert len(events_received) == 1
        assert events_received[0].type == "processed"

        data, _ = await storage.get(f"results/{user.id}/output.json")
        assert b"success" in data

        # Cleanup
        await event_bus.disconnect()
        await storage.disconnect()
