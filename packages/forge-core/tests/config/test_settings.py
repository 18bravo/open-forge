"""Tests for configuration settings."""

import os

import pytest

from forge_core.config.settings import (
    DatabaseSettings,
    Environment,
    Settings,
    get_settings,
)


class TestSettings:
    """Tests for the Settings class."""

    def test_default_settings(self) -> None:
        """Test default settings values."""
        settings = Settings()

        assert settings.environment == Environment.DEVELOPMENT
        assert settings.debug is False
        assert settings.app_name == "Open Forge"

    def test_environment_validation(self) -> None:
        """Test environment validation."""
        settings = Settings(environment="production")  # type: ignore
        assert settings.environment == Environment.PRODUCTION

        settings = Settings(environment="STAGING")  # type: ignore
        assert settings.environment == Environment.STAGING

    def test_is_development(self) -> None:
        """Test is_development property."""
        dev_settings = Settings(environment=Environment.DEVELOPMENT)
        prod_settings = Settings(environment=Environment.PRODUCTION)

        assert dev_settings.is_development
        assert not prod_settings.is_development

    def test_is_production(self) -> None:
        """Test is_production property."""
        dev_settings = Settings(environment=Environment.DEVELOPMENT)
        prod_settings = Settings(environment=Environment.PRODUCTION)

        assert not dev_settings.is_production
        assert prod_settings.is_production

    def test_is_test(self) -> None:
        """Test is_test property."""
        test_settings = Settings(environment=Environment.TEST)
        dev_settings = Settings(environment=Environment.DEVELOPMENT)

        assert test_settings.is_test
        assert not dev_settings.is_test


class TestDatabaseSettings:
    """Tests for DatabaseSettings."""

    def test_default_values(self) -> None:
        """Test default database settings."""
        settings = DatabaseSettings()

        assert settings.host == "localhost"
        assert settings.port == 5432
        assert settings.name == "forge"

    def test_url_property(self) -> None:
        """Test URL property generation."""
        settings = DatabaseSettings(
            host="db.example.com",
            port=5432,
            name="mydb",
            user="myuser",
        )

        assert "db.example.com" in settings.url
        assert "mydb" in settings.url
        assert "myuser" in settings.url

    def test_async_url_property(self) -> None:
        """Test async URL property generation."""
        settings = DatabaseSettings()

        assert "asyncpg" in settings.async_url


class TestGetSettings:
    """Tests for the get_settings function."""

    def test_returns_settings(self) -> None:
        """Test that get_settings returns a Settings instance."""
        # Clear cache first
        get_settings.cache_clear()

        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_caching(self) -> None:
        """Test that settings are cached."""
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_cache_clear(self) -> None:
        """Test clearing the settings cache."""
        get_settings.cache_clear()

        settings1 = get_settings()

        get_settings.cache_clear()

        settings2 = get_settings()

        # After cache clear, we should get a new instance
        # (though they may be equal in value)
        assert settings1 is not settings2
