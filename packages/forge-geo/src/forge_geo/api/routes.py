"""
Forge Geo API Routes

FastAPI endpoints for geospatial operations.
"""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from forge_geo.core.types import GeoLine, GeoPoint, GeoPolygon


# ============================================================================
# Request/Response Models
# ============================================================================


class PointRequest(BaseModel):
    """Request model for a geographic point."""

    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")


class PolygonRequest(BaseModel):
    """Request model for a geographic polygon."""

    coordinates: list[list[tuple[float, float]]] = Field(
        ..., description="Polygon coordinates (exterior ring + optional holes)"
    )


class DistanceRequest(BaseModel):
    """Request for distance calculation between two points."""

    point1: PointRequest
    point2: PointRequest
    unit: Literal["km", "m", "mi"] = "km"


class DistanceResponse(BaseModel):
    """Response for distance calculation."""

    distance: float
    unit: str


class WithinDistanceRequest(BaseModel):
    """Request for finding features within distance."""

    center: PointRequest
    distance_km: float = Field(..., gt=0, description="Search radius in kilometers")
    dataset_id: str
    limit: int = Field(default=1000, ge=1, le=10000)


class NearestRequest(BaseModel):
    """Request for K-nearest neighbors search."""

    point: PointRequest
    dataset_id: str
    k: int = Field(default=10, ge=1, le=100)


class InPolygonRequest(BaseModel):
    """Request for finding features within a polygon."""

    polygon: PolygonRequest
    dataset_id: str
    limit: int = Field(default=1000, ge=1, le=10000)


class H3CellRequest(BaseModel):
    """Request for H3 cell operations."""

    point: PointRequest
    resolution: int = Field(default=9, ge=0, le=15)


class H3CellResponse(BaseModel):
    """Response for H3 cell lookup."""

    cell_id: str
    resolution: int
    boundary: dict[str, Any]  # GeoJSON polygon


class H3PolygonRequest(BaseModel):
    """Request for H3 cells covering a polygon."""

    polygon: PolygonRequest
    resolution: int = Field(default=9, ge=0, le=15)


class BufferRequest(BaseModel):
    """Request for geometry buffer operation."""

    geometry: dict[str, Any]  # GeoJSON geometry
    distance_km: float = Field(..., gt=0)


class FeatureResponse(BaseModel):
    """Response containing GeoJSON features."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[dict[str, Any]]
    total_count: int
    query_time_ms: float | None = None


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/api/v1/geo", tags=["geo"])


@router.post("/distance", response_model=DistanceResponse)
async def calculate_distance(request: DistanceRequest) -> DistanceResponse:
    """
    Calculate the distance between two points.

    Uses the Haversine formula for accurate great-circle distance.
    """
    p1 = GeoPoint(longitude=request.point1.longitude, latitude=request.point1.latitude)
    p2 = GeoPoint(longitude=request.point2.longitude, latitude=request.point2.latitude)

    distance = p1.distance_to(p2, unit=request.unit)

    return DistanceResponse(distance=distance, unit=request.unit)


@router.post("/within-distance", response_model=FeatureResponse)
async def points_within_distance(request: WithinDistanceRequest) -> FeatureResponse:
    """
    Find all features within a specified distance of a center point.

    Uses PostGIS ST_DWithin for efficient spatial filtering.
    """
    # Stub - actual implementation would query the database
    # center = GeoPoint(longitude=request.center.longitude, latitude=request.center.latitude)
    # query = (
    #     SpatialQuery(table=request.dataset_id)
    #     .within_distance(center, request.distance_km * 1000)
    #     .limit(request.limit)
    # )
    # result = await query.execute(pool)
    raise NotImplementedError("Database connection required")


@router.post("/nearest", response_model=FeatureResponse)
async def find_nearest(request: NearestRequest) -> FeatureResponse:
    """
    Find the K nearest neighbors to a point.

    Uses PostGIS KNN index for efficient nearest neighbor search.
    """
    # Stub - actual implementation would query the database
    # point = GeoPoint(longitude=request.point.longitude, latitude=request.point.latitude)
    # query = (
    #     SpatialQuery(table=request.dataset_id)
    #     .nearest(point, k=request.k)
    # )
    # result = await query.execute(pool)
    raise NotImplementedError("Database connection required")


@router.post("/in-polygon", response_model=FeatureResponse)
async def points_in_polygon(request: InPolygonRequest) -> FeatureResponse:
    """
    Find all features within a polygon boundary.

    Uses PostGIS ST_Within for efficient containment testing.
    """
    # Stub - actual implementation would query the database
    # polygon = GeoPolygon(coordinates=request.polygon.coordinates)
    # query = (
    #     SpatialQuery(table=request.dataset_id)
    #     .within(polygon)
    #     .limit(request.limit)
    # )
    # result = await query.execute(pool)
    raise NotImplementedError("Database connection required")


@router.post("/h3/cell", response_model=H3CellResponse)
async def point_to_h3_cell(request: H3CellRequest) -> H3CellResponse:
    """
    Get the H3 cell ID and boundary for a point.

    Returns the hexagonal cell containing the point at the specified resolution.
    """
    # Stub - actual implementation would use h3 library
    # from forge_geo.core.indexes import H3Index
    # index = H3Index(resolution=request.resolution)
    # point = GeoPoint(longitude=request.point.longitude, latitude=request.point.latitude)
    # cell_id = index.index_point(point)
    # boundary = index.get_cell_boundary(cell_id)
    raise NotImplementedError("H3 library required")


@router.post("/h3/polygon", response_model=list[str])
async def h3_cells_in_polygon(request: H3PolygonRequest) -> list[str]:
    """
    Get all H3 cells that cover a polygon.

    Returns a list of H3 cell IDs at the specified resolution.
    """
    # Stub - actual implementation would use h3 library
    # from forge_geo.core.indexes import H3Index
    # index = H3Index(resolution=request.resolution)
    # polygon = GeoPolygon(coordinates=request.polygon.coordinates)
    # cells = index.cells_in_polygon(polygon)
    raise NotImplementedError("H3 library required")


@router.post("/buffer")
async def buffer_geometry(request: BufferRequest) -> dict[str, Any]:
    """
    Create a buffer polygon around a geometry.

    Returns a GeoJSON polygon representing the buffered area.
    """
    # Stub - actual implementation would use shapely/pyproj
    # This requires coordinate transformation for accurate buffering
    raise NotImplementedError("Shapely/pyproj required for buffer operation")


@router.get("/bbox/{dataset_id}")
async def get_dataset_bbox(
    dataset_id: str,
) -> dict[str, Any]:
    """
    Get the bounding box of all features in a dataset.

    Returns min/max coordinates for the dataset extent.
    """
    # Stub - actual implementation would query the database
    # SELECT ST_Extent(geom) FROM dataset_id
    raise NotImplementedError("Database connection required")


@router.get("/datasets/{dataset_id}/features")
async def get_features(
    dataset_id: str,
    bbox: Annotated[str | None, Query(description="Bounding box: minLon,minLat,maxLon,maxLat")] = None,
    limit: Annotated[int, Query(ge=1, le=10000)] = 1000,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> FeatureResponse:
    """
    Get features from a dataset, optionally filtered by bounding box.

    This endpoint is used by the Atlas map component to load visible features.
    """
    # Stub - actual implementation would query the database
    # query = SpatialQuery(table=dataset_id)
    # if bbox:
    #     min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
    #     query = query.bbox(min_lon, min_lat, max_lon, max_lat)
    # query = query.limit(limit).offset(offset)
    # result = await query.execute(pool)
    raise NotImplementedError("Database connection required")
