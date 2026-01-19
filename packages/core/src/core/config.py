"""
Central configuration management for Open Foundry.
Uses pydantic-settings for validation and environment variable support.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """PostgreSQL configuration."""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    user: str = Field(default="foundry", env="DB_USER")
    password: str = Field(env="DB_PASSWORD")
    database: str = Field(default="foundry", env="DB_NAME")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

class IcebergSettings(BaseSettings):
    """Apache Iceberg catalog configuration."""
    catalog_uri: str = Field(default="http://localhost:8181", env="ICEBERG_CATALOG_URI")
    warehouse_path: str = Field(default="s3://foundry-lake/warehouse", env="ICEBERG_WAREHOUSE")
    s3_endpoint: str = Field(default="http://localhost:9000", env="S3_ENDPOINT")
    s3_access_key: str = Field(env="S3_ACCESS_KEY")
    s3_secret_key: str = Field(env="S3_SECRET_KEY")

class RedisSettings(BaseSettings):
    """Redis configuration for messaging and caching."""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    @property
    def connection_string(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}"
        return f"redis://{self.host}:{self.port}"

class LLMSettings(BaseSettings):
    """LLM API configuration."""
    anthropic_api_key: str = Field(env="ANTHROPIC_API_KEY")
    default_model: str = Field(default="claude-sonnet-4-20250514", env="DEFAULT_LLM_MODEL")
    max_tokens: int = Field(default=16000, env="LLM_MAX_TOKENS")

class ObservabilitySettings(BaseSettings):
    """Observability and tracing configuration."""
    otlp_endpoint: str = Field(default="http://localhost:4317", env="OTLP_ENDPOINT")
    service_name: str = Field(default="open-foundry", env="SERVICE_NAME")
    langsmith_api_key: Optional[str] = Field(default=None, env="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="open-foundry", env="LANGSMITH_PROJECT")

class Settings(BaseSettings):
    """Root settings object."""
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    database: DatabaseSettings = DatabaseSettings()
    iceberg: IcebergSettings = IcebergSettings()
    redis: RedisSettings = RedisSettings()
    llm: LLMSettings = LLMSettings()
    observability: ObservabilitySettings = ObservabilitySettings()

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()