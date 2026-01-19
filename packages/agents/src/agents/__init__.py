"""
Open Forge Agents Package

Specialist agent implementations for autonomous FDE operations.

This package provides two styles of agents:
1. Cluster-based agents: Custom LangGraph workflows for complex multi-step processes
2. ReAct agents: LangGraph prebuilt create_react_agent pattern with memory support

ReAct agents are recommended for new implementations as they provide:
- Consistent reasoning + acting pattern
- Built-in memory tools (remember/recall)
- Easier maintenance and testing
- Integration with the SupervisorOrchestrator

Usage:
    # ReAct agents (recommended)
    from agents.discovery import DiscoveryReActAgent, create_discovery_react_agent
    from agents.data_architect import DataArchitectReActAgent
    from agents.app_builder import AppBuilderReActAgent
    from agents.operations import OperationsReActAgent
    from agents.enablement import EnablementReActAgent

    # Cluster agents (legacy)
    from agents.discovery import DiscoveryCluster
    from agents.data_architect import DataArchitectCluster
"""

__version__ = "0.1.0"

# ReAct agent imports
from agents.discovery.react_agent import (
    DiscoveryReActAgent,
    create_discovery_react_agent,
)
from agents.data_architect.react_agent import (
    DataArchitectReActAgent,
    create_data_architect_react_agent,
)
from agents.app_builder.react_agent import (
    AppBuilderReActAgent,
    create_app_builder_react_agent,
)
from agents.operations.react_agent import (
    OperationsReActAgent,
    create_operations_react_agent,
)
from agents.enablement.react_agent import (
    EnablementReActAgent,
    create_enablement_react_agent,
)

__all__ = [
    # ReAct agents
    "DiscoveryReActAgent",
    "create_discovery_react_agent",
    "DataArchitectReActAgent",
    "create_data_architect_react_agent",
    "AppBuilderReActAgent",
    "create_app_builder_react_agent",
    "OperationsReActAgent",
    "create_operations_react_agent",
    "EnablementReActAgent",
    "create_enablement_react_agent",
]
