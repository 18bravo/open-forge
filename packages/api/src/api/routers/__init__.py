"""
API Routers for Open Forge.
"""
from api.routers.health import router as health_router
from api.routers.engagements import router as engagements_router
from api.routers.agents import router as agents_router
from api.routers.data_sources import router as data_sources_router
from api.routers.approvals import router as approvals_router
from api.routers.reviews import router as reviews_router
from api.routers.admin import router as admin_router
from api.routers.codegen import router as codegen_router

__all__ = [
    "health_router",
    "engagements_router",
    "agents_router",
    "data_sources_router",
    "approvals_router",
    "reviews_router",
    "admin_router",
    "codegen_router",
]
