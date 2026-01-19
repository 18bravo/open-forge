"""
Integration tests for Redis Streams event bus.

Tests event publishing, subscription, consumer groups, and message
acknowledgment with a real Redis instance.
"""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import json

from tests.integration.conftest import requires_redis


pytestmark = [pytest.mark.integration, requires_redis]


class TestEventBusConnection:
    """Tests for event bus connection management."""

    @pytest.mark.asyncio
    async def test_event_bus_connection(self, event_bus):
        """Test that event bus connects to Redis successfully."""
        assert event_bus is not None
        assert event_bus.redis is not None

    @pytest.mark.asyncio
    async def test_redis_ping(self, redis_client):
        """Test that Redis responds to ping."""
        response = await redis_client.ping()
        assert response is True

    @pytest.mark.asyncio
    async def test_event_bus_disconnect(self, test_env):
        """Test event bus disconnect."""
        from core.messaging.events import EventBus

        event_bus = EventBus()
        # Note: We need to mock the Redis connection for this test
        # since the actual connection requires settings

        # This test verifies the disconnect method exists and doesn't error
        await event_bus.disconnect()


class TestEventPublishing:
    """Tests for event publishing."""

    @pytest.mark.asyncio
    async def test_publish_simple_event(self, event_bus):
        """Test publishing a simple event."""
        event_id = await event_bus.publish(
            "test.simple",
            {"message": "Hello, World!", "timestamp": datetime.utcnow().isoformat()}
        )

        assert event_id is not None
        assert isinstance(event_id, str)

    @pytest.mark.asyncio
    async def test_publish_event_with_complex_payload(self, event_bus):
        """Test publishing event with complex nested payload."""
        payload = {
            "engagement_id": "eng-12345",
            "agent_name": "discovery_agent",
            "results": {
                "sources_found": 5,
                "stakeholders": ["user1", "user2"],
                "metadata": {
                    "confidence": 0.95,
                    "processing_time_ms": 1500
                }
            },
            "tags": ["automated", "integration-test"],
            "created_at": datetime.utcnow().isoformat()
        }

        event_id = await event_bus.publish("test.complex", payload)

        assert event_id is not None

    @pytest.mark.asyncio
    async def test_publish_multiple_events(self, event_bus):
        """Test publishing multiple events."""
        event_ids = []

        for i in range(10):
            event_id = await event_bus.publish(
                "test.batch",
                {"index": i, "message": f"Event {i}"}
            )
            event_ids.append(event_id)

        assert len(event_ids) == 10
        assert len(set(event_ids)) == 10  # All unique IDs

    @pytest.mark.asyncio
    async def test_get_stream_length(self, event_bus):
        """Test getting stream length."""
        # Publish some events
        for i in range(5):
            await event_bus.publish(
                "test.length",
                {"index": i}
            )

        length = await event_bus.get_stream_length("test.length")

        assert length >= 5

    @pytest.mark.asyncio
    async def test_publish_different_event_types(self, event_bus):
        """Test publishing different event types go to different streams."""
        # Publish to different event types
        await event_bus.publish("discovery.started", {"engagement": "1"})
        await event_bus.publish("discovery.completed", {"engagement": "1"})
        await event_bus.publish("agent.task.created", {"task_id": "1"})
        await event_bus.publish("approval.requested", {"approval_id": "1"})

        # Verify events went to correct streams
        discovery_length = await event_bus.get_stream_length("discovery.started")
        agent_length = await event_bus.get_stream_length("agent.task.created")
        approval_length = await event_bus.get_stream_length("approval.requested")

        assert discovery_length >= 1
        assert agent_length >= 1
        assert approval_length >= 1


class TestEventSubscription:
    """Tests for event subscription."""

    @pytest.mark.asyncio
    async def test_subscribe_handler(self, event_bus):
        """Test subscribing a handler to an event type."""
        received_events: List[Any] = []

        async def handler(event):
            received_events.append(event)

        event_bus.subscribe("test.subscribe", handler)

        assert "test.subscribe" in event_bus.handlers
        assert handler in event_bus.handlers["test.subscribe"]

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event(self, event_bus):
        """Test multiple handlers for the same event type."""
        handler1_calls = []
        handler2_calls = []

        def handler1(event):
            handler1_calls.append(event)

        def handler2(event):
            handler2_calls.append(event)

        event_bus.subscribe("test.multi", handler1)
        event_bus.subscribe("test.multi", handler2)

        assert len(event_bus.handlers["test.multi"]) == 2

    @pytest.mark.asyncio
    async def test_subscribe_multiple_event_types(self, event_bus):
        """Test subscribing to multiple event types."""
        handler_calls: Dict[str, List] = {"type1": [], "type2": [], "type3": []}

        def handler_type1(event):
            handler_calls["type1"].append(event)

        def handler_type2(event):
            handler_calls["type2"].append(event)

        def handler_type3(event):
            handler_calls["type3"].append(event)

        event_bus.subscribe("test.type1", handler_type1)
        event_bus.subscribe("test.type2", handler_type2)
        event_bus.subscribe("test.type3", handler_type3)

        assert "test.type1" in event_bus.handlers
        assert "test.type2" in event_bus.handlers
        assert "test.type3" in event_bus.handlers


class TestConsumerGroups:
    """Tests for consumer group functionality."""

    @pytest.mark.asyncio
    async def test_create_consumer_group(self, redis_client):
        """Test creating a consumer group."""
        stream_name = f"events:test_group_{datetime.utcnow().timestamp()}"

        # First add a message to create the stream
        await redis_client.xadd(stream_name, {"data": "init"})

        # Create consumer group
        try:
            await redis_client.xgroup_create(
                stream_name,
                "test_consumer_group",
                mkstream=True
            )
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Verify group exists
        groups = await redis_client.xinfo_groups(stream_name)
        group_names = [g["name"] for g in groups]

        assert "test_consumer_group" in group_names

    @pytest.mark.asyncio
    async def test_consumer_reads_from_group(self, redis_client):
        """Test consumer reading from a group."""
        stream_name = f"events:consumer_read_{datetime.utcnow().timestamp()}"
        group_name = "read_group"
        consumer_name = "consumer1"

        # Create stream with messages
        for i in range(5):
            await redis_client.xadd(
                stream_name,
                {"data": json.dumps({"index": i})}
            )

        # Create consumer group
        try:
            await redis_client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        except Exception:
            pass

        # Read messages as consumer
        messages = await redis_client.xreadgroup(
            group_name,
            consumer_name,
            {stream_name: ">"},
            count=5
        )

        assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_message_acknowledgment(self, redis_client):
        """Test acknowledging messages in a consumer group."""
        stream_name = f"events:ack_test_{datetime.utcnow().timestamp()}"
        group_name = "ack_group"
        consumer_name = "acker"

        # Create stream with message
        message_id = await redis_client.xadd(
            stream_name,
            {"data": "ack_me"}
        )

        # Create group
        try:
            await redis_client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        except Exception:
            pass

        # Read and acknowledge
        messages = await redis_client.xreadgroup(
            group_name,
            consumer_name,
            {stream_name: ">"},
            count=1
        )

        if messages:
            stream, stream_messages = messages[0]
            for msg_id, data in stream_messages:
                ack_count = await redis_client.xack(stream_name, group_name, msg_id)
                assert ack_count == 1


class TestEventProcessing:
    """Tests for end-to-end event processing."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_publish_and_consume_event(self, redis_client):
        """Test publishing and consuming an event end-to-end."""
        stream_name = f"events:e2e_{datetime.utcnow().timestamp()}"
        group_name = "e2e_group"
        consumer_name = "e2e_consumer"

        # Create test event data
        event_data = {
            "event_id": "evt-123",
            "event_type": "test.e2e",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {"message": "end-to-end test", "value": 42}
        }

        # Publish event
        message_id = await redis_client.xadd(
            stream_name,
            {"data": json.dumps(event_data)}
        )

        # Create consumer group
        try:
            await redis_client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        except Exception:
            pass

        # Consume event
        messages = await redis_client.xreadgroup(
            group_name,
            consumer_name,
            {stream_name: ">"},
            count=1,
            block=1000
        )

        assert len(messages) > 0
        stream, stream_messages = messages[0]
        msg_id, data = stream_messages[0]

        received_event = json.loads(data["data"])
        assert received_event["event_id"] == "evt-123"
        assert received_event["payload"]["value"] == 42

        # Acknowledge
        await redis_client.xack(stream_name, group_name, msg_id)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_consumers(self, redis_client):
        """Test multiple consumers processing events concurrently."""
        stream_name = f"events:concurrent_{datetime.utcnow().timestamp()}"
        group_name = "concurrent_group"

        # Publish multiple events
        for i in range(20):
            await redis_client.xadd(
                stream_name,
                {"data": json.dumps({"index": i})}
            )

        # Create consumer group
        try:
            await redis_client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        except Exception:
            pass

        # Simulate multiple consumers
        async def consume(consumer_id: int) -> List[int]:
            consumed = []
            while True:
                messages = await redis_client.xreadgroup(
                    group_name,
                    f"consumer_{consumer_id}",
                    {stream_name: ">"},
                    count=5,
                    block=500
                )

                if not messages:
                    break

                for stream, stream_messages in messages:
                    for msg_id, data in stream_messages:
                        event_data = json.loads(data["data"])
                        consumed.append(event_data["index"])
                        await redis_client.xack(stream_name, group_name, msg_id)

            return consumed

        # Run three consumers concurrently
        results = await asyncio.gather(
            consume(1),
            consume(2),
            consume(3)
        )

        # All events should be processed exactly once
        all_consumed = []
        for r in results:
            all_consumed.extend(r)

        assert len(all_consumed) == 20
        assert set(all_consumed) == set(range(20))


class TestEventBusResilience:
    """Tests for event bus resilience and error handling."""

    @pytest.mark.asyncio
    async def test_publish_without_connection_raises_error(self):
        """Test that publishing without connection raises an error."""
        from core.messaging.events import EventBus

        event_bus = EventBus()
        # Don't connect

        with pytest.raises(RuntimeError, match="EventBus not connected"):
            await event_bus.publish("test.event", {"data": "test"})

    @pytest.mark.asyncio
    async def test_stream_persistence(self, redis_client):
        """Test that events persist in the stream."""
        stream_name = f"events:persist_{datetime.utcnow().timestamp()}"

        # Add events
        for i in range(5):
            await redis_client.xadd(stream_name, {"data": json.dumps({"i": i})})

        # Read all events
        events = await redis_client.xrange(stream_name, "-", "+")

        assert len(events) == 5

        # Read partial range
        partial = await redis_client.xrange(stream_name, "-", "+", count=2)
        assert len(partial) == 2

    @pytest.mark.asyncio
    async def test_stream_trimming(self, redis_client):
        """Test stream trimming to limit size."""
        stream_name = f"events:trim_{datetime.utcnow().timestamp()}"

        # Add many events
        for i in range(100):
            await redis_client.xadd(stream_name, {"data": json.dumps({"i": i})})

        # Trim to 50 entries
        await redis_client.xtrim(stream_name, maxlen=50)

        # Verify length
        length = await redis_client.xlen(stream_name)
        assert length <= 50
