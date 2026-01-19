"""
Integration tests for agent state persistence with Redis.

Tests checkpoint saving, loading, and state recovery.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any
import json

from tests.integration.conftest import requires_redis


pytestmark = [pytest.mark.integration, requires_redis]


class TestRedisMemorySaver:
    """Tests for Redis-backed memory saver."""

    @pytest.mark.asyncio
    async def test_memory_saver_initialization(self, redis_client):
        """Test RedisMemorySaver initialization."""
        from agent_framework.memory import RedisMemorySaver

        saver = RedisMemorySaver(redis_client=redis_client)

        assert saver is not None
        assert saver.prefix == "openforge:checkpoint"

    @pytest.mark.asyncio
    async def test_save_checkpoint(self, redis_client):
        """Test saving a checkpoint."""
        from agent_framework.memory import RedisMemorySaver

        saver = RedisMemorySaver(redis_client=redis_client)

        thread_id = f"test_thread_{datetime.utcnow().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}

        checkpoint = {
            "state": {
                "messages": [],
                "outputs": {"result": "test"},
                "current_step": "step1"
            },
            "id": "checkpoint_1"
        }

        await saver.aput(config, checkpoint)

        # Verify checkpoint was saved
        key = f"openforge:checkpoint:{thread_id}:checkpoint_1"
        data = await redis_client.get(key)

        assert data is not None
        saved_checkpoint = json.loads(data)
        assert saved_checkpoint["state"]["outputs"]["result"] == "test"

    @pytest.mark.asyncio
    async def test_get_checkpoint(self, redis_client):
        """Test retrieving a checkpoint."""
        from agent_framework.memory import RedisMemorySaver

        saver = RedisMemorySaver(redis_client=redis_client)

        thread_id = f"get_test_{datetime.utcnow().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}

        # Save checkpoint
        checkpoint = {
            "state": {"value": 42},
            "id": "cp_get_test"
        }
        await saver.aput(config, checkpoint)

        # Retrieve checkpoint
        config_with_id = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": "cp_get_test"
            }
        }
        retrieved = await saver.aget(config_with_id)

        assert retrieved is not None
        assert retrieved["state"]["value"] == 42

    @pytest.mark.asyncio
    async def test_get_latest_checkpoint(self, redis_client):
        """Test retrieving the latest checkpoint."""
        from agent_framework.memory import RedisMemorySaver

        saver = RedisMemorySaver(redis_client=redis_client)

        thread_id = f"latest_test_{datetime.utcnow().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}

        # Save multiple checkpoints
        for i in range(3):
            checkpoint = {
                "state": {"iteration": i},
                "id": f"cp_{i}"
            }
            await saver.aput(config, checkpoint)

        # Get latest (without checkpoint_id)
        retrieved = await saver.aget(config)

        assert retrieved is not None
        assert retrieved["state"]["iteration"] == 2

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, redis_client):
        """Test listing all checkpoints for a thread."""
        from agent_framework.memory import RedisMemorySaver

        saver = RedisMemorySaver(redis_client=redis_client)

        thread_id = f"list_test_{datetime.utcnow().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}

        # Save multiple checkpoints
        for i in range(5):
            checkpoint = {
                "state": {"step": i},
                "id": f"list_cp_{i}"
            }
            await saver.aput(config, checkpoint)

        # List checkpoints
        checkpoints = await saver.alist(config)

        assert len(checkpoints) >= 5

    @pytest.mark.asyncio
    async def test_checkpoint_without_thread_id(self, redis_client):
        """Test that operations without thread_id return None/empty."""
        from agent_framework.memory import RedisMemorySaver

        saver = RedisMemorySaver(redis_client=redis_client)

        config = {"configurable": {}}

        # Get should return None
        result = await saver.aget(config)
        assert result is None

        # List should return empty
        checkpoints = await saver.alist(config)
        assert len(checkpoints) == 0


class TestConversationMemory:
    """Tests for conversation memory."""

    @pytest.mark.asyncio
    async def test_add_message(self, redis_client):
        """Test adding a message to conversation memory."""
        from agent_framework.memory import ConversationMemory

        memory = ConversationMemory(redis_client=redis_client)
        thread_id = f"conv_test_{datetime.utcnow().timestamp()}"

        await memory.add_message(
            thread_id=thread_id,
            role="user",
            content="Hello, agent!",
            metadata={"source": "test"}
        )

        messages = await memory.get_messages(thread_id)

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello, agent!"
        assert messages[0]["metadata"]["source"] == "test"

    @pytest.mark.asyncio
    async def test_add_multiple_messages(self, redis_client):
        """Test adding multiple messages."""
        from agent_framework.memory import ConversationMemory

        memory = ConversationMemory(redis_client=redis_client)
        thread_id = f"multi_msg_{datetime.utcnow().timestamp()}"

        # Add conversation
        await memory.add_message(thread_id, "user", "What is 2+2?")
        await memory.add_message(thread_id, "assistant", "2+2 equals 4")
        await memory.add_message(thread_id, "user", "Thanks!")
        await memory.add_message(thread_id, "assistant", "You're welcome!")

        messages = await memory.get_messages(thread_id)

        assert len(messages) == 4
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_messages_with_limit(self, redis_client):
        """Test getting messages with a limit."""
        from agent_framework.memory import ConversationMemory

        memory = ConversationMemory(redis_client=redis_client)
        thread_id = f"limit_msg_{datetime.utcnow().timestamp()}"

        # Add 10 messages
        for i in range(10):
            await memory.add_message(thread_id, "user", f"Message {i}")

        # Get only last 3
        messages = await memory.get_messages(thread_id, limit=3)

        assert len(messages) == 3
        assert messages[-1]["content"] == "Message 9"

    @pytest.mark.asyncio
    async def test_message_trimming(self, redis_client):
        """Test that messages are trimmed to max size."""
        from agent_framework.memory import ConversationMemory

        memory = ConversationMemory(
            max_messages=5,
            redis_client=redis_client
        )
        thread_id = f"trim_msg_{datetime.utcnow().timestamp()}"

        # Add 10 messages
        for i in range(10):
            await memory.add_message(thread_id, "user", f"Message {i}")

        messages = await memory.get_messages(thread_id)

        # Should only have last 5
        assert len(messages) <= 5

    @pytest.mark.asyncio
    async def test_clear_conversation(self, redis_client):
        """Test clearing conversation history."""
        from agent_framework.memory import ConversationMemory

        memory = ConversationMemory(redis_client=redis_client)
        thread_id = f"clear_msg_{datetime.utcnow().timestamp()}"

        # Add messages
        await memory.add_message(thread_id, "user", "Message 1")
        await memory.add_message(thread_id, "user", "Message 2")

        # Clear
        await memory.clear(thread_id)

        # Should be empty
        messages = await memory.get_messages(thread_id)
        assert len(messages) == 0


class TestEngagementContext:
    """Tests for engagement-level context."""

    @pytest.mark.asyncio
    async def test_set_context_value(self, redis_client):
        """Test setting a context value."""
        from agent_framework.memory import EngagementContext

        engagement_id = f"eng_{datetime.utcnow().timestamp()}"
        context = EngagementContext(
            engagement_id=engagement_id,
            redis_client=redis_client
        )

        await context.set("stakeholders", ["user1", "user2"])
        await context.set("status", "in_progress")

        value = await context.get("stakeholders")
        assert value == ["user1", "user2"]

        status = await context.get("status")
        assert status == "in_progress"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, redis_client):
        """Test getting a key that doesn't exist."""
        from agent_framework.memory import EngagementContext

        engagement_id = f"eng_nonexist_{datetime.utcnow().timestamp()}"
        context = EngagementContext(
            engagement_id=engagement_id,
            redis_client=redis_client
        )

        # Get with default
        value = await context.get("nonexistent", default="default_value")
        assert value == "default_value"

        # Get without default
        value = await context.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_get_all_context(self, redis_client):
        """Test getting all context values."""
        from agent_framework.memory import EngagementContext

        engagement_id = f"eng_all_{datetime.utcnow().timestamp()}"
        context = EngagementContext(
            engagement_id=engagement_id,
            redis_client=redis_client
        )

        await context.set("key1", "value1")
        await context.set("key2", {"nested": "object"})
        await context.set("key3", 42)

        all_values = await context.get_all()

        assert "key1" in all_values
        assert all_values["key1"] == "value1"
        assert all_values["key2"]["nested"] == "object"
        assert all_values["key3"] == 42

    @pytest.mark.asyncio
    async def test_delete_context_key(self, redis_client):
        """Test deleting a context key."""
        from agent_framework.memory import EngagementContext

        engagement_id = f"eng_del_{datetime.utcnow().timestamp()}"
        context = EngagementContext(
            engagement_id=engagement_id,
            redis_client=redis_client
        )

        await context.set("to_delete", "temporary")
        assert await context.get("to_delete") == "temporary"

        await context.delete("to_delete")
        assert await context.get("to_delete") is None

    @pytest.mark.asyncio
    async def test_complex_context_values(self, redis_client):
        """Test storing complex objects in context."""
        from agent_framework.memory import EngagementContext

        engagement_id = f"eng_complex_{datetime.utcnow().timestamp()}"
        context = EngagementContext(
            engagement_id=engagement_id,
            redis_client=redis_client
        )

        complex_value = {
            "sources": [
                {"name": "db1", "type": "postgres", "tables": ["users", "orders"]},
                {"name": "api1", "type": "rest", "endpoints": ["/users", "/products"]}
            ],
            "requirements": {
                "functional": ["REQ-001", "REQ-002"],
                "non_functional": ["NFR-001"]
            },
            "metadata": {
                "created_at": "2024-01-15T10:00:00Z",
                "version": 1
            }
        }

        await context.set("discovery_results", complex_value)

        retrieved = await context.get("discovery_results")

        assert retrieved["sources"][0]["name"] == "db1"
        assert len(retrieved["requirements"]["functional"]) == 2


class TestStatePersistenceIntegration:
    """Integration tests for state persistence with agent workflow."""

    @pytest.mark.asyncio
    async def test_agent_with_redis_persistence(self, redis_client, mock_llm):
        """Test agent workflow with Redis state persistence."""
        from agent_framework.memory import RedisMemorySaver
        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState
        from contracts.agent_interface import AgentInput
        from langgraph.graph import StateGraph, END
        from typing import List

        class PersistentAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "persistent_agent"

            @property
            def description(self) -> str:
                return "Agent with persistent state"

            @property
            def required_inputs(self) -> List[str]:
                return []

            @property
            def output_keys(self) -> List[str]:
                return ["result"]

            def get_system_prompt(self) -> str:
                return "You are an agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def process(state: AgentState) -> Dict[str, Any]:
                    return {
                        "outputs": {"result": "persisted"},
                        "current_step": "done"
                    }

                graph.add_node("process", process)
                graph.set_entry_point("process")
                graph.add_edge("process", END)

                return graph

        memory_saver = RedisMemorySaver(redis_client=redis_client)
        agent = PersistentAgent(llm=mock_llm, memory=memory_saver)

        engagement_id = f"persist_eng_{datetime.utcnow().timestamp()}"

        input_data = AgentInput(
            engagement_id=engagement_id,
            phase="test",
            context={}
        )

        output = await agent.run(input_data)

        assert output.success is True

        # Verify checkpoint was saved
        config = {"configurable": {"thread_id": engagement_id}}
        checkpoint = await memory_saver.aget(config)

        assert checkpoint is not None

    @pytest.mark.asyncio
    async def test_state_recovery_after_interruption(self, redis_client, mock_llm):
        """Test recovering state after simulated interruption."""
        from agent_framework.memory import RedisMemorySaver, ConversationMemory

        thread_id = f"recovery_test_{datetime.utcnow().timestamp()}"

        # First session: save state
        memory = ConversationMemory(redis_client=redis_client)
        await memory.add_message(thread_id, "user", "Step 1 complete")
        await memory.add_message(thread_id, "assistant", "Acknowledged step 1")

        # Simulate "interruption" - create new memory instance
        memory2 = ConversationMemory(redis_client=redis_client)

        # Should recover previous messages
        messages = await memory2.get_messages(thread_id)

        assert len(messages) == 2
        assert messages[0]["content"] == "Step 1 complete"
