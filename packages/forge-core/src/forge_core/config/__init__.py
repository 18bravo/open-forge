"""
Configuration Management Module

This module provides centralized configuration management for the Open Forge platform.

Features:
- Environment-based configuration (development, staging, production)
- Validation using Pydantic settings
- Support for environment variables and .env files
- Secret management integration
"""

from forge_core.config.settings import (
    DatabaseSettings,
    Environment,
    RedisSettings,
    Settings,
    StorageSettings,
    get_settings,
)

__all__ = [
    "Settings",
    "Environment",
    "DatabaseSettings",
    "RedisSettings",
    "StorageSettings",
    "get_settings",
]
