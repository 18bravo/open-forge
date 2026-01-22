"""
Spatial Primitive Types

Core geospatial data structures for representing geographic features.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GeoPoint:
    """
    A geographic point representing a location on Earth.

    Attributes:
        longitude: The longitude coordinate (x) in degrees (-180 to 180).
        latitude: The latitude coordinate (y) in degrees (-90 to 90).
        altitude: Optional altitude in meters above sea level.
        properties: Additional metadata associated with this point.
    """

    longitude: float
    latitude: float
    altitude: float | None = None
    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def coordinates(self) -> tuple[float, float]:
        """Return coordinates as (longitude, latitude) tuple."""
        return (self.longitude, self.latitude)

    def to_geojson(self) -> dict[str, Any]:
        """Convert to GeoJSON Point geometry."""
        coords = [self.longitude, self.latitude]
        if self.altitude is not None:
            coords.append(self.altitude)
        return {
            "type": "Point",
            "coordinates": coords,
        }

    def to_feature(self) -> dict[str, Any]:
        """Convert to GeoJSON Feature with properties."""
        return {
            "type": "Feature",
            "geometry": self.to_geojson(),
            "properties": self.properties,
        }

    def distance_to(self, other: GeoPoint, unit: str = "km") -> float:
        """
        Calculate the Haversine distance to another point.

        Args:
            other: The target point.
            unit: Distance unit - 'km' (kilometers), 'm' (meters), or 'mi' (miles).

        Returns:
            Distance between points in the specified unit.
        """
        r = 6371  # Earth radius in km

        lat1, lat2 = math.radians(self.latitude), math.radians(other.latitude)
        dlat = math.radians(other.latitude - self.latitude)
        dlon = math.radians(other.longitude - self.longitude)

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        distance_km = r * c

        if unit == "m":
            return distance_km * 1000
        elif unit == "mi":
            return distance_km * 0.621371
        return distance_km

    def bearing_to(self, other: GeoPoint) -> float:
        """
        Calculate the initial bearing to another point.

        Args:
            other: The target point.

        Returns:
            Bearing in degrees (0-360, where 0 is north).
        """
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(other.latitude)
        dlon = math.radians(other.longitude - self.longitude)

        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360


@dataclass
class GeoPolygon:
    """
    A geographic polygon representing an area on Earth.

    The coordinates follow GeoJSON format: the first array is the exterior ring,
    subsequent arrays are interior rings (holes).

    Attributes:
        coordinates: List of coordinate rings. Each ring is a list of [lon, lat] tuples.
                    The first ring is the exterior, others are holes.
        properties: Additional metadata associated with this polygon.
    """

    coordinates: list[list[tuple[float, float]]]
    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def exterior(self) -> list[tuple[float, float]]:
        """Return the exterior ring coordinates."""
        return self.coordinates[0] if self.coordinates else []

    @property
    def holes(self) -> list[list[tuple[float, float]]]:
        """Return the interior rings (holes)."""
        return self.coordinates[1:] if len(self.coordinates) > 1 else []

    def to_geojson(self) -> dict[str, Any]:
        """Convert to GeoJSON Polygon geometry."""
        return {
            "type": "Polygon",
            "coordinates": [[[lon, lat] for lon, lat in ring] for ring in self.coordinates],
        }

    def to_feature(self) -> dict[str, Any]:
        """Convert to GeoJSON Feature with properties."""
        return {
            "type": "Feature",
            "geometry": self.to_geojson(),
            "properties": self.properties,
        }

    def contains_point(self, point: GeoPoint) -> bool:
        """
        Check if this polygon contains a point.

        Uses the ray casting algorithm.

        Args:
            point: The point to check.

        Returns:
            True if the point is inside the polygon.
        """
        # Simplified ray casting - for production use shapely
        x, y = point.longitude, point.latitude
        exterior = self.exterior

        n = len(exterior)
        inside = False

        p1x, p1y = exterior[0]
        for i in range(1, n + 1):
            p2x, p2y = exterior[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    @property
    def centroid(self) -> GeoPoint:
        """
        Calculate the centroid of the polygon.

        Returns:
            A GeoPoint at the centroid location.
        """
        exterior = self.exterior
        if not exterior:
            raise ValueError("Cannot calculate centroid of empty polygon")

        # Simple centroid calculation (average of vertices)
        # For production, use proper weighted centroid algorithm
        n = len(exterior) - 1  # Exclude closing point
        if n < 1:
            raise ValueError("Polygon must have at least one vertex")

        sum_lon = sum(coord[0] for coord in exterior[:-1])
        sum_lat = sum(coord[1] for coord in exterior[:-1])

        return GeoPoint(longitude=sum_lon / n, latitude=sum_lat / n)

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        """
        Calculate the bounding box.

        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat).
        """
        exterior = self.exterior
        if not exterior:
            raise ValueError("Cannot calculate bbox of empty polygon")

        lons = [coord[0] for coord in exterior]
        lats = [coord[1] for coord in exterior]

        return (min(lons), min(lats), max(lons), max(lats))


@dataclass
class GeoLine:
    """
    A geographic line (LineString) representing a path on Earth.

    Attributes:
        coordinates: List of [lon, lat] coordinate tuples forming the line.
        properties: Additional metadata associated with this line.
    """

    coordinates: list[tuple[float, float]]
    properties: dict[str, Any] = field(default_factory=dict)

    def to_geojson(self) -> dict[str, Any]:
        """Convert to GeoJSON LineString geometry."""
        return {
            "type": "LineString",
            "coordinates": [[lon, lat] for lon, lat in self.coordinates],
        }

    def to_feature(self) -> dict[str, Any]:
        """Convert to GeoJSON Feature with properties."""
        return {
            "type": "Feature",
            "geometry": self.to_geojson(),
            "properties": self.properties,
        }

    @property
    def length_km(self) -> float:
        """
        Calculate the total length of the line in kilometers.

        Returns:
            Total distance along the line.
        """
        total = 0.0
        for i in range(1, len(self.coordinates)):
            p1 = GeoPoint(longitude=self.coordinates[i - 1][0], latitude=self.coordinates[i - 1][1])
            p2 = GeoPoint(longitude=self.coordinates[i][0], latitude=self.coordinates[i][1])
            total += p1.distance_to(p2)
        return total

    @property
    def start_point(self) -> GeoPoint:
        """Return the starting point of the line."""
        if not self.coordinates:
            raise ValueError("Line has no coordinates")
        lon, lat = self.coordinates[0]
        return GeoPoint(longitude=lon, latitude=lat)

    @property
    def end_point(self) -> GeoPoint:
        """Return the ending point of the line."""
        if not self.coordinates:
            raise ValueError("Line has no coordinates")
        lon, lat = self.coordinates[-1]
        return GeoPoint(longitude=lon, latitude=lat)

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        """
        Calculate the bounding box.

        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat).
        """
        if not self.coordinates:
            raise ValueError("Cannot calculate bbox of empty line")

        lons = [coord[0] for coord in self.coordinates]
        lats = [coord[1] for coord in self.coordinates]

        return (min(lons), min(lats), max(lons), max(lats))
