"""
API module - FastAPI routes for forge-ai.

This module provides HTTP endpoints for:
- Completions and streaming
- Logic function management
- Context configuration
- Security configuration
"""

from forge_ai.api.routes import create_router

__all__ = ["create_router"]
