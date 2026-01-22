"""Tests for the event bus."""

import pytest

from forge_core.events.bus import Event
from forge_core.events.backends.memory import InMemoryEventBus


class TestEvent:
    """Tests for the Event class."""

    def test_event_creation(self) -> None:
        """Test creating an event."""
        event = Event(
            topic="users.created",
            type="created",
            payload={"user_id": "123"},
        )
        assert event.topic == "users.created"
        assert event.type == "created"
        assert event.payload == {"user_id": "123"}
        assert event.id  # Should have auto-generated ID

    def test_event_to_dict(self) -> None:
        """Test converting event to dictionary."""
        event = Event(
            topic="test.topic",
            type="test",
            payload={"key": "value"},
            source="test-source",
        )
        data = event.to_dict()

        assert data["topic"] == "test.topic"
        assert data["type"] == "test"
        assert data["payload"] == {"key": "value"}
        assert data["source"] == "test-source"
        assert "timestamp" in data

    def test_event_from_dict(self) -> None:
        """Test creating event from dictionary."""
        data = {
            "id": "event-123",
            "topic": "test.topic",
            "type": "test",
            "payload": {"key": "value"},
        }
        event = Event.from_dict(data)

        assert event.id == "event-123"
        assert event.topic == "test.topic"
        assert event.type == "test"
        assert event.payload == {"key": "value"}


class TestInMemoryEventBus:
    """Tests for the InMemoryEventBus."""

    @pytest.mark.asyncio
    async def test_connect_disconnect(self) -> None:
        """Test connecting and disconnecting."""
        bus = InMemoryEventBus()
        await bus.connect()
        assert bus._connected
        await bus.disconnect()
        assert not bus._connected

    @pytest.mark.asyncio
    async def test_publish_subscribe(self, event_bus: InMemoryEventBus) -> None:
        """Test publishing and subscribing to events."""
        received_events: list[Event] = []

        async def handler(event: Event) -> None:
            received_events.append(event)

        await event_bus.subscribe("test.topic", handler)

        event = Event(topic="test.topic", type="test", payload={"data": "value"})
        await event_bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].topic == "test.topic"

    @pytest.mark.asyncio
    async def test_pattern_subscribe(self, event_bus: InMemoryEventBus) -> None:
        """Test pattern-based subscription."""
        received_events: list[Event] = []

        async def handler(event: Event) -> None:
            received_events.append(event)

        await event_bus.subscribe("test.*", handler)

        await event_bus.publish(Event(topic="test.a", type="test", payload={}))
        await event_bus.publish(Event(topic="test.b", type="test", payload={}))
        await event_bus.publish(Event(topic="other.c", type="test", payload={}))

        assert len(received_events) == 2

    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus: InMemoryEventBus) -> None:
        """Test unsubscribing from events."""
        received_events: list[Event] = []

        async def handler(event: Event) -> None:
            received_events.append(event)

        sub = await event_bus.subscribe("test.topic", handler)

        await event_bus.publish(Event(topic="test.topic", type="test", payload={}))
        assert len(received_events) == 1

        await event_bus.unsubscribe(sub)

        await event_bus.publish(Event(topic="test.topic", type="test", payload={}))
        assert len(received_events) == 1  # No new events

    @pytest.mark.asyncio
    async def test_multiple_handlers(self, event_bus: InMemoryEventBus) -> None:
        """Test multiple handlers for the same topic."""
        results: list[str] = []

        async def handler1(event: Event) -> None:
            results.append("handler1")

        async def handler2(event: Event) -> None:
            results.append("handler2")

        await event_bus.subscribe("test.topic", handler1)
        await event_bus.subscribe("test.topic", handler2)

        await event_bus.publish(Event(topic="test.topic", type="test", payload={}))

        assert "handler1" in results
        assert "handler2" in results

    @pytest.mark.asyncio
    async def test_clear(self, event_bus: InMemoryEventBus) -> None:
        """Test clearing all handlers."""
        async def handler(event: Event) -> None:
            pass

        await event_bus.subscribe("test.a", handler)
        await event_bus.subscribe("test.b", handler)

        assert event_bus.handler_count == 2

        event_bus.clear()

        assert event_bus.handler_count == 0
