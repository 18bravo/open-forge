"""
MCP Server Registry for Open Forge.

Provides configuration management and discovery for MCP servers,
allowing dynamic registration and lookup of available MCP tools.
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MCPServerType(str, Enum):
    """Types of MCP servers."""

    FILESYSTEM = "filesystem"
    POSTGRES = "postgres"
    GITHUB = "github"
    OPEN_FORGE = "open-forge"
    CUSTOM = "custom"


class MCPServerConfig(BaseModel):
    """
    Configuration for an MCP server.

    Attributes:
        name: Unique identifier for the server
        server_type: Type of MCP server
        command: Command to start the server
        args: Command arguments
        env: Environment variables
        enabled: Whether the server is enabled
        description: Human-readable description
        required_env_vars: List of required environment variables
    """

    name: str = Field(description="Unique identifier for the server")
    server_type: MCPServerType = Field(description="Type of MCP server")
    command: str = Field(description="Command to start the server")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    enabled: bool = Field(default=True, description="Whether the server is enabled")
    description: str = Field(default="", description="Human-readable description")
    required_env_vars: list[str] = Field(
        default_factory=list,
        description="List of required environment variables that must be set"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate server name is not empty and contains valid characters."""
        if not v or not v.strip():
            raise ValueError("Server name cannot be empty")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Server name must be alphanumeric with optional hyphens/underscores")
        return v.strip().lower()

    def is_ready(self, env_vars: Optional[dict[str, str]] = None) -> bool:
        """
        Check if all required environment variables are available.

        Args:
            env_vars: Optional dictionary of environment variables to check against

        Returns:
            True if all required variables are set
        """
        import os
        check_env = env_vars or {}

        for var in self.required_env_vars:
            if var not in check_env and var not in os.environ:
                return False
        return True


# Default server configurations
DEFAULT_FILESYSTEM_CONFIG = MCPServerConfig(
    name="filesystem",
    server_type=MCPServerType.FILESYSTEM,
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem"],
    description="MCP server for filesystem operations (read, write, list files)",
    enabled=True,
)

DEFAULT_POSTGRES_CONFIG = MCPServerConfig(
    name="postgres",
    server_type=MCPServerType.POSTGRES,
    command="npx",
    args=["-y", "@modelcontextprotocol/server-postgres"],
    description="MCP server for PostgreSQL database operations",
    required_env_vars=["POSTGRES_CONNECTION_STRING"],
    enabled=True,
)

DEFAULT_GITHUB_CONFIG = MCPServerConfig(
    name="github",
    server_type=MCPServerType.GITHUB,
    command="npx",
    args=["-y", "@modelcontextprotocol/server-github"],
    description="MCP server for GitHub API operations",
    required_env_vars=["GITHUB_PERSONAL_ACCESS_TOKEN"],
    enabled=True,
)

DEFAULT_OPEN_FORGE_CONFIG = MCPServerConfig(
    name="open-forge",
    server_type=MCPServerType.OPEN_FORGE,
    command="python",
    args=["-m", "mcp_server.open_forge_mcp"],
    description="Open Forge native MCP server for ontology, pipeline, and codegen operations",
    enabled=True,
)


class MCPRegistry:
    """
    Registry for MCP server configurations.

    Manages registration, lookup, and listing of MCP server configurations.
    Pre-configured with common MCP servers (filesystem, postgres, github, open-forge).

    Example usage:
        >>> registry = MCPRegistry()
        >>> config = registry.get("filesystem")
        >>> enabled_servers = registry.list_enabled()
    """

    # Default servers that are pre-registered
    DEFAULT_SERVERS: list[MCPServerConfig] = [
        DEFAULT_FILESYSTEM_CONFIG,
        DEFAULT_POSTGRES_CONFIG,
        DEFAULT_GITHUB_CONFIG,
        DEFAULT_OPEN_FORGE_CONFIG,
    ]

    def __init__(self, include_defaults: bool = True):
        """
        Initialize the MCP registry.

        Args:
            include_defaults: Whether to include default server configurations
        """
        self._configs: dict[str, MCPServerConfig] = {}

        if include_defaults:
            for config in self.DEFAULT_SERVERS:
                self._configs[config.name] = config

    def register(self, config: MCPServerConfig) -> None:
        """
        Register an MCP server configuration.

        Args:
            config: Server configuration to register

        Raises:
            ValueError: If a server with the same name already exists
        """
        if config.name in self._configs:
            raise ValueError(
                f"Server '{config.name}' is already registered. "
                "Use update() to modify existing configurations."
            )
        self._configs[config.name] = config

    def update(self, config: MCPServerConfig) -> None:
        """
        Update an existing MCP server configuration.

        Args:
            config: Server configuration to update

        Raises:
            KeyError: If the server is not registered
        """
        if config.name not in self._configs:
            raise KeyError(f"Server '{config.name}' is not registered")
        self._configs[config.name] = config

    def unregister(self, name: str) -> None:
        """
        Remove an MCP server configuration.

        Args:
            name: Name of the server to remove

        Raises:
            KeyError: If the server is not registered
        """
        if name not in self._configs:
            raise KeyError(f"Server '{name}' is not registered")
        del self._configs[name]

    def get(self, name: str) -> MCPServerConfig:
        """
        Get an MCP server configuration by name.

        Args:
            name: Name of the server

        Returns:
            Server configuration

        Raises:
            KeyError: If the server is not registered
        """
        if name not in self._configs:
            raise KeyError(f"Server '{name}' is not registered")
        return self._configs[name]

    def get_optional(self, name: str) -> Optional[MCPServerConfig]:
        """
        Get an MCP server configuration by name, returning None if not found.

        Args:
            name: Name of the server

        Returns:
            Server configuration or None
        """
        return self._configs.get(name)

    def list_all(self) -> list[MCPServerConfig]:
        """
        List all registered server configurations.

        Returns:
            List of all server configurations
        """
        return list(self._configs.values())

    def list_enabled(self) -> list[MCPServerConfig]:
        """
        List all enabled server configurations.

        Returns:
            List of enabled server configurations
        """
        return [config for config in self._configs.values() if config.enabled]

    def list_ready(self, env_vars: Optional[dict[str, str]] = None) -> list[MCPServerConfig]:
        """
        List all enabled servers that have their required environment variables set.

        Args:
            env_vars: Optional dictionary of environment variables to check

        Returns:
            List of ready server configurations
        """
        return [
            config for config in self._configs.values()
            if config.enabled and config.is_ready(env_vars)
        ]

    def list_by_type(self, server_type: MCPServerType) -> list[MCPServerConfig]:
        """
        List all servers of a specific type.

        Args:
            server_type: Type of server to filter by

        Returns:
            List of matching server configurations
        """
        return [
            config for config in self._configs.values()
            if config.server_type == server_type
        ]

    def enable(self, name: str) -> None:
        """
        Enable a server by name.

        Args:
            name: Name of the server to enable

        Raises:
            KeyError: If the server is not registered
        """
        config = self.get(name)
        config.enabled = True
        self._configs[name] = config

    def disable(self, name: str) -> None:
        """
        Disable a server by name.

        Args:
            name: Name of the server to disable

        Raises:
            KeyError: If the server is not registered
        """
        config = self.get(name)
        config.enabled = False
        self._configs[name] = config

    def is_registered(self, name: str) -> bool:
        """Check if a server is registered."""
        return name in self._configs

    @property
    def count(self) -> int:
        """Get the number of registered servers."""
        return len(self._configs)

    @property
    def enabled_count(self) -> int:
        """Get the number of enabled servers."""
        return len(self.list_enabled())

    def to_dict(self) -> dict[str, dict]:
        """
        Export all configurations as a dictionary.

        Returns:
            Dictionary of server configurations
        """
        return {name: config.model_dump() for name, config in self._configs.items()}

    @classmethod
    def from_dict(cls, data: dict[str, dict], include_defaults: bool = False) -> "MCPRegistry":
        """
        Create a registry from a dictionary of configurations.

        Args:
            data: Dictionary of server configurations
            include_defaults: Whether to include default configurations

        Returns:
            New MCPRegistry instance
        """
        registry = cls(include_defaults=include_defaults)
        for name, config_data in data.items():
            config = MCPServerConfig(**config_data)
            if registry.is_registered(config.name):
                registry.update(config)
            else:
                registry.register(config)
        return registry


# Global registry instance
_global_registry: Optional[MCPRegistry] = None


def get_registry() -> MCPRegistry:
    """
    Get the global MCP registry instance.

    Returns:
        Global registry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = MCPRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry to default state."""
    global _global_registry
    _global_registry = None
