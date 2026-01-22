"""
Spatial Index Abstractions

Protocol definitions and implementations for spatial indexing (H3, PostGIS).
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from forge_geo.core.types import GeoPoint, GeoPolygon


@runtime_checkable
class SpatialIndex(Protocol):
    """
    Protocol for spatial indexing systems.

    Spatial indexes enable efficient spatial queries by organizing
    geographic data in a searchable structure.
    """

    @abstractmethod
    def index_point(self, point: GeoPoint) -> str:
        """
        Get the index cell/key for a point.

        Args:
            point: The geographic point to index.

        Returns:
            The index cell identifier (e.g., H3 cell ID, geohash).
        """
        ...

    @abstractmethod
    def get_cell_boundary(self, cell_id: str) -> GeoPolygon:
        """
        Get the boundary polygon of an index cell.

        Args:
            cell_id: The cell identifier.

        Returns:
            A GeoPolygon representing the cell boundary.
        """
        ...

    @abstractmethod
    def get_neighbors(self, cell_id: str, k: int = 1) -> list[str]:
        """
        Get neighboring cells within k steps.

        Args:
            cell_id: The center cell identifier.
            k: Number of steps/rings to include.

        Returns:
            List of neighbor cell identifiers.
        """
        ...

    @abstractmethod
    def cells_in_polygon(self, polygon: GeoPolygon) -> list[str]:
        """
        Get all cells that intersect with a polygon.

        Args:
            polygon: The area to cover.

        Returns:
            List of cell identifiers covering the polygon.
        """
        ...


class H3Index:
    """
    H3 hexagonal hierarchical spatial index.

    H3 divides the Earth into hexagonal cells at multiple resolutions (0-15).
    Higher resolutions provide more precision but more cells.

    Resolution reference:
    - 0: ~4,357 km edge length (continent scale)
    - 5: ~8 km edge length (city scale)
    - 9: ~174 m edge length (neighborhood scale)
    - 12: ~9 m edge length (building scale)
    - 15: ~0.5 m edge length (sub-meter precision)
    """

    def __init__(self, resolution: int = 9) -> None:
        """
        Initialize H3 index with specified resolution.

        Args:
            resolution: H3 resolution level (0-15). Default 9 (~174m cells).
        """
        if not 0 <= resolution <= 15:
            raise ValueError("H3 resolution must be between 0 and 15")
        self.resolution = resolution

    def index_point(self, point: GeoPoint) -> str:
        """
        Get the H3 cell ID for a point.

        Args:
            point: The geographic point.

        Returns:
            H3 cell identifier string.
        """
        # Stub - actual implementation would use h3 library:
        # import h3
        # return h3.latlng_to_cell(point.latitude, point.longitude, self.resolution)
        raise NotImplementedError("H3 index_point requires h3 library")

    def get_cell_boundary(self, cell_id: str) -> GeoPolygon:
        """
        Get the boundary polygon of an H3 cell.

        Args:
            cell_id: H3 cell identifier.

        Returns:
            A GeoPolygon representing the hexagonal cell boundary.
        """
        # Stub - actual implementation would use h3 library:
        # import h3
        # boundary = h3.cell_to_boundary(cell_id)
        # coords = [(lng, lat) for lat, lng in boundary]
        # coords.append(coords[0])  # Close ring
        # return GeoPolygon(coordinates=[coords])
        raise NotImplementedError("H3 get_cell_boundary requires h3 library")

    def get_neighbors(self, cell_id: str, k: int = 1) -> list[str]:
        """
        Get all H3 cells within k rings of the center cell.

        Args:
            cell_id: Center H3 cell identifier.
            k: Number of rings to include.

        Returns:
            List of H3 cell identifiers.
        """
        # Stub - actual implementation would use h3 library:
        # import h3
        # return list(h3.grid_disk(cell_id, k))
        raise NotImplementedError("H3 get_neighbors requires h3 library")

    def cells_in_polygon(self, polygon: GeoPolygon) -> list[str]:
        """
        Get all H3 cells that intersect with a polygon.

        Args:
            polygon: The area to cover.

        Returns:
            List of H3 cell identifiers.
        """
        # Stub - actual implementation would use h3 library:
        # import h3
        # geojson = polygon.to_geojson()
        # return list(h3.polygon_to_cells(geojson, self.resolution))
        raise NotImplementedError("H3 cells_in_polygon requires h3 library")

    def get_ring(self, cell_id: str, k: int) -> list[str]:
        """
        Get the ring of H3 cells at exactly distance k.

        Args:
            cell_id: Center H3 cell identifier.
            k: Ring distance.

        Returns:
            List of H3 cell identifiers forming the ring.
        """
        # Stub - actual implementation would use h3 library:
        # import h3
        # return list(h3.grid_ring(cell_id, k))
        raise NotImplementedError("H3 get_ring requires h3 library")

    def get_parent(self, cell_id: str, parent_resolution: int | None = None) -> str:
        """
        Get the parent cell at a lower resolution.

        Args:
            cell_id: H3 cell identifier.
            parent_resolution: Target resolution. If None, uses resolution - 1.

        Returns:
            Parent cell identifier.
        """
        # Stub - actual implementation would use h3 library:
        # import h3
        # if parent_resolution is None:
        #     parent_resolution = h3.get_resolution(cell_id) - 1
        # return h3.cell_to_parent(cell_id, parent_resolution)
        raise NotImplementedError("H3 get_parent requires h3 library")

    def compact_cells(self, cells: list[str]) -> list[str]:
        """
        Compact a set of H3 cells to larger cells where possible.

        Args:
            cells: List of H3 cell identifiers.

        Returns:
            Compacted list of cell identifiers.
        """
        # Stub - actual implementation would use h3 library:
        # import h3
        # return list(h3.compact_cells(cells))
        raise NotImplementedError("H3 compact_cells requires h3 library")


class PostGISIndex:
    """
    PostGIS spatial index using PostgreSQL.

    Leverages PostGIS R-tree indexes for efficient spatial queries
    directly in the database.
    """

    def __init__(
        self,
        table_name: str,
        geometry_column: str = "geom",
        srid: int = 4326,
    ) -> None:
        """
        Initialize PostGIS index configuration.

        Args:
            table_name: Name of the table containing geometry.
            geometry_column: Name of the geometry column.
            srid: Spatial Reference System Identifier (default 4326 = WGS84).
        """
        self.table_name = table_name
        self.geometry_column = geometry_column
        self.srid = srid

    def index_point(self, point: GeoPoint) -> str:
        """
        Generate SQL for creating a point geometry.

        Note: PostGIS doesn't have discrete cells like H3.
        This returns the WKT representation.

        Args:
            point: The geographic point.

        Returns:
            WKT string representation of the point.
        """
        return f"POINT({point.longitude} {point.latitude})"

    def get_cell_boundary(self, cell_id: str) -> GeoPolygon:
        """
        Not applicable for PostGIS (no discrete cells).

        Raises:
            NotImplementedError: PostGIS doesn't use discrete cells.
        """
        raise NotImplementedError("PostGIS does not use discrete cells like H3")

    def get_neighbors(self, cell_id: str, k: int = 1) -> list[str]:
        """
        Not directly applicable for PostGIS.

        For PostGIS, use spatial queries with ST_DWithin or ST_Buffer.

        Raises:
            NotImplementedError: Use spatial query methods instead.
        """
        raise NotImplementedError("Use SpatialQuery.within_distance for PostGIS")

    def cells_in_polygon(self, polygon: GeoPolygon) -> list[str]:
        """
        Not applicable for PostGIS (no discrete cells).

        For PostGIS, use spatial queries with ST_Within or ST_Intersects.

        Raises:
            NotImplementedError: Use SpatialQuery.intersects for PostGIS.
        """
        raise NotImplementedError("Use SpatialQuery.intersects for PostGIS")

    def create_index_sql(self) -> str:
        """
        Generate SQL to create a spatial index.

        Returns:
            SQL statement to create a GIST spatial index.
        """
        index_name = f"idx_{self.table_name}_{self.geometry_column}_gist"
        return f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON {self.table_name}
        USING GIST ({self.geometry_column});
        """

    def bbox_query_sql(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
    ) -> str:
        """
        Generate SQL for a bounding box query.

        Args:
            min_lon: Minimum longitude.
            min_lat: Minimum latitude.
            max_lon: Maximum longitude.
            max_lat: Maximum latitude.

        Returns:
            SQL WHERE clause for bounding box filter.
        """
        return f"""
        {self.geometry_column} && ST_MakeEnvelope(
            {min_lon}, {min_lat}, {max_lon}, {max_lat}, {self.srid}
        )
        """

    def distance_query_sql(
        self,
        point: GeoPoint,
        distance_meters: float,
    ) -> str:
        """
        Generate SQL for a distance-based query.

        Args:
            point: Center point.
            distance_meters: Search radius in meters.

        Returns:
            SQL WHERE clause for distance filter.
        """
        return f"""
        ST_DWithin(
            {self.geometry_column}::geography,
            ST_SetSRID(ST_MakePoint({point.longitude}, {point.latitude}), {self.srid})::geography,
            {distance_meters}
        )
        """

    def knn_query_sql(
        self,
        point: GeoPoint,
        k: int,
        select_columns: str = "*",
    ) -> str:
        """
        Generate SQL for K-nearest neighbors query.

        Args:
            point: Reference point.
            k: Number of neighbors to return.
            select_columns: Columns to select.

        Returns:
            Complete SQL query for KNN search.
        """
        return f"""
        SELECT {select_columns},
               ST_Distance(
                   {self.geometry_column}::geography,
                   ST_SetSRID(ST_MakePoint({point.longitude}, {point.latitude}), {self.srid})::geography
               ) AS distance_meters
        FROM {self.table_name}
        ORDER BY {self.geometry_column} <-> ST_SetSRID(ST_MakePoint({point.longitude}, {point.latitude}), {self.srid})
        LIMIT {k};
        """
