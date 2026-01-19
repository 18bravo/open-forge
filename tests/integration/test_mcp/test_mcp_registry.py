"""
Integration tests for MCP Registry.

Tests the MCPRegistry class for server configuration management,
registration, lookup, and filtering.
"""
import os
import pytest
from unittest.mock import patch

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


class TestMCPServerConfig:
    """Tests for MCPServerConfig model."""

    def test_create_config(self):
        """Test creating a server configuration."""
        config = MCPServerConfig(
            name="test-server",
            server_type=MCPServerType.CUSTOM,
            command="python",
            args=["-m", "test_server"],
            env={"API_KEY": "test"},
            description="Test server",
        )

        assert config.name == "test-server"
        assert config.server_type == MCPServerType.CUSTOM
        assert config.command == "python"
        assert config.args == ["-m", "test_server"]
        assert config.env == {"API_KEY": "test"}
        assert config.description == "Test server"
        assert config.enabled is True

    def test_config_with_defaults(self):
        """Test configuration with default values."""
        config = MCPServerConfig(
            name="minimal",
            server_type=MCPServerType.CUSTOM,
            command="test",
        )

        assert config.args == []
        assert config.env == {}
        assert config.enabled is True
        assert config.description == ""
        assert config.required_env_vars == []

    def test_name_validation_empty(self):
        """Test that empty name raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            MCPServerConfig(
                name="",
                server_type=MCPServerType.CUSTOM,
                command="test",
            )

    def test_name_validation_whitespace(self):
        """Test that whitespace-only name raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            MCPServerConfig(
                name="   ",
                server_type=MCPServerType.CUSTOM,
                command="test",
            )

    def test_name_validation_special_chars(self):
        """Test that special characters in name raises error."""
        with pytest.raises(ValueError, match="alphanumeric"):
            MCPServerConfig(
                name="test@server",
                server_type=MCPServerType.CUSTOM,
                command="test",
            )

    def test_name_allows_hyphens_underscores(self):
        """Test that hyphens and underscores are allowed in names."""
        config = MCPServerConfig(
            name="test-server_v2",
            server_type=MCPServerType.CUSTOM,
            command="test",
        )
        assert config.name == "test-server_v2"

    def test_name_normalized_to_lowercase(self):
        """Test that name is normalized to lowercase."""
        config = MCPServerConfig(
            name="TEST-SERVER",
            server_type=MCPServerType.CUSTOM,
            command="test",
        )
        assert config.name == "test-server"

    def test_is_ready_no_required_vars(self):
        """Test is_ready when no required vars."""
        config = MCPServerConfig(
            name="test",
            server_type=MCPServerType.CUSTOM,
            command="test",
        )
        assert config.is_ready() is True

    def test_is_ready_with_env_dict(self):
        """Test is_ready with provided env dict."""
        config = MCPServerConfig(
            name="test",
            server_type=MCPServerType.CUSTOM,
            command="test",
            required_env_vars=["API_KEY"],
        )
        assert config.is_ready({"API_KEY": "value"}) is True
        assert config.is_ready({}) is False

    def test_is_ready_with_os_environ(self):
        """Test is_ready checks os.environ."""
        config = MCPServerConfig(
            name="test",
            server_type=MCPServerType.CUSTOM,
            command="test",
            required_env_vars=["TEST_VAR_FOR_MCP"],
        )

        # Not set
        assert config.is_ready() is False

        # Set via os.environ
        with patch.dict(os.environ, {"TEST_VAR_FOR_MCP": "value"}):
            assert config.is_ready() is True


class TestDefaultConfigs:
    """Tests for default server configurations."""

    def test_filesystem_config(self):
        """Test default filesystem configuration."""
        config = DEFAULT_FILESYSTEM_CONFIG
        assert config.name == "filesystem"
        assert config.server_type == MCPServerType.FILESYSTEM
        assert config.command == "npx"
        assert "@modelcontextprotocol/server-filesystem" in " ".join(config.args)

    def test_postgres_config(self):
        """Test default postgres configuration."""
        config = DEFAULT_POSTGRES_CONFIG
        assert config.name == "postgres"
        assert config.server_type == MCPServerType.POSTGRES
        assert "POSTGRES_CONNECTION_STRING" in config.required_env_vars

    def test_github_config(self):
        """Test default github configuration."""
        config = DEFAULT_GITHUB_CONFIG
        assert config.name == "github"
        assert config.server_type == MCPServerType.GITHUB
        assert "GITHUB_PERSONAL_ACCESS_TOKEN" in config.required_env_vars

    def test_open_forge_config(self):
        """Test default open-forge configuration."""
        config = DEFAULT_OPEN_FORGE_CONFIG
        assert config.name == "open-forge"
        assert config.server_type == MCPServerType.OPEN_FORGE
        assert config.command == "python"


class TestMCPRegistry:
    """Tests for MCPRegistry class."""

    def test_init_with_defaults(self):
        """Test registry initialization with defaults."""
        registry = MCPRegistry()

        assert registry.count == 4
        assert registry.is_registered("filesystem")
        assert registry.is_registered("postgres")
        assert registry.is_registered("github")
        assert registry.is_registered("open-forge")

    def test_init_without_defaults(self):
        """Test registry initialization without defaults."""
        registry = MCPRegistry(include_defaults=False)
        assert registry.count == 0

    def test_register(self):
        """Test registering a new server."""
        registry = MCPRegistry(include_defaults=False)

        config = MCPServerConfig(
            name="test",
            server_type=MCPServerType.CUSTOM,
            command="test",
        )
        registry.register(config)

        assert registry.is_registered("test")
        assert registry.count == 1

    def test_register_duplicate_raises_error(self):
        """Test registering duplicate server raises error."""
        registry = MCPRegistry(include_defaults=False)

        config = MCPServerConfig(
            name="test",
            server_type=MCPServerType.CUSTOM,
            command="test",
        )
        registry.register(config)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(config)

    def test_update(self):
        """Test updating existing server."""
        registry = MCPRegistry(include_defaults=False)

        config1 = MCPServerConfig(
            name="test",
            server_type=MCPServerType.CUSTOM,
            command="old_command",
        )
        registry.register(config1)

        config2 = MCPServerConfig(
            name="test",
            server_type=MCPServerType.CUSTOM,
            command="new_command",
        )
        registry.update(config2)

        assert registry.get("test").command == "new_command"

    def test_update_not_registered_raises_error(self):
        """Test updating non-existent server raises error."""
        registry = MCPRegistry(include_defaults=False)

        config = MCPServerConfig(
            name="test",
            server_type=MCPServerType.CUSTOM,
            command="test",
        )

        with pytest.raises(KeyError, match="not registered"):
            registry.update(config)

    def test_unregister(self):
        """Test unregistering a server."""
        registry = MCPRegistry(include_defaults=False)

        config = MCPServerConfig(
            name="test",
            server_type=MCPServerType.CUSTOM,
            command="test",
        )
        registry.register(config)
        registry.unregister("test")

        assert not registry.is_registered("test")

    def test_unregister_not_registered_raises_error(self):
        """Test unregistering non-existent server raises error."""
        registry = MCPRegistry(include_defaults=False)

        with pytest.raises(KeyError, match="not registered"):
            registry.unregister("test")

    def test_get(self):
        """Test getting a server configuration."""
        registry = MCPRegistry()

        config = registry.get("filesystem")
        assert config.name == "filesystem"

    def test_get_not_registered_raises_error(self):
        """Test getting non-existent server raises error."""
        registry = MCPRegistry(include_defaults=False)

        with pytest.raises(KeyError, match="not registered"):
            registry.get("nonexistent")

    def test_get_optional(self):
        """Test get_optional returns None for non-existent."""
        registry = MCPRegistry(include_defaults=False)

        assert registry.get_optional("test") is None

    def test_get_optional_returns_config(self):
        """Test get_optional returns config when exists."""
        registry = MCPRegistry()

        config = registry.get_optional("filesystem")
        assert config is not None
        assert config.name == "filesystem"

    def test_list_all(self):
        """Test listing all servers."""
        registry = MCPRegistry()

        configs = registry.list_all()
        assert len(configs) == 4

    def test_list_enabled(self):
        """Test listing enabled servers."""
        registry = MCPRegistry()

        configs = registry.list_enabled()
        assert len(configs) == 4

        # Disable one
        registry.disable("filesystem")
        configs = registry.list_enabled()
        assert len(configs) == 3

    def test_list_ready(self):
        """Test listing ready servers."""
        registry = MCPRegistry()

        # Without env vars, postgres and github shouldn't be ready
        ready = registry.list_ready()
        ready_names = [c.name for c in ready]

        assert "filesystem" in ready_names
        assert "open-forge" in ready_names
        # These require env vars
        assert "postgres" not in ready_names
        assert "github" not in ready_names

    def test_list_ready_with_env(self):
        """Test list_ready with environment variables."""
        registry = MCPRegistry()

        ready = registry.list_ready({
            "POSTGRES_CONNECTION_STRING": "test",
            "GITHUB_PERSONAL_ACCESS_TOKEN": "test",
        })
        ready_names = [c.name for c in ready]

        assert "postgres" in ready_names
        assert "github" in ready_names

    def test_list_by_type(self):
        """Test listing by server type."""
        registry = MCPRegistry()

        filesystem_servers = registry.list_by_type(MCPServerType.FILESYSTEM)
        assert len(filesystem_servers) == 1
        assert filesystem_servers[0].name == "filesystem"

    def test_enable(self):
        """Test enabling a server."""
        registry = MCPRegistry()
        registry.disable("filesystem")

        assert not registry.get("filesystem").enabled

        registry.enable("filesystem")
        assert registry.get("filesystem").enabled

    def test_disable(self):
        """Test disabling a server."""
        registry = MCPRegistry()

        registry.disable("filesystem")
        assert not registry.get("filesystem").enabled

    def test_enabled_count(self):
        """Test enabled_count property."""
        registry = MCPRegistry()

        assert registry.enabled_count == 4

        registry.disable("filesystem")
        assert registry.enabled_count == 3

    def test_to_dict(self):
        """Test exporting to dictionary."""
        registry = MCPRegistry(include_defaults=False)
        config = MCPServerConfig(
            name="test",
            server_type=MCPServerType.CUSTOM,
            command="test",
        )
        registry.register(config)

        data = registry.to_dict()
        assert "test" in data
        assert data["test"]["command"] == "test"

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "custom": {
                "name": "custom",
                "server_type": "custom",
                "command": "custom_cmd",
            }
        }

        registry = MCPRegistry.from_dict(data, include_defaults=False)
        assert registry.is_registered("custom")
        assert registry.get("custom").command == "custom_cmd"

    def test_from_dict_with_defaults(self):
        """Test from_dict includes defaults when specified."""
        data = {
            "custom": {
                "name": "custom",
                "server_type": "custom",
                "command": "custom_cmd",
            }
        }

        registry = MCPRegistry.from_dict(data, include_defaults=True)
        assert registry.is_registered("custom")
        assert registry.is_registered("filesystem")


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def teardown_method(self):
        """Reset global registry after each test."""
        reset_registry()

    def test_get_registry_creates_instance(self):
        """Test get_registry creates global instance."""
        registry = get_registry()

        assert registry is not None
        assert registry.count == 4

    def test_get_registry_returns_same_instance(self):
        """Test get_registry returns same instance."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_reset_registry(self):
        """Test reset_registry resets global instance."""
        registry1 = get_registry()
        registry1.disable("filesystem")

        reset_registry()

        registry2 = get_registry()
        assert registry2.get("filesystem").enabled is True
        assert registry1 is not registry2
