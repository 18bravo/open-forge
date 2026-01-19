"""
Open Forge Agent Memory System

This module provides memory capabilities for agents:
- Long-term memory: Cross-thread semantic search via PostgresStore + pgvector
- Short-term memory: Within-thread checkpoints via PostgresSaver (use directly from LangGraph)

Example usage:
    from agent_framework.memory import EngagementMemoryStore, MemoryTypes

    # Initialize the store
    store = EngagementMemoryStore(connection_string)

    # Store a memory
    key = await store.store_memory(
        engagement_id="eng_123",
        memory_type=MemoryTypes.STAKEHOLDER,
        content={"name": "John", "role": "CTO"}
    )

    # Search memories
    results = await store.search_memories(
        engagement_id="eng_123",
        query="executive stakeholders",
        memory_types=[MemoryTypes.STAKEHOLDER]
    )
"""
from agent_framework.memory.long_term import (
    EngagementMemoryStore,
    MemoryTypes,
)

__all__ = [
    "EngagementMemoryStore",
    "MemoryTypes",
]
