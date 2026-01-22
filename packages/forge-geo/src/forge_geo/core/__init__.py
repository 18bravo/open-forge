"""
Forge Geo Core Module

Spatial primitives, indexes, and query operations.
"""

from forge_geo.core.types import GeoLine, GeoPoint, GeoPolygon
from forge_geo.core.indexes import H3Index, PostGISIndex, SpatialIndex
from forge_geo.core.queries import SpatialQuery

__all__ = [
    # Types
    "GeoPoint",
    "GeoPolygon",
    "GeoLine",
    # Indexes
    "SpatialIndex",
    "H3Index",
    "PostGISIndex",
    # Queries
    "SpatialQuery",
]
