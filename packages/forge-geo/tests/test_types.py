"""
Tests for forge_geo.core.types module.

These are scaffold tests that verify the basic structure works.
"""

import pytest

from forge_geo.core.types import GeoLine, GeoPoint, GeoPolygon


class TestGeoPoint:
    """Tests for GeoPoint class."""

    def test_create_point(self) -> None:
        """Test basic point creation."""
        point = GeoPoint(longitude=-122.4, latitude=37.8)
        assert point.longitude == -122.4
        assert point.latitude == 37.8
        assert point.altitude is None

    def test_point_with_altitude(self) -> None:
        """Test point with altitude."""
        point = GeoPoint(longitude=-122.4, latitude=37.8, altitude=100.0)
        assert point.altitude == 100.0

    def test_coordinates_property(self) -> None:
        """Test coordinates tuple property."""
        point = GeoPoint(longitude=-122.4, latitude=37.8)
        assert point.coordinates == (-122.4, 37.8)

    def test_to_geojson(self) -> None:
        """Test GeoJSON conversion."""
        point = GeoPoint(longitude=-122.4, latitude=37.8)
        geojson = point.to_geojson()
        assert geojson["type"] == "Point"
        assert geojson["coordinates"] == [-122.4, 37.8]

    def test_distance_calculation(self) -> None:
        """Test distance calculation between points."""
        sf = GeoPoint(longitude=-122.4194, latitude=37.7749)
        la = GeoPoint(longitude=-118.2437, latitude=34.0522)

        distance = sf.distance_to(la)
        # SF to LA is approximately 560 km
        assert 550 < distance < 570

    def test_distance_units(self) -> None:
        """Test distance in different units."""
        p1 = GeoPoint(longitude=0, latitude=0)
        p2 = GeoPoint(longitude=1, latitude=0)

        km = p1.distance_to(p2, unit="km")
        m = p1.distance_to(p2, unit="m")
        mi = p1.distance_to(p2, unit="mi")

        assert abs(m - km * 1000) < 0.1
        assert abs(mi - km * 0.621371) < 0.1


class TestGeoPolygon:
    """Tests for GeoPolygon class."""

    def test_create_polygon(self) -> None:
        """Test basic polygon creation."""
        coords = [
            [(-122.5, 37.7), (-122.3, 37.7), (-122.3, 37.9), (-122.5, 37.9), (-122.5, 37.7)]
        ]
        polygon = GeoPolygon(coordinates=coords)
        assert polygon.exterior == coords[0]
        assert polygon.holes == []

    def test_polygon_with_hole(self) -> None:
        """Test polygon with interior hole."""
        exterior = [(-122.5, 37.7), (-122.3, 37.7), (-122.3, 37.9), (-122.5, 37.9), (-122.5, 37.7)]
        hole = [(-122.45, 37.75), (-122.35, 37.75), (-122.35, 37.85), (-122.45, 37.85), (-122.45, 37.75)]
        polygon = GeoPolygon(coordinates=[exterior, hole])

        assert polygon.exterior == exterior
        assert polygon.holes == [hole]

    def test_to_geojson(self) -> None:
        """Test GeoJSON conversion."""
        coords = [
            [(-122.5, 37.7), (-122.3, 37.7), (-122.3, 37.9), (-122.5, 37.9), (-122.5, 37.7)]
        ]
        polygon = GeoPolygon(coordinates=coords)
        geojson = polygon.to_geojson()

        assert geojson["type"] == "Polygon"
        assert len(geojson["coordinates"]) == 1

    def test_bbox(self) -> None:
        """Test bounding box calculation."""
        coords = [
            [(-122.5, 37.7), (-122.3, 37.7), (-122.3, 37.9), (-122.5, 37.9), (-122.5, 37.7)]
        ]
        polygon = GeoPolygon(coordinates=coords)
        bbox = polygon.bbox

        assert bbox == (-122.5, 37.7, -122.3, 37.9)


class TestGeoLine:
    """Tests for GeoLine class."""

    def test_create_line(self) -> None:
        """Test basic line creation."""
        coords = [(-122.4, 37.7), (-122.3, 37.8), (-122.2, 37.9)]
        line = GeoLine(coordinates=coords)
        assert line.coordinates == coords

    def test_to_geojson(self) -> None:
        """Test GeoJSON conversion."""
        coords = [(-122.4, 37.7), (-122.3, 37.8)]
        line = GeoLine(coordinates=coords)
        geojson = line.to_geojson()

        assert geojson["type"] == "LineString"
        assert len(geojson["coordinates"]) == 2

    def test_start_end_points(self) -> None:
        """Test start and end point properties."""
        coords = [(-122.4, 37.7), (-122.3, 37.8), (-122.2, 37.9)]
        line = GeoLine(coordinates=coords)

        assert line.start_point.coordinates == (-122.4, 37.7)
        assert line.end_point.coordinates == (-122.2, 37.9)

    def test_length(self) -> None:
        """Test line length calculation."""
        coords = [(-122.4, 37.7), (-122.3, 37.8), (-122.2, 37.9)]
        line = GeoLine(coordinates=coords)

        length = line.length_km
        assert length > 0
