"""
Open Forge Agent Framework

LangGraph-based multi-agent system for autonomous FDE operations.
"""
from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
from agent_framework.state_management import (
    AgentState,
    DiscoveryState,
    DataArchitectState,
    AppBuilderState,
    create_initial_state,
    add_decision,
    mark_for_review,
)
from agent_framework.graph_builder import WorkflowBuilder, create_approval_subgraph
from agent_framework.memory import RedisMemorySaver, ConversationMemory, EngagementContext
from agent_framework.prompts import PromptTemplate, PromptLibrary

__all__ = [
    # Base classes
    "BaseOpenForgeAgent",
    "NodeBuilder",
    # State management
    "AgentState",
    "DiscoveryState",
    "DataArchitectState",
    "AppBuilderState",
    "create_initial_state",
    "add_decision",
    "mark_for_review",
    # Graph building
    "WorkflowBuilder",
    "create_approval_subgraph",
    # Memory
    "RedisMemorySaver",
    "ConversationMemory",
    "EngagementContext",
    # Prompts
    "PromptTemplate",
    "PromptLibrary",
]
