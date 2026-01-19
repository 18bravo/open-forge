"""
Open Forge Agent Tools

Reusable tools for agent capabilities, including MCP adapter support
for extensible tool integration.
"""
from agent_framework.tools.base import (
    create_tool,
    WebSearchInput,
    FileReadInput,
    FileWriteInput,
    CodeExecutionInput,
)

from agent_framework.tools.mcp_adapter import (
    MCPToolProvider,
    MCPServerConnection,
)

from agent_framework.tools.mcp_registry import (
    MCPServerType,
    MCPServerConfig,
    MCPRegistry,
    get_registry,
    reset_registry,
    DEFAULT_FILESYSTEM_CONFIG,
    DEFAULT_POSTGRES_CONFIG,
    DEFAULT_GITHUB_CONFIG,
    DEFAULT_OPEN_FORGE_CONFIG,
)

__all__ = [
    # Base tools
    "create_tool",
    "WebSearchInput",
    "FileReadInput",
    "FileWriteInput",
    "CodeExecutionInput",
    # MCP Adapter
    "MCPToolProvider",
    "MCPServerConnection",
    # MCP Registry
    "MCPServerType",
    "MCPServerConfig",
    "MCPRegistry",
    "get_registry",
    "reset_registry",
    "DEFAULT_FILESYSTEM_CONFIG",
    "DEFAULT_POSTGRES_CONFIG",
    "DEFAULT_GITHUB_CONFIG",
    "DEFAULT_OPEN_FORGE_CONFIG",
]
