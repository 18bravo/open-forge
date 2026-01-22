"""
FastAPI routes for forge-vectors.

This module provides REST API endpoints for:
- Vector store management (collections)
- Document operations (upsert, delete, get)
- Search operations (semantic, hybrid)
- Embedding generation
"""

from forge_vectors.api.routes import router

__all__ = ["router"]
