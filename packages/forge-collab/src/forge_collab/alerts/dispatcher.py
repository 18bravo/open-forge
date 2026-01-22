"""Alert dispatcher - Coordinate alert evaluation and notification delivery."""

import logging
from typing import Any, Protocol
import secrets
from datetime import datetime

from forge_collab.alerts.rules import AlertRule, Severity
from forge_collab.alerts.channels import NotificationChannel, Notification


logger = logging.getLogger(__name__)


class RuleStore(Protocol):
    """Protocol for alert rule storage."""

    async def get_rules_for_resource(
        self, resource_type: str, resource_id: str
    ) -> list[AlertRule]:
        """Get all rules that may apply to a resource."""
        ...

    async def get_active_rules(self) -> list[AlertRule]:
        """Get all active rules."""
        ...


class AlertDispatcher:
    """Dispatch alerts based on rules and send notifications.

    The AlertDispatcher coordinates:
    1. Evaluating events against alert rules
    2. Creating notifications for matching rules
    3. Sending notifications through configured channels

    Example usage:
        dispatcher = AlertDispatcher()
        dispatcher.register_channel("slack", slack_channel)
        dispatcher.register_channel("email", email_channel)

        await dispatcher.process_event(
            event_type="data.quality.failed",
            resource_type="dataset",
            resource_id="customer-data",
            event_data={"metric": "completeness", "value": 0.85, "threshold": 0.95},
            rules=active_rules,
        )
    """

    def __init__(self, default_channels: list[str] | None = None):
        """Initialize the dispatcher.

        Args:
            default_channels: Default channels to use if rule doesn't specify
        """
        self._channels: dict[str, NotificationChannel] = {}
        self._default_channels = default_channels or ["webhook"]

    def register_channel(self, name: str, channel: NotificationChannel) -> None:
        """Register a notification channel.

        Args:
            name: Channel identifier
            channel: The NotificationChannel implementation
        """
        self._channels[name] = channel
        logger.info(f"Registered notification channel: {name}")

    def unregister_channel(self, name: str) -> bool:
        """Unregister a notification channel.

        Args:
            name: Channel identifier

        Returns:
            True if channel was removed, False if not found
        """
        if name in self._channels:
            del self._channels[name]
            return True
        return False

    def get_channel(self, name: str) -> NotificationChannel | None:
        """Get a registered channel by name."""
        return self._channels.get(name)

    def list_channels(self) -> list[str]:
        """List all registered channel names."""
        return list(self._channels.keys())

    async def process_event(
        self,
        event_type: str,
        resource_type: str,
        resource_id: str,
        event_data: dict[str, Any],
        rules: list[AlertRule],
        channels: list[str] | None = None,
    ) -> list[Notification]:
        """Process an event against rules and dispatch notifications.

        Args:
            event_type: Type of the event (e.g., "data.quality.failed")
            resource_type: Type of resource (e.g., "dataset")
            resource_id: ID of the resource
            event_data: Event payload data
            rules: List of alert rules to evaluate
            channels: Override channels to use (default: use rule-specified or defaults)

        Returns:
            List of notifications that were sent
        """
        sent_notifications: list[Notification] = []

        # Find matching rules
        matching_rules = [
            rule for rule in rules
            if rule.evaluate(resource_type, resource_id, event_data)
        ]

        if not matching_rules:
            logger.debug(f"No matching rules for {resource_type}/{resource_id}")
            return sent_notifications

        logger.info(
            f"Found {len(matching_rules)} matching rules for "
            f"{resource_type}/{resource_id}"
        )

        # Process each matching rule
        for rule in matching_rules:
            notification = self._create_notification(
                rule=rule,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                event_data=event_data,
            )

            # Determine channels to use
            target_channels = channels or self._get_rule_channels(rule)

            # Dispatch to channels
            success = await self._dispatch_notification(notification, target_channels)
            if success:
                sent_notifications.append(notification)

        return sent_notifications

    def _create_notification(
        self,
        rule: AlertRule,
        event_type: str,
        resource_type: str,
        resource_id: str,
        event_data: dict[str, Any],
    ) -> Notification:
        """Create a notification from an alert rule match."""
        return Notification(
            id=secrets.token_hex(16),
            title=f"[{rule.severity.value.upper()}] {rule.name}",
            message=self._format_message(rule, event_type, event_data),
            severity=rule.severity,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata={
                "rule_id": rule.id,
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def _format_message(
        self,
        rule: AlertRule,
        event_type: str,
        event_data: dict[str, Any],
    ) -> str:
        """Format the notification message."""
        if rule.description:
            return f"{rule.description}\n\nEvent: {event_type}"
        return f"Alert rule '{rule.name}' triggered for event: {event_type}"

    def _get_rule_channels(self, rule: AlertRule) -> list[str]:
        """Get channels to use for a rule.

        Extracts channel information from rule actions or uses defaults.
        """
        channels = set()

        for action in rule.actions:
            if action.type == "notify":
                action_channels = action.parameters.get("channels", [])
                channels.update(action_channels)

        if not channels:
            channels.update(self._default_channels)

        return [c for c in channels if c in self._channels]

    async def _dispatch_notification(
        self,
        notification: Notification,
        channel_names: list[str],
    ) -> bool:
        """Dispatch notification to specified channels.

        Args:
            notification: The notification to send
            channel_names: List of channel names to send to

        Returns:
            True if at least one channel succeeded
        """
        if not channel_names:
            logger.warning("No channels specified for notification dispatch")
            return False

        successes = 0
        for channel_name in channel_names:
            channel = self._channels.get(channel_name)
            if channel is None:
                logger.warning(f"Channel not found: {channel_name}")
                continue

            try:
                success = await channel.send(notification)
                if success:
                    successes += 1
                    logger.info(
                        f"Sent notification {notification.id} via {channel_name}"
                    )
            except Exception as e:
                logger.error(
                    f"Failed to send notification via {channel_name}: {e}"
                )

        return successes > 0

    async def test_channel(
        self,
        channel_name: str,
        test_message: str = "Test notification from Open Forge",
    ) -> bool:
        """Send a test notification to verify channel configuration.

        Args:
            channel_name: Channel to test
            test_message: Message to include in test notification

        Returns:
            True if test was successful
        """
        channel = self._channels.get(channel_name)
        if channel is None:
            logger.error(f"Channel not found: {channel_name}")
            return False

        # Validate configuration first
        if not await channel.validate_config():
            logger.error(f"Channel {channel_name} has invalid configuration")
            return False

        notification = Notification(
            id=secrets.token_hex(16),
            title="Test Notification",
            message=test_message,
            severity=Severity.INFO,
            metadata={"test": True},
        )

        try:
            return await channel.send(notification)
        except NotImplementedError:
            logger.info(f"Channel {channel_name} send not implemented (scaffold)")
            return False
        except Exception as e:
            logger.error(f"Test notification failed: {e}")
            return False
