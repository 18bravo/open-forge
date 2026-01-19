"""
Agent Registry module for discovering and instantiating agents.
"""
from orchestration.registry.agent_registry import (
    AgentRegistry,
    register_agent,
    get_registry,
    AgentMetadata,
)

__all__ = [
    "AgentRegistry",
    "register_agent",
    "get_registry",
    "AgentMetadata",
]
