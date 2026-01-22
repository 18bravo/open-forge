"""
Event Bus Abstraction

This module defines the core event bus protocol and data types for
event-driven communication across the Open Forge platform.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Protocol, runtime_checkable
from uuid import uuid4


@dataclass
class Event:
    """
    Represents an event in the system.

    Events are immutable records of something that happened in the system.
    They carry a payload and metadata for routing and processing.

    Attributes:
        id: Unique event identifier
        topic: Topic/channel the event is published to
        type: Event type within the topic (e.g., "created", "updated")
        payload: Event data (should be JSON-serializable)
        source: Origin of the event (e.g., "forge-api", "forge-pipelines")
        timestamp: When the event was created
        correlation_id: ID for tracing related events across services
        user_id: ID of the user who triggered the event (if applicable)
        metadata: Additional event metadata
    """

    topic: str
    type: str
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str | None = None
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "id": self.id,
            "topic": self.topic,
            "type": self.type,
            "payload": self.payload,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()

        return cls(
            id=data.get("id", str(uuid4())),
            topic=data["topic"],
            type=data["type"],
            payload=data.get("payload", {}),
            source=data.get("source", ""),
            timestamp=timestamp,
            correlation_id=data.get("correlation_id"),
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {}),
        )


# Type alias for event handlers
EventHandler = Callable[[Event], Awaitable[None]]


@dataclass
class Subscription:
    """
    Represents a subscription to events on a topic.

    Subscriptions can be cancelled to stop receiving events.

    Attributes:
        id: Unique subscription identifier
        topic: Topic pattern being subscribed to
        handler: Callback function for handling events
        created_at: When the subscription was created
    """

    id: str
    topic: str
    handler: EventHandler
    created_at: datetime = field(default_factory=datetime.utcnow)

    async def cancel(self) -> None:
        """
        Cancel this subscription.

        After cancellation, the handler will no longer receive events.
        This method should be implemented by the event bus backend.
        """
        # Stub: Implementation provided by backend
        raise NotImplementedError


@runtime_checkable
class EventBus(Protocol):
    """
    Protocol for event bus implementations.

    The event bus provides publish/subscribe messaging for loose coupling
    between components. Multiple backends are supported for different
    deployment scenarios.

    Example usage:
        >>> bus = RedisEventBus(redis_url="redis://localhost")
        >>> await bus.connect()
        >>>
        >>> # Subscribe to events
        >>> async def handle_user_created(event: Event):
        ...     print(f"User created: {event.payload}")
        >>>
        >>> sub = await bus.subscribe("users", handle_user_created)
        >>>
        >>> # Publish events
        >>> event = Event(
        ...     topic="users",
        ...     type="created",
        ...     payload={"user_id": "123", "email": "user@example.com"},
        ... )
        >>> await bus.publish(event)
    """

    async def connect(self) -> None:
        """
        Connect to the event bus backend.

        This should be called during application startup.
        """
        ...

    async def disconnect(self) -> None:
        """
        Disconnect from the event bus backend.

        This should be called during application shutdown.
        Pending events may be lost.
        """
        ...

    async def publish(self, event: Event) -> None:
        """
        Publish an event to a topic.

        Args:
            event: Event to publish

        Raises:
            EventBusError: If publishing fails
        """
        ...

    async def subscribe(
        self,
        topic: str,
        handler: EventHandler,
    ) -> Subscription:
        """
        Subscribe to events on a topic.

        Args:
            topic: Topic to subscribe to (supports wildcards: "users.*")
            handler: Async function to handle received events

        Returns:
            Subscription that can be cancelled

        Raises:
            EventBusError: If subscription fails
        """
        ...

    async def unsubscribe(self, subscription: Subscription) -> None:
        """
        Unsubscribe from a topic.

        Args:
            subscription: Subscription to cancel
        """
        ...


class BaseEventBus(ABC):
    """
    Abstract base class for event bus implementations.

    Provides common functionality for event serialization and handler management.
    """

    def __init__(self, source: str = "forge-core") -> None:
        """
        Initialize the event bus.

        Args:
            source: Default source for events published from this bus
        """
        self.source = source
        self._subscriptions: dict[str, Subscription] = {}

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the backend."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the backend."""
        ...

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event."""
        ...

    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        handler: EventHandler,
    ) -> Subscription:
        """Subscribe to a topic."""
        ...

    async def unsubscribe(self, subscription: Subscription) -> None:
        """Unsubscribe from a topic."""
        if subscription.id in self._subscriptions:
            del self._subscriptions[subscription.id]

    def _create_subscription(
        self,
        topic: str,
        handler: EventHandler,
    ) -> Subscription:
        """Create and track a new subscription."""
        sub = Subscription(
            id=str(uuid4()),
            topic=topic,
            handler=handler,
        )
        self._subscriptions[sub.id] = sub
        return sub


class EventBusError(Exception):
    """Base exception for event bus errors."""

    pass


class PublishError(EventBusError):
    """Raised when publishing an event fails."""

    pass


class SubscriptionError(EventBusError):
    """Raised when subscription fails."""

    pass
