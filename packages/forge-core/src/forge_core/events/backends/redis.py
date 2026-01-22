"""
Redis Event Bus Backend

This module implements the event bus using Redis Pub/Sub.
Recommended for distributed deployments with multiple instances.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from forge_core.events.bus import (
    BaseEventBus,
    Event,
    EventHandler,
    PublishError,
    Subscription,
    SubscriptionError,
)

if TYPE_CHECKING:
    import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisEventBus(BaseEventBus):
    """
    Event bus implementation using Redis Pub/Sub.

    Redis provides:
    - Low latency message delivery
    - Pattern-based subscriptions
    - Scalable fan-out to multiple consumers

    Limitations:
    - No message persistence (fire-and-forget)
    - No guaranteed delivery
    - Messages lost if no subscribers

    For guaranteed delivery, consider using Redis Streams instead.

    Example usage:
        >>> bus = RedisEventBus("redis://localhost:6379")
        >>> await bus.connect()
        >>>
        >>> async def handler(event: Event):
        ...     print(f"Received: {event}")
        >>>
        >>> await bus.subscribe("users.*", handler)
        >>> await bus.publish(Event(topic="users.created", type="created", payload={}))
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        source: str = "forge-core",
        channel_prefix: str = "forge:",
    ) -> None:
        """
        Initialize the Redis event bus.

        Args:
            redis_url: Redis connection URL
            source: Default source for events
            channel_prefix: Prefix for Redis channels
        """
        super().__init__(source=source)
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self._client: "redis.Redis | None" = None
        self._pubsub: "redis.client.PubSub | None" = None
        self._listener_task = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            import redis.asyncio as redis_async

            self._client = redis_async.from_url(self.redis_url)
            self._pubsub = self._client.pubsub()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except ImportError:
            raise ImportError(
                "redis package required. Install with: pip install redis"
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._pubsub:
            await self._pubsub.close()
            self._pubsub = None

        if self._client:
            await self._client.close()
            self._client = None

        logger.info("Disconnected from Redis")

    async def publish(self, event: Event) -> None:
        """Publish an event to Redis."""
        if self._client is None:
            raise PublishError("Not connected to Redis")

        channel = f"{self.channel_prefix}{event.topic}"
        message = json.dumps(event.to_dict())

        try:
            await self._client.publish(channel, message)
            logger.debug(f"Published event {event.id} to {channel}")
        except Exception as e:
            raise PublishError(f"Failed to publish event: {e}")

    async def subscribe(
        self,
        topic: str,
        handler: EventHandler,
    ) -> Subscription:
        """Subscribe to events on a topic."""
        if self._pubsub is None:
            raise SubscriptionError("Not connected to Redis")

        pattern = f"{self.channel_prefix}{topic}"

        # Use pattern subscribe for wildcard support
        if "*" in topic:
            await self._pubsub.psubscribe(pattern)
        else:
            await self._pubsub.subscribe(pattern)

        subscription = self._create_subscription(topic, handler)
        logger.info(f"Subscribed to {pattern}")

        return subscription

    async def unsubscribe(self, subscription: Subscription) -> None:
        """Unsubscribe from a topic."""
        await super().unsubscribe(subscription)

        if self._pubsub:
            pattern = f"{self.channel_prefix}{subscription.topic}"
            if "*" in subscription.topic:
                await self._pubsub.punsubscribe(pattern)
            else:
                await self._pubsub.unsubscribe(pattern)

    async def listen(self) -> None:
        """
        Listen for messages and dispatch to handlers.

        This should be run as a background task.
        """
        if self._pubsub is None:
            return

        async for message in self._pubsub.listen():
            if message["type"] in ("message", "pmessage"):
                try:
                    data = json.loads(message["data"])
                    event = Event.from_dict(data)

                    # Find matching subscriptions
                    for sub in self._subscriptions.values():
                        if self._topic_matches(sub.topic, event.topic):
                            await sub.handler(event)

                except Exception as e:
                    logger.error(f"Error processing message: {e}")

    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """Check if a topic matches a subscription pattern."""
        if "*" not in pattern:
            return pattern == topic

        # Simple wildcard matching
        import fnmatch

        return fnmatch.fnmatch(topic, pattern)
