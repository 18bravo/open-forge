"""
Open Forge Geo - Geospatial Capabilities Package

This package provides geospatial functionality for the Open Forge platform:

- **core**: Spatial primitives (Point, Polygon, Line), spatial indexes (H3, PostGIS), and queries
- **atlas**: Map visualization components (TypeScript/React - see src/atlas/)
- **api**: FastAPI routes for spatial operations

The package is a hybrid Python/TypeScript package:
- Python backend: src/forge_geo/ (spatial primitives, indexes, queries)
- TypeScript frontend: src/atlas/ (React map components with Mapbox/deck.gl)
"""

from forge_geo.core.types import GeoLine, GeoPoint, GeoPolygon
from forge_geo.core.indexes import H3Index, PostGISIndex, SpatialIndex
from forge_geo.core.queries import SpatialQuery

__version__ = "0.1.0"

__all__ = [
    # Spatial Types
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
