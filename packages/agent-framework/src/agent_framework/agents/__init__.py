"""
Open Forge Agent Classes

This module provides base classes for building agents:
- MemoryAwareAgent: Base class for agents with long-term memory capabilities
- SimpleMemoryAwareAgent: Ready-to-use agent with memory and optional custom tools

Example usage:
    from agent_framework.agents import MemoryAwareAgent, SimpleMemoryAwareAgent
    from langchain_anthropic import ChatAnthropic
    from langgraph.checkpoint.postgres import PostgresSaver
    from langgraph.store.postgres import PostgresStore

    # Create a simple agent
    agent = SimpleMemoryAwareAgent(
        llm=ChatAnthropic(model="claude-sonnet-4-20250514"),
        checkpointer=PostgresSaver.from_conn_string(conn_str),
        store=PostgresStore.from_conn_string(conn_str),
        engagement_id="eng_123",
        agent_id="helper_agent",
        system_prompt="You are a helpful assistant..."
    )

    # Run the agent
    result = await agent.run("What do we know about the stakeholders?", thread_id="t1")
"""
from agent_framework.agents.base_memory_agent import (
    MemoryAwareAgent,
    SimpleMemoryAwareAgent,
)

__all__ = [
    "MemoryAwareAgent",
    "SimpleMemoryAwareAgent",
]
