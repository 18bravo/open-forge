"""
MCP Tool Provider for Open Forge.

Provides integration with Model Context Protocol (MCP) servers,
allowing agents to use any MCP-compatible tool server for extensible capabilities.
"""
import os
from typing import Any, Optional
from contextlib import asynccontextmanager

from langchain_core.tools import BaseTool
from langchain_mcp_adapters import MCPToolkit
from pydantic import BaseModel, Field


class MCPServerConnection(BaseModel):
    """Represents an active MCP server connection."""

    server_name: str = Field(description="Name of the MCP server")
    command: str = Field(description="Command to start the server")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    toolkit: Optional[Any] = Field(default=None, exclude=True, description="MCPToolkit instance")

    class Config:
        arbitrary_types_allowed = True


class MCPToolProvider:
    """
    Provider for MCP (Model Context Protocol) tools.

    Manages connections to MCP servers and provides a unified interface
    for accessing tools from multiple MCP-compatible sources.

    Example usage:
        >>> provider = MCPToolProvider()
        >>> await provider.connect_server("filesystem", "npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"])
        >>> tools = provider.get_all_tools()
        >>> await provider.disconnect_all()
    """

    def __init__(self):
        """Initialize the MCP tool provider."""
        self._connections: dict[str, MCPServerConnection] = {}
        self._tools: dict[str, list[BaseTool]] = {}

    async def connect_server(
        self,
        server_name: str,
        command: str,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
    ) -> list[BaseTool]:
        """
        Connect to an MCP server and retrieve its tools.

        Args:
            server_name: Unique name for this server connection
            command: Command to start the MCP server
            args: Command arguments
            env: Environment variables for the server process

        Returns:
            List of tools provided by the server

        Raises:
            ConnectionError: If connection to the server fails
            ValueError: If server_name is already connected
        """
        if server_name in self._connections:
            raise ValueError(f"Server '{server_name}' is already connected. Disconnect first.")

        try:
            toolkit = MCPToolkit(
                command=command,
                args=args or [],
                env=env or {},
            )
            await toolkit.initialize()
            tools = toolkit.get_tools()

            connection = MCPServerConnection(
                server_name=server_name,
                command=command,
                args=args or [],
                env=env or {},
                toolkit=toolkit,
            )

            self._connections[server_name] = connection
            self._tools[server_name] = tools

            return tools

        except Exception as e:
            raise ConnectionError(f"Failed to connect to MCP server '{server_name}': {e}") from e

    async def connect_filesystem(
        self,
        allowed_paths: list[str],
        server_name: str = "filesystem",
    ) -> list[BaseTool]:
        """
        Convenience method to connect to the filesystem MCP server.

        Args:
            allowed_paths: List of filesystem paths the server can access
            server_name: Optional custom name for the server

        Returns:
            List of filesystem tools
        """
        args = ["-y", "@modelcontextprotocol/server-filesystem"]
        args.extend(allowed_paths)

        return await self.connect_server(
            server_name=server_name,
            command="npx",
            args=args,
        )

    async def connect_postgres(
        self,
        connection_string: str,
        server_name: str = "postgres",
    ) -> list[BaseTool]:
        """
        Convenience method to connect to the PostgreSQL MCP server.

        Args:
            connection_string: PostgreSQL connection string
            server_name: Optional custom name for the server

        Returns:
            List of PostgreSQL tools
        """
        return await self.connect_server(
            server_name=server_name,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres"],
            env={"POSTGRES_CONNECTION_STRING": connection_string},
        )

    async def connect_github(
        self,
        token: str,
        server_name: str = "github",
    ) -> list[BaseTool]:
        """
        Convenience method to connect to the GitHub MCP server.

        Args:
            token: GitHub personal access token
            server_name: Optional custom name for the server

        Returns:
            List of GitHub tools
        """
        return await self.connect_server(
            server_name=server_name,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": token},
        )

    async def connect_open_forge(
        self,
        api_url: Optional[str] = None,
        server_name: str = "open-forge",
    ) -> list[BaseTool]:
        """
        Connect to the Open Forge MCP server.

        Args:
            api_url: Optional Open Forge API URL
            server_name: Optional custom name for the server

        Returns:
            List of Open Forge tools
        """
        env = {}
        if api_url:
            env["OPEN_FORGE_API_URL"] = api_url

        return await self.connect_server(
            server_name=server_name,
            command="python",
            args=["-m", "mcp_server.open_forge_mcp"],
            env=env,
        )

    def get_tools(self, server_name: str) -> list[BaseTool]:
        """
        Get tools from a specific server.

        Args:
            server_name: Name of the server

        Returns:
            List of tools from that server

        Raises:
            KeyError: If server is not connected
        """
        if server_name not in self._tools:
            raise KeyError(f"Server '{server_name}' is not connected")
        return self._tools[server_name]

    def get_all_tools(self) -> list[BaseTool]:
        """
        Get all tools from all connected servers.

        Returns:
            Combined list of all tools from all servers
        """
        all_tools = []
        for tools in self._tools.values():
            all_tools.extend(tools)
        return all_tools

    def list_servers(self) -> list[str]:
        """
        List all connected server names.

        Returns:
            List of connected server names
        """
        return list(self._connections.keys())

    async def disconnect(self, server_name: str) -> None:
        """
        Disconnect from a specific server.

        Args:
            server_name: Name of the server to disconnect

        Raises:
            KeyError: If server is not connected
        """
        if server_name not in self._connections:
            raise KeyError(f"Server '{server_name}' is not connected")

        connection = self._connections[server_name]
        if connection.toolkit:
            try:
                # MCPToolkit may have cleanup methods
                if hasattr(connection.toolkit, 'close'):
                    await connection.toolkit.close()
                elif hasattr(connection.toolkit, 'shutdown'):
                    await connection.toolkit.shutdown()
            except Exception:
                # Ignore cleanup errors
                pass

        del self._connections[server_name]
        del self._tools[server_name]

    async def disconnect_all(self) -> None:
        """Disconnect from all connected servers."""
        server_names = list(self._connections.keys())
        for server_name in server_names:
            try:
                await self.disconnect(server_name)
            except Exception:
                # Continue disconnecting other servers
                pass

    @asynccontextmanager
    async def session(self):
        """
        Context manager for automatic cleanup.

        Example:
            >>> async with provider.session():
            ...     await provider.connect_filesystem(["/tmp"])
            ...     tools = provider.get_all_tools()
            ...     # Use tools
            ... # Automatic cleanup
        """
        try:
            yield self
        finally:
            await self.disconnect_all()

    def is_connected(self, server_name: str) -> bool:
        """Check if a server is connected."""
        return server_name in self._connections

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)

    @property
    def tool_count(self) -> int:
        """Get the total number of available tools."""
        return sum(len(tools) for tools in self._tools.values())
