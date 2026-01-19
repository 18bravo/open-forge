"""
Agent Registry for discovering and instantiating Open Forge agents.

This module provides a central registry for all specialist agents,
supporting decorator-based registration and dynamic instantiation.
"""
from typing import Dict, Any, List, Optional, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentCategory(str, Enum):
    """Categories of agents in Open Forge."""
    DISCOVERY = "discovery"
    DATA_ARCHITECT = "data_architect"
    APP_BUILDER = "app_builder"
    OPERATIONS = "operations"
    ENABLEMENT = "enablement"
    ORCHESTRATOR = "orchestrator"
    UTILITY = "utility"


@dataclass
class AgentMetadata:
    """Metadata for a registered agent."""
    name: str
    agent_class: Type
    category: AgentCategory
    description: str
    version: str = "1.0.0"
    required_inputs: List[str] = field(default_factory=list)
    output_keys: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    is_react_agent: bool = False
    is_memory_aware: bool = False


class AgentRegistry:
    """
    Central registry for Open Forge agents.

    Supports:
    - Decorator-based agent registration
    - Agent discovery by name, category, or capability
    - Dynamic agent instantiation with configuration
    - Agent metadata queries

    Example:
        registry = AgentRegistry()

        @registry.register(
            name="discovery_react",
            category=AgentCategory.DISCOVERY,
            description="Discovery agent using ReAct pattern"
        )
        class DiscoveryReActAgent(MemoryAwareAgent):
            ...

        # Get agent class
        agent_cls = registry.get("discovery_react")

        # Instantiate with config
        agent = registry.instantiate(
            "discovery_react",
            llm=my_llm,
            checkpointer=checkpointer,
            store=store,
            engagement_id="eng_123"
        )
    """

    _instance: Optional["AgentRegistry"] = None

    def __new__(cls) -> "AgentRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents: Dict[str, AgentMetadata] = {}
            cls._instance._factories: Dict[str, Callable] = {}
        return cls._instance

    def register(
        self,
        name: str,
        category: AgentCategory,
        description: str,
        version: str = "1.0.0",
        required_inputs: Optional[List[str]] = None,
        output_keys: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        is_react_agent: bool = False,
        is_memory_aware: bool = False,
    ) -> Callable:
        """
        Decorator for registering an agent class.

        Args:
            name: Unique name for the agent
            category: Agent category for grouping
            description: Human-readable description
            version: Agent version string
            required_inputs: List of required input keys
            output_keys: List of output keys produced
            capabilities: List of capability tags
            dependencies: List of dependent agent names
            is_react_agent: Whether this uses ReAct pattern
            is_memory_aware: Whether this uses memory tools

        Returns:
            Decorator function

        Example:
            @registry.register(
                name="my_agent",
                category=AgentCategory.DISCOVERY,
                description="My custom agent"
            )
            class MyAgent(MemoryAwareAgent):
                ...
        """
        def decorator(cls: Type) -> Type:
            metadata = AgentMetadata(
                name=name,
                agent_class=cls,
                category=category,
                description=description,
                version=version,
                required_inputs=required_inputs or [],
                output_keys=output_keys or [],
                capabilities=capabilities or [],
                dependencies=dependencies or [],
                is_react_agent=is_react_agent,
                is_memory_aware=is_memory_aware,
            )

            self._agents[name] = metadata
            logger.info(f"Registered agent: {name} (category={category.value})")

            return cls

        return decorator

    def register_factory(
        self,
        name: str,
        factory: Callable,
        category: AgentCategory,
        description: str,
        **metadata_kwargs,
    ) -> None:
        """
        Register an agent factory function.

        Use this for agents that need custom instantiation logic.

        Args:
            name: Unique name for the agent
            factory: Factory function that creates agent instances
            category: Agent category
            description: Human-readable description
            **metadata_kwargs: Additional metadata fields
        """
        # Store factory separately
        self._factories[name] = factory

        # Create metadata with placeholder class
        metadata = AgentMetadata(
            name=name,
            agent_class=type(f"{name}_Factory", (), {}),  # Placeholder
            category=category,
            description=description,
            **metadata_kwargs,
        )
        self._agents[name] = metadata

        logger.info(f"Registered agent factory: {name}")

    def get(self, name: str) -> Optional[Type]:
        """
        Get an agent class by name.

        Args:
            name: The agent name

        Returns:
            The agent class or None if not found
        """
        metadata = self._agents.get(name)
        if metadata:
            return metadata.agent_class
        return None

    def get_metadata(self, name: str) -> Optional[AgentMetadata]:
        """
        Get agent metadata by name.

        Args:
            name: The agent name

        Returns:
            AgentMetadata or None if not found
        """
        return self._agents.get(name)

    def instantiate(
        self,
        name: str,
        **kwargs,
    ) -> Any:
        """
        Instantiate an agent by name with provided configuration.

        Args:
            name: The agent name
            **kwargs: Configuration passed to agent constructor

        Returns:
            Instantiated agent

        Raises:
            KeyError: If agent name is not registered
        """
        if name not in self._agents:
            raise KeyError(f"Agent not registered: {name}")

        # Check for factory first
        if name in self._factories:
            return self._factories[name](**kwargs)

        # Otherwise use class constructor
        agent_cls = self._agents[name].agent_class
        return agent_cls(**kwargs)

    def list_agents(
        self,
        category: Optional[AgentCategory] = None,
        capability: Optional[str] = None,
        react_only: bool = False,
        memory_aware_only: bool = False,
    ) -> List[AgentMetadata]:
        """
        List registered agents with optional filtering.

        Args:
            category: Filter by category
            capability: Filter by capability tag
            react_only: Only return ReAct agents
            memory_aware_only: Only return memory-aware agents

        Returns:
            List of matching AgentMetadata
        """
        results = []

        for metadata in self._agents.values():
            # Apply filters
            if category and metadata.category != category:
                continue
            if capability and capability not in metadata.capabilities:
                continue
            if react_only and not metadata.is_react_agent:
                continue
            if memory_aware_only and not metadata.is_memory_aware:
                continue

            results.append(metadata)

        return results

    def list_by_category(self) -> Dict[AgentCategory, List[AgentMetadata]]:
        """
        List agents grouped by category.

        Returns:
            Dict mapping categories to lists of agent metadata
        """
        result: Dict[AgentCategory, List[AgentMetadata]] = {}

        for metadata in self._agents.values():
            if metadata.category not in result:
                result[metadata.category] = []
            result[metadata.category].append(metadata)

        return result

    def get_dependencies(self, name: str) -> List[str]:
        """
        Get the dependency chain for an agent.

        Args:
            name: The agent name

        Returns:
            List of dependent agent names in dependency order
        """
        if name not in self._agents:
            return []

        visited = set()
        result = []

        def visit(agent_name: str):
            if agent_name in visited:
                return
            visited.add(agent_name)

            metadata = self._agents.get(agent_name)
            if metadata:
                for dep in metadata.dependencies:
                    visit(dep)
                result.append(agent_name)

        visit(name)
        return result[:-1]  # Exclude the agent itself

    def to_dict(self) -> Dict[str, Any]:
        """
        Export registry as a dictionary.

        Returns:
            Dict representation of all registered agents
        """
        return {
            name: {
                "category": meta.category.value,
                "description": meta.description,
                "version": meta.version,
                "required_inputs": meta.required_inputs,
                "output_keys": meta.output_keys,
                "capabilities": meta.capabilities,
                "dependencies": meta.dependencies,
                "is_react_agent": meta.is_react_agent,
                "is_memory_aware": meta.is_memory_aware,
            }
            for name, meta in self._agents.items()
        }

    def clear(self) -> None:
        """Clear all registered agents (useful for testing)."""
        self._agents.clear()
        self._factories.clear()


# Global registry instance
_global_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.

    Returns:
        The global AgentRegistry singleton
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


def register_agent(
    name: str,
    category: AgentCategory,
    description: str,
    **kwargs,
) -> Callable:
    """
    Convenience decorator for registering with the global registry.

    Args:
        name: Unique name for the agent
        category: Agent category
        description: Human-readable description
        **kwargs: Additional metadata fields

    Returns:
        Decorator function

    Example:
        @register_agent(
            name="discovery_react",
            category=AgentCategory.DISCOVERY,
            description="Discovery agent using ReAct pattern",
            is_react_agent=True,
            is_memory_aware=True
        )
        class DiscoveryReActAgent(MemoryAwareAgent):
            ...
    """
    registry = get_registry()
    return registry.register(name, category, description, **kwargs)
