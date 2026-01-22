"""Forge Collab - Collaboration features for Open Forge.

This package provides collaboration capabilities including:
- **sharing**: Permission management with BATCHED permission checks (P2 fix for N+1 queries),
  shareable links for external sharing
- **alerts**: Alert rule definitions, notification channels (Email, Slack, webhook),
  and alert dispatching
- **audit**: Structured audit event logging, queries, and compliance exports

Example usage:

    # Batched permission checking (avoids N+1 queries)
    from forge_collab.sharing import PermissionService, PermissionCheck

    service = PermissionService(auth_provider)
    results = await service.check_batch(
        user=current_user,
        checks=[
            PermissionCheck(resource="datasets/123", action="read"),
            PermissionCheck(resource="datasets/456", action="write"),
        ]
    )

    # Alert dispatching
    from forge_collab.alerts import AlertDispatcher, SlackChannel

    dispatcher = AlertDispatcher()
    dispatcher.register_channel("slack", SlackChannel(webhook_url="..."))
    await dispatcher.process_event(
        event_type="data.quality.failed",
        resource_type="dataset",
        resource_id="customer-data",
        event_data={"completeness": 0.85},
        rules=active_rules,
    )

    # Audit logging
    from forge_collab.audit import AuditLogger, AuditAction

    logger = AuditLogger(storage_backend)
    await logger.log_create(
        actor_id="user-123",
        resource_type="dataset",
        resource_id="ds-456",
    )
"""

__version__ = "0.1.0"

# Sharing module - Permission management
from forge_collab.sharing import (
    PermissionService,
    PermissionCheck,
    PermissionResult,
    ShareableLink,
    ShareableLinkService,
    PermissionLevel,
    ResourceType,
)

# Alerts module - Notifications and alerting
from forge_collab.alerts import (
    AlertRule,
    AlertCondition,
    AlertAction,
    Severity,
    AlertDispatcher,
    Notification,
    NotificationChannel,
    EmailChannel,
    SlackChannel,
    WebhookChannel,
)

# Audit module - Structured logging
from forge_collab.audit import (
    AuditLogger,
    AuditEvent,
    AuditAction as AuditActionEnum,  # Avoid conflict with alerts.AlertAction
    AuditQuery,
    AuditSearchResult,
    AuditExporter,
    ExportFormat,
)

__all__ = [
    # Version
    "__version__",
    # Sharing
    "PermissionService",
    "PermissionCheck",
    "PermissionResult",
    "ShareableLink",
    "ShareableLinkService",
    "PermissionLevel",
    "ResourceType",
    # Alerts
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
    # Audit
    "AuditLogger",
    "AuditEvent",
    "AuditActionEnum",
    "AuditQuery",
    "AuditSearchResult",
    "AuditExporter",
    "ExportFormat",
]
