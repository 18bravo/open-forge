"""
Centralized Configuration Settings

This module defines the configuration schema for the Open Forge platform
using Pydantic settings for validation and environment variable support.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class DatabaseSettings(BaseSettings):
    """
    Database configuration settings.

    Attributes:
        host: Database host
        port: Database port
        name: Database name
        user: Database user
        password: Database password
        pool_size: Connection pool size
        max_overflow: Maximum pool overflow
        echo: Whether to echo SQL statements
    """

    model_config = SettingsConfigDict(env_prefix="FORGE_DB_")

    host: str = "localhost"
    port: int = 5432
    name: str = "forge"
    user: str = "forge"
    password: SecretStr = SecretStr("")
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False

    @property
    def url(self) -> str:
        """Get the database URL (without password for logging)."""
        return f"postgresql://{self.user}@{self.host}:{self.port}/{self.name}"

    @property
    def async_url(self) -> str:
        """Get the async database URL."""
        pwd = self.password.get_secret_value()
        return f"postgresql+asyncpg://{self.user}:{pwd}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """
    Redis configuration settings.

    Attributes:
        host: Redis host
        port: Redis port
        password: Redis password
        db: Redis database number
        ssl: Whether to use SSL
    """

    model_config = SettingsConfigDict(env_prefix="FORGE_REDIS_")

    host: str = "localhost"
    port: int = 6379
    password: SecretStr | None = None
    db: int = 0
    ssl: bool = False

    @property
    def url(self) -> str:
        """Get the Redis URL."""
        scheme = "rediss" if self.ssl else "redis"
        auth = ""
        if self.password:
            auth = f":{self.password.get_secret_value()}@"
        return f"{scheme}://{auth}{self.host}:{self.port}/{self.db}"


class StorageSettings(BaseSettings):
    """
    Object storage configuration settings.

    Attributes:
        provider: Storage provider (s3, azure, local)
        bucket: Bucket/container name
        endpoint: Custom endpoint URL
        region: Cloud region
        access_key: Access key ID
        secret_key: Secret access key
        base_path: Base path prefix
    """

    model_config = SettingsConfigDict(env_prefix="FORGE_STORAGE_")

    provider: str = "local"
    bucket: str = "/tmp/forge-storage"
    endpoint: str | None = None
    region: str = "us-east-1"
    access_key: SecretStr | None = None
    secret_key: SecretStr | None = None
    base_path: str = ""


class AuthSettings(BaseSettings):
    """
    Authentication configuration settings.

    Attributes:
        provider: Auth provider type (oidc, oauth2, internal)
        issuer: Token issuer URL
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        audience: Expected token audience
        jwt_secret: Secret for signing JWTs (internal auth only)
        jwt_algorithm: JWT signing algorithm
        token_expiry_minutes: Access token expiry time
        refresh_expiry_days: Refresh token expiry time
    """

    model_config = SettingsConfigDict(env_prefix="FORGE_AUTH_")

    provider: str = "internal"
    issuer: str = "http://localhost:8000"
    client_id: str = ""
    client_secret: SecretStr | None = None
    audience: str = "forge-api"
    jwt_secret: SecretStr = SecretStr("development-secret-change-in-production")
    jwt_algorithm: str = "HS256"
    token_expiry_minutes: int = 60
    refresh_expiry_days: int = 7


class EventBusSettings(BaseSettings):
    """
    Event bus configuration settings.

    Attributes:
        backend: Event bus backend (redis, postgres, memory)
        channel_prefix: Prefix for event channels
    """

    model_config = SettingsConfigDict(env_prefix="FORGE_EVENTS_")

    backend: str = "memory"
    channel_prefix: str = "forge:"


class GatewaySettings(BaseSettings):
    """
    API gateway configuration settings.

    Attributes:
        rate_limit_requests: Maximum requests per window
        rate_limit_window_seconds: Rate limit window in seconds
        circuit_breaker_failure_threshold: Failures before opening circuit
        circuit_breaker_timeout_seconds: Time before half-open state
    """

    model_config = SettingsConfigDict(env_prefix="FORGE_GATEWAY_")

    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 30


class LoggingSettings(BaseSettings):
    """
    Logging configuration settings.

    Attributes:
        level: Log level
        format: Log format (json, text)
        include_timestamp: Include timestamps in logs
    """

    model_config = SettingsConfigDict(env_prefix="FORGE_LOG_")

    level: str = "INFO"
    format: str = "text"
    include_timestamp: bool = True


class Settings(BaseSettings):
    """
    Main application settings.

    This is the root configuration class that aggregates all sub-configurations.
    Settings can be loaded from environment variables or .env files.

    Example usage:
        >>> settings = get_settings()
        >>> print(settings.environment)
        >>> print(settings.database.url)
    """

    model_config = SettingsConfigDict(
        env_prefix="FORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Core settings
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    app_name: str = "Open Forge"
    version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # CORS settings
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    cors_allow_credentials: bool = True

    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    events: EventBusSettings = Field(default_factory=EventBusSettings)
    gateway: GatewaySettings = Field(default_factory=GatewaySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v: str | Environment) -> Environment:
        """Validate and convert environment string to enum."""
        if isinstance(v, Environment):
            return v
        return Environment(v.lower())

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_test(self) -> bool:
        """Check if running in test mode."""
        return self.environment == Environment.TEST


@lru_cache()
def get_settings() -> Settings:
    """
    Get the application settings singleton.

    Settings are cached for performance. To reload settings, clear the cache:
        >>> get_settings.cache_clear()

    Returns:
        Settings instance
    """
    return Settings()


def configure_logging(settings: Settings | None = None) -> None:
    """
    Configure logging based on settings.

    Args:
        settings: Optional settings instance (uses get_settings() if None)
    """
    import logging
    import sys

    if settings is None:
        settings = get_settings()

    log_level = getattr(logging, settings.logging.level.upper(), logging.INFO)

    if settings.logging.format == "json":
        # Use JSON format for production
        format_string = (
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        # Human-readable format for development
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        if not settings.logging.include_timestamp:
            format_string = "%(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=log_level,
        format=format_string,
        stream=sys.stdout,
    )

    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
