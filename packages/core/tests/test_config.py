"""
Tests for core configuration module.
"""
import pytest
from unittest.mock import patch
import os


class TestSettings:
    """Tests for Settings configuration."""

    def test_settings_loads_from_env(self, mock_env_vars):
        """Test that settings are loaded from environment variables."""
        # Import inside test to pick up mocked env vars
        from core.config import Settings

        with patch.dict(os.environ, mock_env_vars, clear=False):
            settings = Settings()

            assert settings.environment == "test"
            assert settings.database.host == "localhost"
            assert settings.database.port == 5432
            assert settings.database.name == "test_db"
            assert settings.redis.host == "localhost"
            assert settings.redis.port == 6379

    def test_database_url_construction(self, mock_env_vars):
        """Test that database URL is properly constructed."""
        from core.config import Settings

        with patch.dict(os.environ, mock_env_vars, clear=False):
            settings = Settings()

            expected_url = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
            assert settings.database.async_url == expected_url

    def test_redis_url_construction(self, mock_env_vars):
        """Test that Redis URL is properly constructed."""
        from core.config import Settings

        with patch.dict(os.environ, mock_env_vars, clear=False):
            settings = Settings()

            expected_url = "redis://localhost:6379"
            assert settings.redis.url == expected_url

    def test_settings_caching(self, mock_env_vars):
        """Test that get_settings returns cached instance."""
        from core.config import get_settings

        with patch.dict(os.environ, mock_env_vars, clear=False):
            # Clear cache first
            get_settings.cache_clear()

            settings1 = get_settings()
            settings2 = get_settings()

            assert settings1 is settings2
