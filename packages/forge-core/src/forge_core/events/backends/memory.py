"""
In-Memory Event Bus Backend

This module implements the event bus using in-memory data structures.
Ideal for testing and single-process development environments.
"""

from __future__ import annotations

import asyncio
import fnmatch
import logging
from collections import defaultdict

from forge_core.events.bus import (
    BaseEventBus,
    Event,
    EventHandler,
    Subscription,
)

logger = logging.getLogger(__name__)


class InMemoryEventBus(BaseEventBus):
    """
    In-memory event bus implementation.

    This is useful for:
    - Unit and integration testing
    - Single-process development
    - Scenarios where external dependencies are undesirable

    Limitations:
    - Events are not persisted
    - Only works within a single process
    - Lost on application restart

    Example usage:
        >>> bus = InMemoryEventBus()
        >>> await bus.connect()
        >>>
        >>> events_received = []
        >>>
        >>> async def handler(event: Event):
        ...     events_received.append(event)
        >>>
        >>> await bus.subscribe("test.*", handler)
        >>> await bus.publish(Event(topic="test.created", type="created", payload={}))
        >>>
        >>> assert len(events_received) == 1
    """

    def __init__(self, source: str = "forge-core") -> None:
        """Initialize the in-memory event bus."""
        super().__init__(source=source)
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._connected = False

    async def connect(self) -> None:
        """Mark the bus as connected."""
        self._connected = True
        logger.info("In-memory event bus connected")

    async def disconnect(self) -> None:
        """Mark the bus as disconnected and clear handlers."""
        self._connected = False
        self._handlers.clear()
        self._subscriptions.clear()
        logger.info("In-memory event bus disconnected")

    async def publish(self, event: Event) -> None:
        """Publish an event to all matching handlers."""
        if not self._connected:
            raise RuntimeError("Event bus not connected")

        # Find all matching handlers
        handlers_to_call = []
        for pattern, handlers in self._handlers.items():
            if self._matches_pattern(pattern, event.topic):
                handlers_to_call.extend(handlers)

        # Call handlers concurrently
        if handlers_to_call:
            await asyncio.gather(
                *(handler(event) for handler in handlers_to_call),
                return_exceptions=True,
            )

        logger.debug(
            f"Published event {event.id} to {len(handlers_to_call)} handlers"
        )

    async def subscribe(
        self,
        topic: str,
        handler: EventHandler,
    ) -> Subscription:
        """Subscribe a handler to a topic pattern."""
        if not self._connected:
            raise RuntimeError("Event bus not connected")

        self._handlers[topic].append(handler)
        subscription = self._create_subscription(topic, handler)

        logger.debug(f"Subscribed handler to {topic}")
        return subscription

    async def unsubscribe(self, subscription: Subscription) -> None:
        """Unsubscribe a handler from a topic."""
        await super().unsubscribe(subscription)

        topic = subscription.topic
        if topic in self._handlers:
            try:
                self._handlers[topic].remove(subscription.handler)
                if not self._handlers[topic]:
                    del self._handlers[topic]
            except ValueError:
                pass  # Handler already removed

    def _matches_pattern(self, pattern: str, topic: str) -> bool:
        """Check if a topic matches a subscription pattern."""
        # Convert pattern to fnmatch format
        # "**" matches any number of levels
        # "*" matches a single level
        if pattern == "**":
            return True

        # Replace ** with a placeholder, convert single * to [^.]*
        fnmatch_pattern = pattern.replace("**", "\x00")
        fnmatch_pattern = fnmatch_pattern.replace("*", "[^.]*")
        fnmatch_pattern = fnmatch_pattern.replace("\x00", "*")

        return fnmatch.fnmatch(topic, fnmatch_pattern)

    def clear(self) -> None:
        """Clear all handlers and subscriptions (useful for testing)."""
        self._handlers.clear()
        self._subscriptions.clear()

    @property
    def handler_count(self) -> int:
        """Return the total number of registered handlers."""
        return sum(len(handlers) for handlers in self._handlers.values())
