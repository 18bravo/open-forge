"""Alerts module - Alert rules, notifications, and dispatch channels."""

from forge_collab.alerts.rules import (
    AlertRule,
    AlertCondition,
    AlertAction,
    Severity,
)
from forge_collab.alerts.dispatcher import (
    AlertDispatcher,
    Notification,
)
from forge_collab.alerts.channels import (
    NotificationChannel,
    EmailChannel,
    SlackChannel,
    WebhookChannel,
)

__all__ = [
    "AlertRule",
    "AlertCondition",
    "AlertAction",
    "Severity",
    "AlertDispatcher",
    "Notification",
    "NotificationChannel",
    "EmailChannel",
    "SlackChannel",
    "WebhookChannel",
]
