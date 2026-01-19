"""
Tests for messaging/events module.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os


class TestEventBus:
    """Tests for EventBus messaging."""

    @pytest.mark.asyncio
    async def test_event_bus_publish(self, mock_env_vars, mock_redis):
        """Test publishing an event."""
        from core.messaging.events import EventBus

        with patch.dict(os.environ, mock_env_vars, clear=False):
            event_bus = EventBus()
            event_bus._redis = mock_redis
            mock_redis.xadd = AsyncMock(return_value="1234567890-0")

            event_id = await event_bus.publish(
                "test.event",
                {"data": "test_value"}
            )

            assert event_id == "1234567890-0"
            mock_redis.xadd.assert_called_once()

    def test_event_bus_subscribe(self, mock_env_vars):
        """Test subscribing to an event type."""
        from core.messaging.events import EventBus

        with patch.dict(os.environ, mock_env_vars, clear=False):
            event_bus = EventBus()
            handler = MagicMock()

            event_bus.subscribe("test.event", handler)

            assert "test.event" in event_bus._handlers
            assert handler in event_bus._handlers["test.event"]

    def test_event_bus_multiple_handlers(self, mock_env_vars):
        """Test multiple handlers for same event type."""
        from core.messaging.events import EventBus

        with patch.dict(os.environ, mock_env_vars, clear=False):
            event_bus = EventBus()
            handler1 = MagicMock()
            handler2 = MagicMock()

            event_bus.subscribe("test.event", handler1)
            event_bus.subscribe("test.event", handler2)

            assert len(event_bus._handlers["test.event"]) == 2
