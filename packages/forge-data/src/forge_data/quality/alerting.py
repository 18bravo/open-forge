"""
Quality alerting infrastructure.

Provides alert channels and dispatch for quality check failures.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AlertChannel(str, Enum):
    """Supported alert channels."""

    SLACK = "slack"
    EMAIL = "email"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"


class AlertConfig(BaseModel):
    """Configuration for alert dispatch."""

    channels: list[AlertChannel] = Field(default_factory=list)
    severity_threshold: str = "warning"
    notify_on_recovery: bool = True
    channel_configs: dict[str, dict[str, Any]] = Field(default_factory=dict)


class Alert(BaseModel):
    """An alert to be dispatched."""

    id: str
    monitor_id: str
    monitor_name: str
    dataset_id: str
    severity: str
    message: str
    failures: list[dict[str, Any]]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertChannelHandler(ABC):
    """Abstract base class for alert channel handlers."""

    @property
    @abstractmethod
    def channel_type(self) -> AlertChannel:
        """Return the channel type this handler supports."""
        ...

    @abstractmethod
    async def send(self, alert: Alert, config: dict[str, Any]) -> bool:
        """
        Send an alert through this channel.

        Args:
            alert: The alert to send
            config: Channel-specific configuration

        Returns:
            True if sent successfully
        """
        ...


class SlackAlertHandler(AlertChannelHandler):
    """Slack alert channel handler (stub)."""

    @property
    def channel_type(self) -> AlertChannel:
        return AlertChannel.SLACK

    async def send(self, alert: Alert, config: dict[str, Any]) -> bool:
        """
        Send alert to Slack.

        Config options:
            webhook_url: Slack webhook URL
            channel: Channel to post to (optional)
        """
        # Stub implementation
        # Full implementation would use httpx to post to webhook_url
        return True


class EmailAlertHandler(AlertChannelHandler):
    """Email alert channel handler (stub)."""

    @property
    def channel_type(self) -> AlertChannel:
        return AlertChannel.EMAIL

    async def send(self, alert: Alert, config: dict[str, Any]) -> bool:
        """
        Send alert via email.

        Config options:
            recipients: List of email addresses
            smtp_host: SMTP server host
            smtp_port: SMTP server port
        """
        # Stub implementation
        return True


class AlertDispatcher:
    """
    Dispatches alerts through configured channels.

    Example:
        dispatcher = AlertDispatcher()
        dispatcher.register_handler(SlackAlertHandler())
        dispatcher.register_handler(EmailAlertHandler())

        await dispatcher.dispatch(monitor, failures)
    """

    def __init__(self) -> None:
        self._handlers: dict[AlertChannel, AlertChannelHandler] = {}

    def register_handler(self, handler: AlertChannelHandler) -> None:
        """Register an alert channel handler."""
        self._handlers[handler.channel_type] = handler

    async def dispatch(
        self,
        monitor: Any,  # QualityMonitor
        failures: list[Any],  # list[CheckResult]
    ) -> list[AlertChannel]:
        """
        Dispatch alerts for check failures.

        Args:
            monitor: The monitor that produced failures
            failures: List of failed check results

        Returns:
            List of channels that were successfully notified
        """
        if not monitor.alerting or not failures:
            return []

        alert = Alert(
            id=f"alert-{monitor.id}-{datetime.utcnow().timestamp()}",
            monitor_id=monitor.id,
            monitor_name=monitor.name,
            dataset_id=monitor.dataset_id,
            severity=max(f.severity for f in failures) if failures else "info",
            message=f"{len(failures)} quality check(s) failed for {monitor.name}",
            failures=[f.model_dump() if hasattr(f, "model_dump") else f for f in failures],
        )

        successful_channels = []
        for channel in monitor.alerting.channels:
            if channel in self._handlers:
                config = monitor.alerting.channel_configs.get(channel.value, {})
                success = await self._handlers[channel].send(alert, config)
                if success:
                    successful_channels.append(channel)

        return successful_channels
