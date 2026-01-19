"""
Open Forge Custom Langflow Components

This package provides custom Langflow components that wrap Open Forge
agent clusters and tools for visual workflow design.

Components:
- Agents: Discovery, Data Architect, App Builder agent wrappers
- Tools: Ontology queries, pipeline triggers
- Memory: PostgresStore integration

These components enable the "AI-generates, user-refines" paradigm
by allowing visual editing of AI-generated agent workflows.
"""

from langflow_components.agents import (
    DiscoveryAgentComponent,
    DataArchitectAgentComponent,
    AppBuilderAgentComponent,
)
from langflow_components.tools import (
    OntologyToolComponent,
    PipelineToolComponent,
)
from langflow_components.memory import (
    PostgresMemoryComponent,
)

__version__ = "0.1.0"

__all__ = [
    # Agent components
    "DiscoveryAgentComponent",
    "DataArchitectAgentComponent",
    "AppBuilderAgentComponent",
    # Tool components
    "OntologyToolComponent",
    "PipelineToolComponent",
    # Memory components
    "PostgresMemoryComponent",
]

# Langflow component registration
# These are automatically discovered by Langflow when the package is installed
LANGFLOW_COMPONENTS = [
    DiscoveryAgentComponent,
    DataArchitectAgentComponent,
    AppBuilderAgentComponent,
    OntologyToolComponent,
    PipelineToolComponent,
    PostgresMemoryComponent,
]
