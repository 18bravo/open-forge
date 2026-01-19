"""
Open Forge Orchestration Package

Provides supervisor-based orchestration for coordinating specialist agents
using LangGraph's prebuilt patterns.
"""
from orchestration.supervisor_orchestrator import (
    SupervisorOrchestrator,
    create_supervisor_orchestrator,
)
from orchestration.registry.agent_registry import (
    AgentRegistry,
    register_agent,
    get_registry,
)

__all__ = [
    "SupervisorOrchestrator",
    "create_supervisor_orchestrator",
    "AgentRegistry",
    "register_agent",
    "get_registry",
]
