"""
Spatial Query Operations

Query builders and executors for spatial operations (bbox, intersection, distance, within).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import asyncpg

    from forge_geo.core.types import GeoPoint, GeoPolygon


class SpatialOperator(str, Enum):
    """Spatial relationship operators."""

    BBOX = "bbox"
    INTERSECTS = "intersects"
    WITHIN = "within"
    CONTAINS = "contains"
    DISTANCE = "distance"
    NEAREST = "nearest"


@dataclass
class SpatialQueryResult:
    """Result of a spatial query."""

    features: list[dict[str, Any]]
    total_count: int
    query_time_ms: float | None = None


@dataclass
class SpatialQuery:
    """
    Builder for spatial queries.

    Provides a fluent interface for constructing spatial queries that can
    be executed against PostGIS or filtered in memory.

    Example:
        query = (
            SpatialQuery(table="locations", geometry_column="geom")
            .bbox(-122.5, 37.7, -122.3, 37.9)
            .within_distance(center_point, 1000)
            .limit(100)
        )
        results = await query.execute(pool)
    """

    table: str
    geometry_column: str = "geom"
    srid: int = 4326
    select_columns: list[str] = field(default_factory=lambda: ["*"])
    filters: list[dict[str, Any]] = field(default_factory=list)
    order_by: str | None = None
    limit_count: int | None = None
    offset_count: int = 0

    def bbox(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
    ) -> SpatialQuery:
        """
        Filter by bounding box.

        Args:
            min_lon: Minimum longitude (west).
            min_lat: Minimum latitude (south).
            max_lon: Maximum longitude (east).
            max_lat: Maximum latitude (north).

        Returns:
            Self for chaining.
        """
        self.filters.append({
            "type": SpatialOperator.BBOX,
            "min_lon": min_lon,
            "min_lat": min_lat,
            "max_lon": max_lon,
            "max_lat": max_lat,
        })
        return self

    def intersects(self, polygon: GeoPolygon) -> SpatialQuery:
        """
        Filter by intersection with a polygon.

        Args:
            polygon: The polygon to test intersection with.

        Returns:
            Self for chaining.
        """
        self.filters.append({
            "type": SpatialOperator.INTERSECTS,
            "geometry": polygon.to_geojson(),
        })
        return self

    def within(self, polygon: GeoPolygon) -> SpatialQuery:
        """
        Filter by containment within a polygon.

        Args:
            polygon: The polygon that must contain the features.

        Returns:
            Self for chaining.
        """
        self.filters.append({
            "type": SpatialOperator.WITHIN,
            "geometry": polygon.to_geojson(),
        })
        return self

    def within_distance(
        self,
        point: GeoPoint,
        distance_meters: float,
    ) -> SpatialQuery:
        """
        Filter by distance from a point.

        Args:
            point: The center point.
            distance_meters: Maximum distance in meters.

        Returns:
            Self for chaining.
        """
        self.filters.append({
            "type": SpatialOperator.DISTANCE,
            "point": {"longitude": point.longitude, "latitude": point.latitude},
            "distance_meters": distance_meters,
        })
        return self

    def nearest(
        self,
        point: GeoPoint,
        k: int = 10,
    ) -> SpatialQuery:
        """
        Find K nearest neighbors to a point.

        Args:
            point: The reference point.
            k: Number of neighbors to return.

        Returns:
            Self for chaining.
        """
        self.filters.append({
            "type": SpatialOperator.NEAREST,
            "point": {"longitude": point.longitude, "latitude": point.latitude},
            "k": k,
        })
        self.limit_count = k
        return self

    def select(self, *columns: str) -> SpatialQuery:
        """
        Specify columns to select.

        Args:
            columns: Column names to select.

        Returns:
            Self for chaining.
        """
        self.select_columns = list(columns)
        return self

    def limit(self, count: int) -> SpatialQuery:
        """
        Limit the number of results.

        Args:
            count: Maximum number of results.

        Returns:
            Self for chaining.
        """
        self.limit_count = count
        return self

    def offset(self, count: int) -> SpatialQuery:
        """
        Skip a number of results (for pagination).

        Args:
            count: Number of results to skip.

        Returns:
            Self for chaining.
        """
        self.offset_count = count
        return self

    def order_by_distance(self, point: GeoPoint) -> SpatialQuery:
        """
        Order results by distance from a point.

        Args:
            point: The reference point.

        Returns:
            Self for chaining.
        """
        self.order_by = f"{self.geometry_column} <-> ST_SetSRID(ST_MakePoint({point.longitude}, {point.latitude}), {self.srid})"
        return self

    def build_sql(self) -> tuple[str, list[Any]]:
        """
        Build the SQL query string and parameters.

        Returns:
            Tuple of (SQL string, parameter list).
        """
        select_clause = ", ".join(self.select_columns)
        where_clauses: list[str] = []
        params: list[Any] = []
        param_idx = 1

        for f in self.filters:
            filter_type = f["type"]

            if filter_type == SpatialOperator.BBOX:
                where_clauses.append(
                    f"{self.geometry_column} && ST_MakeEnvelope(${param_idx}, ${param_idx + 1}, ${param_idx + 2}, ${param_idx + 3}, {self.srid})"
                )
                params.extend([f["min_lon"], f["min_lat"], f["max_lon"], f["max_lat"]])
                param_idx += 4

            elif filter_type == SpatialOperator.INTERSECTS:
                where_clauses.append(
                    f"ST_Intersects({self.geometry_column}, ST_SetSRID(ST_GeomFromGeoJSON(${param_idx}), {self.srid}))"
                )
                import json
                params.append(json.dumps(f["geometry"]))
                param_idx += 1

            elif filter_type == SpatialOperator.WITHIN:
                where_clauses.append(
                    f"ST_Within({self.geometry_column}, ST_SetSRID(ST_GeomFromGeoJSON(${param_idx}), {self.srid}))"
                )
                import json
                params.append(json.dumps(f["geometry"]))
                param_idx += 1

            elif filter_type == SpatialOperator.DISTANCE:
                point = f["point"]
                where_clauses.append(
                    f"ST_DWithin({self.geometry_column}::geography, ST_SetSRID(ST_MakePoint(${param_idx}, ${param_idx + 1}), {self.srid})::geography, ${param_idx + 2})"
                )
                params.extend([point["longitude"], point["latitude"], f["distance_meters"]])
                param_idx += 3

            elif filter_type == SpatialOperator.NEAREST:
                # KNN handled via ORDER BY, not WHERE
                point = f["point"]
                self.order_by = f"{self.geometry_column} <-> ST_SetSRID(ST_MakePoint({point['longitude']}, {point['latitude']}), {self.srid})"

        where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"
        order_clause = f"ORDER BY {self.order_by}" if self.order_by else ""
        limit_clause = f"LIMIT {self.limit_count}" if self.limit_count else ""
        offset_clause = f"OFFSET {self.offset_count}" if self.offset_count else ""

        sql = f"""
        SELECT {select_clause}
        FROM {self.table}
        WHERE {where_clause}
        {order_clause}
        {limit_clause}
        {offset_clause}
        """.strip()

        return sql, params

    async def execute(self, pool: asyncpg.Pool) -> SpatialQueryResult:
        """
        Execute the query against a PostgreSQL/PostGIS database.

        Args:
            pool: asyncpg connection pool.

        Returns:
            SpatialQueryResult with features and metadata.
        """
        import time

        sql, params = self.build_sql()

        start_time = time.perf_counter()

        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        features = [dict(row) for row in rows]

        return SpatialQueryResult(
            features=features,
            total_count=len(features),
            query_time_ms=elapsed_ms,
        )

    async def count(self, pool: asyncpg.Pool) -> int:
        """
        Count results matching the query (without fetching).

        Args:
            pool: asyncpg connection pool.

        Returns:
            Number of matching features.
        """
        where_clauses: list[str] = []
        params: list[Any] = []
        param_idx = 1

        for f in self.filters:
            filter_type = f["type"]

            if filter_type == SpatialOperator.BBOX:
                where_clauses.append(
                    f"{self.geometry_column} && ST_MakeEnvelope(${param_idx}, ${param_idx + 1}, ${param_idx + 2}, ${param_idx + 3}, {self.srid})"
                )
                params.extend([f["min_lon"], f["min_lat"], f["max_lon"], f["max_lat"]])
                param_idx += 4

            elif filter_type == SpatialOperator.DISTANCE:
                point = f["point"]
                where_clauses.append(
                    f"ST_DWithin({self.geometry_column}::geography, ST_SetSRID(ST_MakePoint(${param_idx}, ${param_idx + 1}), {self.srid})::geography, ${param_idx + 2})"
                )
                params.extend([point["longitude"], point["latitude"], f["distance_meters"]])
                param_idx += 3

        where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"

        sql = f"SELECT COUNT(*) FROM {self.table} WHERE {where_clause}"

        async with pool.acquire() as conn:
            result = await conn.fetchval(sql, *params)

        return result or 0
