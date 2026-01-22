"""Tests for audit logger."""

from datetime import datetime

import pytest

from forge_collab.audit.logger import (
    AuditLogger,
    AuditEvent,
    AuditAction,
)


class MockAuditStorage:
    """Mock storage for testing."""

    def __init__(self):
        self.events: list[AuditEvent] = []

    async def store(self, event: AuditEvent) -> None:
        self.events.append(event)

    async def store_batch(self, events: list[AuditEvent]) -> None:
        self.events.extend(events)


class TestAuditEvent:
    """Tests for AuditEvent model."""

    def test_create_event(self):
        """Test creating an audit event."""
        event = AuditEvent.create(
            event_type="dataset.created",
            action=AuditAction.CREATE,
            actor_id="user-123",
            resource_type="dataset",
            resource_id="ds-456",
        )

        assert event.id is not None
        assert event.event_type == "dataset.created"
        assert event.action == AuditAction.CREATE
        assert event.actor_id == "user-123"
        assert event.resource_type == "dataset"
        assert event.resource_id == "ds-456"
        assert event.timestamp is not None

    def test_event_defaults(self):
        """Test audit event default values."""
        event = AuditEvent.create(
            event_type="test.event",
            action=AuditAction.READ,
            actor_id="user-123",
        )

        assert event.success is True
        assert event.sensitive is False
        assert event.metadata == {}
        assert event.actor_type == "user"


class TestAuditLogger:
    """Tests for AuditLogger."""

    @pytest.fixture
    def storage(self):
        """Create mock storage."""
        return MockAuditStorage()

    @pytest.fixture
    def logger(self, storage):
        """Create audit logger with mock storage."""
        return AuditLogger(storage=storage)

    @pytest.mark.asyncio
    async def test_log_event(self, logger, storage):
        """Test logging a basic event."""
        event = await logger.log(
            event_type="dataset.created",
            action=AuditAction.CREATE,
            actor_id="user-123",
            resource_type="dataset",
            resource_id="ds-456",
        )

        assert len(storage.events) == 1
        assert storage.events[0].event_type == "dataset.created"

    @pytest.mark.asyncio
    async def test_log_with_changes(self, logger, storage):
        """Test logging an event with changes."""
        changes = {
            "name": {"old": "Old Name", "new": "New Name"},
            "description": {"old": None, "new": "Added description"},
        }

        event = await logger.log(
            event_type="dataset.updated",
            action=AuditAction.UPDATE,
            actor_id="user-123",
            resource_type="dataset",
            resource_id="ds-456",
            changes=changes,
        )

        assert event.changes == changes
        assert storage.events[0].changes == changes

    @pytest.mark.asyncio
    async def test_log_failed_action(self, logger, storage):
        """Test logging a failed action."""
        event = await logger.log(
            event_type="dataset.deleted",
            action=AuditAction.DELETE,
            actor_id="user-123",
            resource_type="dataset",
            resource_id="ds-456",
            success=False,
            error_message="Permission denied",
        )

        assert event.success is False
        assert event.error_message == "Permission denied"

    @pytest.mark.asyncio
    async def test_log_sensitive_operation(self, logger, storage):
        """Test logging a sensitive operation."""
        event = await logger.log(
            event_type="user.password_changed",
            action=AuditAction.UPDATE,
            actor_id="user-123",
            sensitive=True,
        )

        assert event.sensitive is True

    @pytest.mark.asyncio
    async def test_context_is_added_to_events(self, logger, storage):
        """Test that context is added to logged events."""
        logger.set_context(
            request_id="req-123",
            ip_address="192.168.1.1",
        )

        event = await logger.log(
            event_type="test.event",
            action=AuditAction.READ,
            actor_id="user-123",
        )

        assert event.request_id == "req-123"
        assert event.ip_address == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_clear_context(self, logger, storage):
        """Test clearing context."""
        logger.set_context(request_id="req-123")
        logger.clear_context()

        event = await logger.log(
            event_type="test.event",
            action=AuditAction.READ,
            actor_id="user-123",
        )

        assert event.request_id is None

    @pytest.mark.asyncio
    async def test_convenience_method_log_create(self, logger, storage):
        """Test log_create convenience method."""
        event = await logger.log_create(
            actor_id="user-123",
            resource_type="dataset",
            resource_id="ds-456",
            resource_name="Customer Data",
        )

        assert event.event_type == "dataset.created"
        assert event.action == AuditAction.CREATE

    @pytest.mark.asyncio
    async def test_convenience_method_log_update(self, logger, storage):
        """Test log_update convenience method."""
        event = await logger.log_update(
            actor_id="user-123",
            resource_type="dataset",
            resource_id="ds-456",
            changes={"name": {"old": "A", "new": "B"}},
        )

        assert event.event_type == "dataset.updated"
        assert event.action == AuditAction.UPDATE

    @pytest.mark.asyncio
    async def test_convenience_method_log_delete(self, logger, storage):
        """Test log_delete convenience method."""
        event = await logger.log_delete(
            actor_id="user-123",
            resource_type="dataset",
            resource_id="ds-456",
        )

        assert event.event_type == "dataset.deleted"
        assert event.action == AuditAction.DELETE

    @pytest.mark.asyncio
    async def test_convenience_method_log_share(self, logger, storage):
        """Test log_share convenience method."""
        event = await logger.log_share(
            actor_id="user-123",
            resource_type="dataset",
            resource_id="ds-456",
            shared_with=["user-456", "user-789"],
            permission_level="view",
        )

        assert event.event_type == "dataset.shared"
        assert event.action == AuditAction.SHARE
        assert event.metadata["shared_with"] == ["user-456", "user-789"]
        assert event.metadata["permission_level"] == "view"

    @pytest.mark.asyncio
    async def test_convenience_method_log_login(self, logger, storage):
        """Test log_login convenience method."""
        event = await logger.log_login(
            actor_id="user-123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert event.event_type == "user.login"
        assert event.action == AuditAction.LOGIN
        assert event.ip_address == "192.168.1.1"
