"""
Event Handler Registration

This module provides utilities for registering and managing event handlers.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from forge_core.events.bus import Event, EventBus, EventHandler, Subscription
    from forge_core.events.topics import TopicPattern

logger = logging.getLogger(__name__)


@dataclass
class HandlerRegistration:
    """
    Registration information for an event handler.

    Attributes:
        topic: Topic or pattern to subscribe to
        handler: Event handler function
        name: Human-readable handler name
        retries: Number of retry attempts on failure
        timeout: Handler timeout in seconds
    """

    topic: str
    handler: "EventHandler"
    name: str = ""
    retries: int = 3
    timeout: float = 30.0


class EventHandlerRegistry:
    """
    Registry for event handlers.

    Provides a centralized way to register handlers and manage their lifecycle.
    Supports automatic reconnection and error handling.

    Example usage:
        >>> registry = EventHandlerRegistry()
        >>>
        >>> @registry.handler("users.user.created")
        >>> async def on_user_created(event: Event):
        ...     print(f"User created: {event.payload}")
        >>>
        >>> # Start all handlers
        >>> await registry.start(event_bus)
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._registrations: list[HandlerRegistration] = []
        self._subscriptions: list["Subscription"] = []
        self._bus: "EventBus | None" = None

    def handler(
        self,
        topic: str,
        *,
        name: str = "",
        retries: int = 3,
        timeout: float = 30.0,
    ) -> Callable[["EventHandler"], "EventHandler"]:
        """
        Decorator to register an event handler.

        Args:
            topic: Topic or pattern to subscribe to
            name: Human-readable handler name (defaults to function name)
            retries: Number of retry attempts on failure
            timeout: Handler timeout in seconds

        Returns:
            Decorator function

        Example:
            >>> @registry.handler("data.dataset.created")
            >>> async def handle_dataset_created(event: Event):
            ...     # Process the event
            ...     pass
        """

        def decorator(func: "EventHandler") -> "EventHandler":
            registration = HandlerRegistration(
                topic=topic,
                handler=func,
                name=name or func.__name__,
                retries=retries,
                timeout=timeout,
            )
            self._registrations.append(registration)
            return func

        return decorator

    def register(
        self,
        topic: str,
        handler: "EventHandler",
        *,
        name: str = "",
        retries: int = 3,
        timeout: float = 30.0,
    ) -> None:
        """
        Register an event handler programmatically.

        Args:
            topic: Topic or pattern to subscribe to
            handler: Event handler function
            name: Human-readable handler name
            retries: Number of retry attempts on failure
            timeout: Handler timeout in seconds
        """
        registration = HandlerRegistration(
            topic=topic,
            handler=handler,
            name=name or handler.__name__,
            retries=retries,
            timeout=timeout,
        )
        self._registrations.append(registration)

    async def start(self, bus: "EventBus") -> None:
        """
        Start all registered handlers.

        Subscribes all handlers to their topics on the event bus.

        Args:
            bus: Event bus to subscribe to
        """
        self._bus = bus

        for reg in self._registrations:
            wrapped_handler = self._wrap_handler(reg)
            subscription = await bus.subscribe(reg.topic, wrapped_handler)
            self._subscriptions.append(subscription)
            logger.info(f"Registered handler '{reg.name}' for topic '{reg.topic}'")

    async def stop(self) -> None:
        """
        Stop all handlers.

        Unsubscribes all handlers from the event bus.
        """
        if self._bus is None:
            return

        for subscription in self._subscriptions:
            await self._bus.unsubscribe(subscription)

        self._subscriptions.clear()
        logger.info("Stopped all event handlers")

    def _wrap_handler(
        self,
        registration: HandlerRegistration,
    ) -> "EventHandler":
        """Wrap a handler with retry and timeout logic."""

        async def wrapped(event: "Event") -> None:
            last_error: Exception | None = None

            for attempt in range(registration.retries + 1):
                try:
                    await asyncio.wait_for(
                        registration.handler(event),
                        timeout=registration.timeout,
                    )
                    return
                except asyncio.TimeoutError:
                    last_error = TimeoutError(
                        f"Handler '{registration.name}' timed out "
                        f"after {registration.timeout}s"
                    )
                    logger.warning(
                        f"Handler '{registration.name}' timeout on attempt {attempt + 1}"
                    )
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Handler '{registration.name}' failed on attempt {attempt + 1}: {e}"
                    )

                if attempt < registration.retries:
                    # Exponential backoff
                    await asyncio.sleep(2**attempt)

            # All retries exhausted
            logger.error(
                f"Handler '{registration.name}' failed after "
                f"{registration.retries + 1} attempts: {last_error}"
            )

        return wrapped

    @property
    def handlers(self) -> list[HandlerRegistration]:
        """Get all registered handlers."""
        return list(self._registrations)
