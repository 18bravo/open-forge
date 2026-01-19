"""
Central configuration management for Open Forge.
Uses pydantic-settings for validation and environment variable support.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class DatabaseSettings(BaseSettings):
    """PostgreSQL configuration."""
    host: str = Field(default="localhost", alias="DB_HOST")
    port: int = Field(default=5432, alias="DB_PORT")
    user: str = Field(default="foundry", alias="DB_USER")
    password: str = Field(default="foundry_dev", alias="DB_PASSWORD")
    database: str = Field(default="foundry", alias="DB_NAME")
    pool_size: int = Field(default=10, alias="DB_POOL_SIZE")

    model_config = {"env_prefix": "", "extra": "ignore"}

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class IcebergSettings(BaseSettings):
    """Apache Iceberg catalog configuration."""
    catalog_uri: str = Field(default="http://localhost:8181", alias="ICEBERG_CATALOG_URI")
    warehouse_path: str = Field(default="s3://foundry-lake/warehouse", alias="ICEBERG_WAREHOUSE")
    s3_endpoint: str = Field(default="http://localhost:9000", alias="S3_ENDPOINT")
    s3_access_key: str = Field(default="minio", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="minio123", alias="S3_SECRET_KEY")

    model_config = {"env_prefix": "", "extra": "ignore"}


class RedisSettings(BaseSettings):
    """Redis configuration for messaging and caching."""
    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")

    model_config = {"env_prefix": "", "extra": "ignore"}

    @property
    def connection_string(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}"
        return f"redis://{self.host}:{self.port}"


class LLMSettings(BaseSettings):
    """LLM API configuration."""
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    default_model: str = Field(default="claude-sonnet-4-20250514", alias="DEFAULT_LLM_MODEL")
    max_tokens: int = Field(default=16000, alias="LLM_MAX_TOKENS")

    model_config = {"env_prefix": "", "extra": "ignore"}


class ObservabilitySettings(BaseSettings):
    """Observability and tracing configuration."""
    otlp_endpoint: str = Field(default="http://localhost:4317", alias="OTLP_ENDPOINT")
    service_name: str = Field(default="open-forge", alias="SERVICE_NAME")
    langsmith_api_key: Optional[str] = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="open-forge", alias="LANGSMITH_PROJECT")

    model_config = {"env_prefix": "", "extra": "ignore"}


class Settings(BaseSettings):
    """Root settings object."""
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")

    model_config = {"env_prefix": "", "extra": "ignore"}

    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings()

    @property
    def iceberg(self) -> IcebergSettings:
        return IcebergSettings()

    @property
    def redis(self) -> RedisSettings:
        return RedisSettings()

    @property
    def llm(self) -> LLMSettings:
        return LLMSettings()

    @property
    def observability(self) -> ObservabilitySettings:
        return ObservabilitySettings()


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
