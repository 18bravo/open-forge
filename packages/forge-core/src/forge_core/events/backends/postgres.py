"""
PostgreSQL Event Bus Backend

This module implements the event bus using PostgreSQL LISTEN/NOTIFY.
Suitable for single-instance deployments or when using PostgreSQL as the primary database.
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
    import asyncpg

logger = logging.getLogger(__name__)


class PostgresEventBus(BaseEventBus):
    """
    Event bus implementation using PostgreSQL LISTEN/NOTIFY.

    PostgreSQL provides:
    - No additional infrastructure required
    - ACID guarantees for notifications sent in transactions
    - Works well for moderate message volumes

    Limitations:
    - 8000 byte payload limit per notification
    - Single database server bottleneck
    - No message persistence

    Example usage:
        >>> bus = PostgresEventBus("postgresql://user:pass@localhost/db")
        >>> await bus.connect()
        >>>
        >>> async def handler(event: Event):
        ...     print(f"Received: {event}")
        >>>
        >>> await bus.subscribe("users", handler)
        >>> await bus.publish(Event(topic="users", type="created", payload={}))
    """

    # Maximum payload size for NOTIFY (8000 bytes)
    MAX_PAYLOAD_SIZE = 8000

    def __init__(
        self,
        dsn: str,
        source: str = "forge-core",
        channel_prefix: str = "forge_",
    ) -> None:
        """
        Initialize the PostgreSQL event bus.

        Args:
            dsn: PostgreSQL connection string
            source: Default source for events
            channel_prefix: Prefix for PostgreSQL channels
        """
        super().__init__(source=source)
        self.dsn = dsn
        self.channel_prefix = channel_prefix
        self._pool: "asyncpg.Pool | None" = None
        self._listener_conn: "asyncpg.Connection | None" = None

    async def connect(self) -> None:
        """Connect to PostgreSQL."""
        try:
            import asyncpg

            self._pool = await asyncpg.create_pool(self.dsn, min_size=2, max_size=10)
            self._listener_conn = await asyncpg.connect(self.dsn)
            logger.info("Connected to PostgreSQL")
        except ImportError:
            raise ImportError(
                "asyncpg package required. Install with: pip install asyncpg"
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
        if self._listener_conn:
            await self._listener_conn.close()
            self._listener_conn = None

        if self._pool:
            await self._pool.close()
            self._pool = None

        logger.info("Disconnected from PostgreSQL")

    async def publish(self, event: Event) -> None:
        """Publish an event using NOTIFY."""
        if self._pool is None:
            raise PublishError("Not connected to PostgreSQL")

        channel = self._get_channel(event.topic)
        payload = json.dumps(event.to_dict())

        if len(payload) > self.MAX_PAYLOAD_SIZE:
            raise PublishError(
                f"Event payload exceeds maximum size of {self.MAX_PAYLOAD_SIZE} bytes"
            )

        try:
            async with self._pool.acquire() as conn:
                await conn.execute(f"NOTIFY {channel}, $1", payload)
            logger.debug(f"Published event {event.id} to {channel}")
        except Exception as e:
            raise PublishError(f"Failed to publish event: {e}")

    async def subscribe(
        self,
        topic: str,
        handler: EventHandler,
    ) -> Subscription:
        """Subscribe to events using LISTEN."""
        if self._listener_conn is None:
            raise SubscriptionError("Not connected to PostgreSQL")

        channel = self._get_channel(topic)

        def callback(conn, pid, channel, payload):
            """Callback for LISTEN notifications."""
            try:
                data = json.loads(payload)
                event = Event.from_dict(data)
                # Schedule handler execution
                import asyncio

                asyncio.create_task(handler(event))
            except Exception as e:
                logger.error(f"Error processing notification: {e}")

        await self._listener_conn.add_listener(channel, callback)
        subscription = self._create_subscription(topic, handler)
        logger.info(f"Subscribed to {channel}")

        return subscription

    async def unsubscribe(self, subscription: Subscription) -> None:
        """Unsubscribe using UNLISTEN."""
        await super().unsubscribe(subscription)

        if self._listener_conn:
            channel = self._get_channel(subscription.topic)
            await self._listener_conn.remove_listener(channel, lambda *args: None)

    def _get_channel(self, topic: str) -> str:
        """
        Convert topic to PostgreSQL channel name.

        PostgreSQL channel names must be valid identifiers,
        so we replace dots with underscores.
        """
        safe_topic = topic.replace(".", "_").replace("*", "all")
        return f"{self.channel_prefix}{safe_topic}"
