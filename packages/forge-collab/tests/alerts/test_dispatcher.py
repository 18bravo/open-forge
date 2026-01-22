"""Tests for alert dispatcher."""

from datetime import datetime

import pytest

from forge_collab.alerts.dispatcher import AlertDispatcher
from forge_collab.alerts.rules import (
    AlertRule,
    AlertCondition,
    AlertAction,
    Severity,
)
from forge_collab.alerts.channels import (
    NotificationChannel,
    Notification,
    WebhookChannel,
)


class MockChannel(NotificationChannel):
    """Mock notification channel for testing."""

    def __init__(self, name: str = "mock", should_succeed: bool = True):
        self._name = name
        self._should_succeed = should_succeed
        self.sent_notifications: list[Notification] = []

    @property
    def name(self) -> str:
        return self._name

    async def send(self, notification: Notification) -> bool:
        self.sent_notifications.append(notification)
        return self._should_succeed

    async def validate_config(self) -> bool:
        return True


class TestAlertDispatcher:
    """Tests for AlertDispatcher."""

    @pytest.fixture
    def dispatcher(self):
        """Create a dispatcher with mock channels."""
        dispatcher = AlertDispatcher(default_channels=["mock"])
        dispatcher.register_channel("mock", MockChannel())
        return dispatcher

    @pytest.fixture
    def sample_rule(self):
        """Create a sample alert rule."""
        return AlertRule(
            id="rule-123",
            name="Test Alert",
            resource_type="dataset",
            resource_pattern="*",
            condition=AlertCondition(
                type="threshold",
                parameters={"metric": "value", "operator": "gt", "value": 100}
            ),
            actions=[
                AlertAction(type="notify", parameters={"channels": ["mock"]})
            ],
            severity=Severity.WARNING,
            created_by="user-123",
            created_at=datetime.utcnow(),
        )

    def test_register_channel(self, dispatcher):
        """Test registering a notification channel."""
        new_channel = MockChannel(name="new")
        dispatcher.register_channel("new", new_channel)

        assert "new" in dispatcher.list_channels()
        assert dispatcher.get_channel("new") is new_channel

    def test_unregister_channel(self, dispatcher):
        """Test unregistering a notification channel."""
        result = dispatcher.unregister_channel("mock")

        assert result is True
        assert "mock" not in dispatcher.list_channels()

    def test_unregister_nonexistent_channel(self, dispatcher):
        """Test unregistering a channel that doesn't exist."""
        result = dispatcher.unregister_channel("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_process_event_with_matching_rule(self, dispatcher, sample_rule):
        """Test processing an event that triggers a rule."""
        notifications = await dispatcher.process_event(
            event_type="data.updated",
            resource_type="dataset",
            resource_id="customer-data",
            event_data={"value": 150},  # Above threshold
            rules=[sample_rule],
        )

        assert len(notifications) == 1
        assert notifications[0].severity == Severity.WARNING

    @pytest.mark.asyncio
    async def test_process_event_no_matching_rule(self, dispatcher, sample_rule):
        """Test processing an event that doesn't trigger any rule."""
        notifications = await dispatcher.process_event(
            event_type="data.updated",
            resource_type="dataset",
            resource_id="customer-data",
            event_data={"value": 50},  # Below threshold
            rules=[sample_rule],
        )

        assert len(notifications) == 0

    @pytest.mark.asyncio
    async def test_process_event_dispatches_to_channel(self, dispatcher, sample_rule):
        """Test that notifications are dispatched to channels."""
        mock_channel = dispatcher.get_channel("mock")

        await dispatcher.process_event(
            event_type="data.updated",
            resource_type="dataset",
            resource_id="customer-data",
            event_data={"value": 150},
            rules=[sample_rule],
        )

        assert len(mock_channel.sent_notifications) == 1
        notification = mock_channel.sent_notifications[0]
        assert "Test Alert" in notification.title
        assert notification.resource_type == "dataset"
        assert notification.resource_id == "customer-data"

    @pytest.mark.asyncio
    async def test_process_event_multiple_matching_rules(self, dispatcher):
        """Test processing event with multiple matching rules."""
        rules = [
            AlertRule(
                id=f"rule-{i}",
                name=f"Alert {i}",
                resource_type="dataset",
                resource_pattern="*",
                condition=AlertCondition(
                    type="threshold",
                    parameters={"metric": "value", "operator": "gt", "value": 100}
                ),
                actions=[AlertAction(type="notify", parameters={})],
                severity=Severity.WARNING,
                created_by="user-123",
                created_at=datetime.utcnow(),
            )
            for i in range(3)
        ]

        notifications = await dispatcher.process_event(
            event_type="data.updated",
            resource_type="dataset",
            resource_id="customer-data",
            event_data={"value": 150},
            rules=rules,
        )

        assert len(notifications) == 3

    @pytest.mark.asyncio
    async def test_channel_failure_continues_to_next(self, dispatcher, sample_rule):
        """Test that channel failure doesn't prevent other channels."""
        failing_channel = MockChannel(name="failing", should_succeed=False)
        working_channel = MockChannel(name="working", should_succeed=True)

        dispatcher.register_channel("failing", failing_channel)
        dispatcher.register_channel("working", working_channel)

        notifications = await dispatcher.process_event(
            event_type="data.updated",
            resource_type="dataset",
            resource_id="customer-data",
            event_data={"value": 150},
            rules=[sample_rule],
            channels=["failing", "working"],
        )

        # Should still succeed with at least one channel
        assert len(notifications) == 1
