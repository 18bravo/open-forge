"""
FastAPI routes for connector management.

Provides REST API endpoints for:
- Connector type discovery
- Connection CRUD operations
- Schema discovery and profiling
- Sync job management
- Writeback job management
"""

from forge_connectors.api.routes import router

__all__ = ["router"]
