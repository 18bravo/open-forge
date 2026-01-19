"""
Integration tests for MCP Tool Provider.

Tests the MCPToolProvider class for connecting to MCP servers
and retrieving tools.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent_framework.tools.mcp_adapter import (
    MCPToolProvider,
    MCPServerConnection,
)


class TestMCPServerConnection:
    """Tests for MCPServerConnection model."""

    def test_create_connection(self):
        """Test creating a server connection configuration."""
        connection = MCPServerConnection(
            server_name="test-server",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-test"],
            env={"TEST_VAR": "value"},
        )

        assert connection.server_name == "test-server"
        assert connection.command == "npx"
        assert connection.args == ["-y", "@modelcontextprotocol/server-test"]
        assert connection.env == {"TEST_VAR": "value"}
        assert connection.toolkit is None

    def test_connection_with_defaults(self):
        """Test connection with default values."""
        connection = MCPServerConnection(
            server_name="minimal",
            command="python",
        )

        assert connection.args == []
        assert connection.env == {}


class TestMCPToolProvider:
    """Tests for MCPToolProvider class."""

    def test_init(self):
        """Test provider initialization."""
        provider = MCPToolProvider()

        assert provider._connections == {}
        assert provider._tools == {}
        assert provider.connection_count == 0
        assert provider.tool_count == 0

    @pytest.mark.asyncio
    async def test_connect_server_success(self):
        """Test successful server connection."""
        provider = MCPToolProvider()

        mock_toolkit = MagicMock()
        mock_toolkit.initialize = AsyncMock()
        mock_toolkit.get_tools = MagicMock(return_value=[MagicMock(), MagicMock()])

        with patch(
            "agent_framework.tools.mcp_adapter.MCPToolkit",
            return_value=mock_toolkit,
        ):
            tools = await provider.connect_server(
                server_name="test",
                command="npx",
                args=["-y", "test-server"],
            )

        assert len(tools) == 2
        assert provider.is_connected("test")
        assert provider.connection_count == 1
        mock_toolkit.initialize.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_server_duplicate_raises_error(self):
        """Test connecting to already connected server raises error."""
        provider = MCPToolProvider()

        mock_toolkit = MagicMock()
        mock_toolkit.initialize = AsyncMock()
        mock_toolkit.get_tools = MagicMock(return_value=[])

        with patch(
            "agent_framework.tools.mcp_adapter.MCPToolkit",
            return_value=mock_toolkit,
        ):
            await provider.connect_server("test", "npx", [])

            with pytest.raises(ValueError, match="already connected"):
                await provider.connect_server("test", "npx", [])

    @pytest.mark.asyncio
    async def test_connect_server_failure(self):
        """Test server connection failure raises ConnectionError."""
        provider = MCPToolProvider()

        mock_toolkit = MagicMock()
        mock_toolkit.initialize = AsyncMock(side_effect=Exception("Connection failed"))

        with patch(
            "agent_framework.tools.mcp_adapter.MCPToolkit",
            return_value=mock_toolkit,
        ):
            with pytest.raises(ConnectionError, match="Failed to connect"):
                await provider.connect_server("test", "npx", [])

    @pytest.mark.asyncio
    async def test_connect_filesystem(self):
        """Test filesystem convenience method."""
        provider = MCPToolProvider()

        mock_toolkit = MagicMock()
        mock_toolkit.initialize = AsyncMock()
        mock_toolkit.get_tools = MagicMock(return_value=[MagicMock()])

        with patch(
            "agent_framework.tools.mcp_adapter.MCPToolkit",
            return_value=mock_toolkit,
        ) as mock_class:
            await provider.connect_filesystem(["/tmp", "/home"])

            # Verify the correct args were passed
            call_kwargs = mock_class.call_args.kwargs
            assert "-y" in call_kwargs["args"]
            assert "@modelcontextprotocol/server-filesystem" in call_kwargs["args"]
            assert "/tmp" in call_kwargs["args"]
            assert "/home" in call_kwargs["args"]

    @pytest.mark.asyncio
    async def test_connect_postgres(self):
        """Test postgres convenience method."""
        provider = MCPToolProvider()

        mock_toolkit = MagicMock()
        mock_toolkit.initialize = AsyncMock()
        mock_toolkit.get_tools = MagicMock(return_value=[MagicMock()])

        with patch(
            "agent_framework.tools.mcp_adapter.MCPToolkit",
            return_value=mock_toolkit,
        ) as mock_class:
            await provider.connect_postgres("postgresql://localhost/test")

            call_kwargs = mock_class.call_args.kwargs
            assert "POSTGRES_CONNECTION_STRING" in call_kwargs["env"]
            assert call_kwargs["env"]["POSTGRES_CONNECTION_STRING"] == "postgresql://localhost/test"

    @pytest.mark.asyncio
    async def test_connect_github(self):
        """Test github convenience method."""
        provider = MCPToolProvider()

        mock_toolkit = MagicMock()
        mock_toolkit.initialize = AsyncMock()
        mock_toolkit.get_tools = MagicMock(return_value=[MagicMock()])

        with patch(
            "agent_framework.tools.mcp_adapter.MCPToolkit",
            return_value=mock_toolkit,
        ) as mock_class:
            await provider.connect_github("ghp_test_token")

            call_kwargs = mock_class.call_args.kwargs
            assert "GITHUB_PERSONAL_ACCESS_TOKEN" in call_kwargs["env"]
            assert call_kwargs["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "ghp_test_token"

    @pytest.mark.asyncio
    async def test_get_tools_from_server(self):
        """Test getting tools from a specific server."""
        provider = MCPToolProvider()

        mock_tools = [MagicMock(), MagicMock()]
        mock_toolkit = MagicMock()
        mock_toolkit.initialize = AsyncMock()
        mock_toolkit.get_tools = MagicMock(return_value=mock_tools)

        with patch(
            "agent_framework.tools.mcp_adapter.MCPToolkit",
            return_value=mock_toolkit,
        ):
            await provider.connect_server("test", "npx", [])

        tools = provider.get_tools("test")
        assert tools == mock_tools

    def test_get_tools_not_connected(self):
        """Test getting tools from non-existent server raises error."""
        provider = MCPToolProvider()

        with pytest.raises(KeyError, match="not connected"):
            provider.get_tools("nonexistent")

    @pytest.mark.asyncio
    async def test_get_all_tools(self):
        """Test getting all tools from all servers."""
        provider = MCPToolProvider()

        mock_toolkit1 = MagicMock()
        mock_toolkit1.initialize = AsyncMock()
        mock_toolkit1.get_tools = MagicMock(return_value=[MagicMock()])

        mock_toolkit2 = MagicMock()
        mock_toolkit2.initialize = AsyncMock()
        mock_toolkit2.get_tools = MagicMock(return_value=[MagicMock(), MagicMock()])

        toolkits = [mock_toolkit1, mock_toolkit2]
        toolkit_index = [0]

        def get_toolkit(*args, **kwargs):
            toolkit = toolkits[toolkit_index[0]]
            toolkit_index[0] += 1
            return toolkit

        with patch(
            "agent_framework.tools.mcp_adapter.MCPToolkit",
            side_effect=get_toolkit,
        ):
            await provider.connect_server("server1", "npx", [])
            await provider.connect_server("server2", "npx", [])

        all_tools = provider.get_all_tools()
        assert len(all_tools) == 3
        assert provider.tool_count == 3

    def test_list_servers(self):
        """Test listing connected servers."""
        provider = MCPToolProvider()
        provider._connections = {
            "server1": MagicMock(),
            "server2": MagicMock(),
        }

        servers = provider.list_servers()
        assert "server1" in servers
        assert "server2" in servers

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from a server."""
        provider = MCPToolProvider()

        mock_toolkit = MagicMock()
        mock_toolkit.initialize = AsyncMock()
        mock_toolkit.get_tools = MagicMock(return_value=[])
        mock_toolkit.close = AsyncMock()

        with patch(
            "agent_framework.tools.mcp_adapter.MCPToolkit",
            return_value=mock_toolkit,
        ):
            await provider.connect_server("test", "npx", [])
            assert provider.is_connected("test")

            await provider.disconnect("test")
            assert not provider.is_connected("test")

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self):
        """Test disconnecting non-existent server raises error."""
        provider = MCPToolProvider()

        with pytest.raises(KeyError, match="not connected"):
            await provider.disconnect("nonexistent")

    @pytest.mark.asyncio
    async def test_disconnect_all(self):
        """Test disconnecting all servers."""
        provider = MCPToolProvider()

        mock_toolkit = MagicMock()
        mock_toolkit.initialize = AsyncMock()
        mock_toolkit.get_tools = MagicMock(return_value=[])

        toolkits = [MagicMock(), MagicMock()]
        for t in toolkits:
            t.initialize = AsyncMock()
            t.get_tools = MagicMock(return_value=[])

        toolkit_index = [0]

        def get_toolkit(*args, **kwargs):
            toolkit = toolkits[toolkit_index[0]]
            toolkit_index[0] += 1
            return toolkit

        with patch(
            "agent_framework.tools.mcp_adapter.MCPToolkit",
            side_effect=get_toolkit,
        ):
            await provider.connect_server("server1", "npx", [])
            await provider.connect_server("server2", "npx", [])

        assert provider.connection_count == 2

        await provider.disconnect_all()
        assert provider.connection_count == 0

    @pytest.mark.asyncio
    async def test_session_context_manager(self):
        """Test session context manager for automatic cleanup."""
        mock_toolkit = MagicMock()
        mock_toolkit.initialize = AsyncMock()
        mock_toolkit.get_tools = MagicMock(return_value=[])

        provider = MCPToolProvider()

        with patch(
            "agent_framework.tools.mcp_adapter.MCPToolkit",
            return_value=mock_toolkit,
        ):
            async with provider.session():
                await provider.connect_server("test", "npx", [])
                assert provider.connection_count == 1

        # After context exits, should be cleaned up
        assert provider.connection_count == 0

    def test_is_connected(self):
        """Test is_connected method."""
        provider = MCPToolProvider()
        provider._connections["test"] = MagicMock()

        assert provider.is_connected("test")
        assert not provider.is_connected("other")
