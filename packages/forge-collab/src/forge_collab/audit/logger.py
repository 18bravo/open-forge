"""Audit logger - Structured event logging for compliance and security."""

from datetime import datetime
from enum import Enum
from typing import Any, Protocol, Literal
import secrets
import logging

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Standard audit actions."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LOGIN = "login"
    LOGOUT = "logout"
    SHARE = "share"
    EXPORT = "export"


class AuditEvent(BaseModel):
    """Structured audit event.

    Captures all relevant context for compliance and security analysis:
    - What happened (action, event_type)
    - Who did it (actor_id, actor_type)
    - What was affected (resource_type, resource_id)
    - When (timestamp)
    - From where (ip_address, user_agent)
    - What changed (changes dict)
    """

    id: str
    timestamp: datetime
    event_type: str = Field(
        description="Hierarchical event type, e.g., 'resource.created', 'user.login'"
    )
    action: AuditAction
    actor_id: str
    actor_type: Literal["user", "service", "system"] = "user"
    resource_type: str | None = None
    resource_id: str | None = None
    resource_name: str | None = None

    # Request context
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    session_id: str | None = None

    # Change details
    changes: dict[str, dict[str, Any]] | None = Field(
        default=None,
        description="Changed fields: {'field': {'old': x, 'new': y}}"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Outcome
    success: bool = True
    error_message: str | None = None

    # Security/compliance flags
    sensitive: bool = Field(
        default=False,
        description="If true, restrict access to this audit record"
    )
    retention_days: int | None = Field(
        default=None,
        description="Override default retention period"
    )

    @classmethod
    def create(
        cls,
        event_type: str,
        action: AuditAction,
        actor_id: str,
        **kwargs: Any,
    ) -> "AuditEvent":
        """Factory method to create an audit event.

        Args:
            event_type: Hierarchical event type
            action: The action performed
            actor_id: ID of the actor (user, service)
            **kwargs: Additional event fields

        Returns:
            New AuditEvent instance
        """
        return cls(
            id=secrets.token_hex(16),
            timestamp=datetime.utcnow(),
            event_type=event_type,
            action=action,
            actor_id=actor_id,
            **kwargs,
        )


class AuditStorage(Protocol):
    """Protocol for audit event storage backend."""

    async def store(self, event: AuditEvent) -> None:
        """Store an audit event."""
        ...

    async def store_batch(self, events: list[AuditEvent]) -> None:
        """Store multiple audit events."""
        ...


class AuditLogger:
    """Structured audit logger for compliance and security.

    The AuditLogger provides a consistent interface for logging audit events
    across the platform. Events are stored in a configurable backend and
    can be queried for compliance reporting, security analysis, and debugging.

    Features:
    - Structured event format
    - Async batch writing for performance
    - Context enrichment (request_id, session_id, etc.)
    - Sensitive data flagging
    - Retention policy support

    Example usage:
        logger = AuditLogger(storage_backend)

        # Log a simple event
        await logger.log(
            event_type="dataset.created",
            action=AuditAction.CREATE,
            actor_id="user-123",
            resource_type="dataset",
            resource_id="ds-456",
        )

        # Log with changes
        await logger.log(
            event_type="dataset.updated",
            action=AuditAction.UPDATE,
            actor_id="user-123",
            resource_type="dataset",
            resource_id="ds-456",
            changes={"name": {"old": "Old Name", "new": "New Name"}},
        )
    """

    def __init__(
        self,
        storage: AuditStorage | None = None,
        default_retention_days: int = 365,
        batch_size: int = 100,
    ):
        """Initialize the audit logger.

        Args:
            storage: Storage backend for persisting events
            default_retention_days: Default retention period for events
            batch_size: Max events to batch before flushing
        """
        self._storage = storage
        self._default_retention = default_retention_days
        self._batch_size = batch_size
        self._batch: list[AuditEvent] = []
        self._context: dict[str, Any] = {}

    def set_context(self, **kwargs: Any) -> None:
        """Set context that will be added to all events.

        Useful for setting request-scoped context like request_id.

        Args:
            **kwargs: Context fields to set
        """
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context fields."""
        self._context.clear()

    async def log(
        self,
        event_type: str,
        action: AuditAction,
        actor_id: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        resource_name: str | None = None,
        changes: dict[str, dict[str, Any]] | None = None,
        success: bool = True,
        error_message: str | None = None,
        sensitive: bool = False,
        metadata: dict[str, Any] | None = None,
        **extra: Any,
    ) -> AuditEvent:
        """Log an audit event.

        Args:
            event_type: Hierarchical event type (e.g., "dataset.created")
            action: The action performed
            actor_id: ID of the actor
            resource_type: Type of affected resource
            resource_id: ID of affected resource
            resource_name: Human-readable name of resource
            changes: Dict of field changes
            success: Whether the action succeeded
            error_message: Error message if action failed
            sensitive: Flag for sensitive operations
            metadata: Additional metadata
            **extra: Additional event fields

        Returns:
            The created AuditEvent
        """
        # Merge context into metadata
        full_metadata = {**self._context, **(metadata or {})}

        event = AuditEvent.create(
            event_type=event_type,
            action=action,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            changes=changes,
            success=success,
            error_message=error_message,
            sensitive=sensitive,
            metadata=full_metadata,
            ip_address=extra.get("ip_address") or self._context.get("ip_address"),
            user_agent=extra.get("user_agent") or self._context.get("user_agent"),
            request_id=extra.get("request_id") or self._context.get("request_id"),
            session_id=extra.get("session_id") or self._context.get("session_id"),
            retention_days=extra.get("retention_days", self._default_retention),
        )

        await self._store_event(event)

        # Also log to standard logger for debugging
        logger.info(
            f"AUDIT: {event_type} | actor={actor_id} | "
            f"resource={resource_type}/{resource_id} | success={success}"
        )

        return event

    async def log_batch(self, events: list[AuditEvent]) -> None:
        """Log multiple events in a batch.

        Args:
            events: List of events to log
        """
        if self._storage:
            await self._storage.store_batch(events)
        else:
            for event in events:
                logger.info(f"AUDIT: {event.event_type} | {event.actor_id}")

    async def _store_event(self, event: AuditEvent) -> None:
        """Store a single event (may batch internally)."""
        if self._storage:
            # For now, store immediately. Could batch for performance.
            await self._storage.store(event)

    # Convenience methods for common operations

    async def log_create(
        self,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        resource_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log a resource creation event."""
        return await self.log(
            event_type=f"{resource_type}.created",
            action=AuditAction.CREATE,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            metadata=metadata,
        )

    async def log_update(
        self,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        changes: dict[str, dict[str, Any]],
        resource_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log a resource update event."""
        return await self.log(
            event_type=f"{resource_type}.updated",
            action=AuditAction.UPDATE,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            changes=changes,
            metadata=metadata,
        )

    async def log_delete(
        self,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        resource_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log a resource deletion event."""
        return await self.log(
            event_type=f"{resource_type}.deleted",
            action=AuditAction.DELETE,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            metadata=metadata,
        )

    async def log_access(
        self,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        resource_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log a resource access (read) event."""
        return await self.log(
            event_type=f"{resource_type}.accessed",
            action=AuditAction.READ,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            metadata=metadata,
        )

    async def log_share(
        self,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        shared_with: str | list[str],
        permission_level: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log a resource sharing event."""
        shared_with_list = (
            shared_with if isinstance(shared_with, list) else [shared_with]
        )
        return await self.log(
            event_type=f"{resource_type}.shared",
            action=AuditAction.SHARE,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata={
                **(metadata or {}),
                "shared_with": shared_with_list,
                "permission_level": permission_level,
            },
        )

    async def log_login(
        self,
        actor_id: str,
        success: bool = True,
        error_message: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log a user login event."""
        return await self.log(
            event_type="user.login",
            action=AuditAction.LOGIN,
            actor_id=actor_id,
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )

    async def log_logout(
        self,
        actor_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Log a user logout event."""
        return await self.log(
            event_type="user.logout",
            action=AuditAction.LOGOUT,
            actor_id=actor_id,
            metadata=metadata,
        )
