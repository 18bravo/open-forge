# Track E: Forge Geo Platform Design

**Date:** 2026-01-20
**Status:** Draft
**Track:** E - Geospatial
**Dependencies:** api, ontology, ui-components

---

## Executive Summary

Track E implements geospatial capabilities for Open Forge, providing map visualization, spatial queries, movement tracking, and network analysis. This track addresses ~12+ geospatial features that enable location-based analytics.

### Key Packages

| Package | Purpose |
|---------|---------|
| `forge-geo-core` | Spatial primitives & queries |
| `forge-atlas` | Map visualization app |
| `forge-tracks` | Movement & trajectory analysis |
| `forge-routes` | Network & routing analysis |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FORGE GEO PLATFORM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         FORGE ATLAS (UI)                               │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐  │  │
│  │  │    Map    │  │   Layer   │  │   Draw    │  │    Popup/Info     │  │  │
│  │  │  Canvas   │  │  Controls │  │  Controls │  │    Panels         │  │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  FORGE TRACKS   │  │  FORGE ROUTES   │  │     FORGE GEO CORE          │  │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────────────────┤  │
│  │  Trajectories   │  │  Network Graph  │  │  Spatial Types              │  │
│  │  Movement Flow  │  │  Routing Engine │  │  Spatial Indexes            │  │
│  │  Clustering     │  │  Shortest Path  │  │  Spatial Queries            │  │
│  │  Anomaly Detect │  │  Isochrones     │  │  Coordinate Systems         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       SPATIAL DATABASE                                 │  │
│  │  ┌──────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │  │
│  │  │   PostGIS    │  │     H3     │  │  GeoHash   │  │    R-Tree    │  │  │
│  │  │  Extensions  │  │   Index    │  │   Index    │  │    Index     │  │  │
│  │  └──────────────┘  └────────────┘  └────────────┘  └──────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Package 1: Forge Geo Core

### Purpose

Core spatial primitives, coordinate systems, spatial indexes, and query operations.

### Module Structure

```
packages/forge-geo-core/
├── src/
│   └── forge_geo/
│       ├── __init__.py
│       ├── types/
│       │   ├── __init__.py
│       │   ├── point.py           # Point geometry
│       │   ├── polygon.py         # Polygon geometry
│       │   ├── line.py            # LineString geometry
│       │   ├── collection.py      # GeometryCollection
│       │   └── feature.py         # GeoJSON Feature
│       ├── indexes/
│       │   ├── __init__.py
│       │   ├── rtree.py           # R-Tree spatial index
│       │   ├── h3.py              # H3 hexagonal index
│       │   └── geohash.py         # GeoHash index
│       ├── queries/
│       │   ├── __init__.py
│       │   ├── bbox.py            # Bounding box queries
│       │   ├── intersection.py    # Intersection tests
│       │   ├── distance.py        # Distance calculations
│       │   ├── within.py          # Contains/within tests
│       │   └── nearest.py         # K-nearest neighbors
│       ├── transforms/
│       │   ├── __init__.py
│       │   ├── projection.py      # Coordinate projection
│       │   ├── simplify.py        # Geometry simplification
│       │   └── buffer.py          # Buffer operations
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# types/point.py
from pydantic import BaseModel
from typing import Any
import math

class Point(BaseModel):
    """A geographic point."""
    longitude: float
    latitude: float
    altitude: float | None = None
    properties: dict[str, Any] = {}

    @property
    def coordinates(self) -> tuple[float, float]:
        return (self.longitude, self.latitude)

    def to_geojson(self) -> dict:
        return {
            "type": "Point",
            "coordinates": [self.longitude, self.latitude]
        }

    def distance_to(self, other: "Point", unit: str = "km") -> float:
        """Calculate Haversine distance to another point."""
        R = 6371  # Earth radius in km

        lat1, lat2 = math.radians(self.latitude), math.radians(other.latitude)
        dlat = math.radians(other.latitude - self.latitude)
        dlon = math.radians(other.longitude - self.longitude)

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        distance_km = R * c

        if unit == "m":
            return distance_km * 1000
        elif unit == "mi":
            return distance_km * 0.621371
        return distance_km

    def bearing_to(self, other: "Point") -> float:
        """Calculate bearing to another point in degrees."""
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(other.latitude)
        dlon = math.radians(other.longitude - self.longitude)

        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360
```

```python
# types/polygon.py
from shapely.geometry import Polygon as ShapelyPolygon, Point as ShapelyPoint

class Polygon(BaseModel):
    """A geographic polygon."""
    coordinates: list[list[tuple[float, float]]]  # Exterior ring + holes
    properties: dict[str, Any] = {}

    @property
    def exterior(self) -> list[tuple[float, float]]:
        return self.coordinates[0]

    @property
    def holes(self) -> list[list[tuple[float, float]]]:
        return self.coordinates[1:] if len(self.coordinates) > 1 else []

    def to_geojson(self) -> dict:
        return {
            "type": "Polygon",
            "coordinates": self.coordinates
        }

    def to_shapely(self) -> ShapelyPolygon:
        return ShapelyPolygon(self.exterior, self.holes)

    def contains_point(self, point: Point) -> bool:
        shapely_poly = self.to_shapely()
        shapely_point = ShapelyPoint(point.longitude, point.latitude)
        return shapely_poly.contains(shapely_point)

    @property
    def area(self) -> float:
        """Calculate area in square kilometers."""
        from pyproj import Geod
        geod = Geod(ellps="WGS84")
        area, _ = geod.geometry_area_perimeter(self.to_shapely())
        return abs(area) / 1_000_000  # Convert to km²

    @property
    def centroid(self) -> Point:
        shapely_poly = self.to_shapely()
        c = shapely_poly.centroid
        return Point(longitude=c.x, latitude=c.y)

    def buffer(self, distance_km: float) -> "Polygon":
        """Create buffer around polygon."""
        from pyproj import Transformer
        import shapely.ops

        # Transform to meters, buffer, transform back
        transformer_to = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        transformer_from = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

        projected = shapely.ops.transform(transformer_to.transform, self.to_shapely())
        buffered = projected.buffer(distance_km * 1000)
        result = shapely.ops.transform(transformer_from.transform, buffered)

        return Polygon(coordinates=[list(result.exterior.coords)])
```

```python
# indexes/h3.py
import h3

class H3Index:
    """H3 hexagonal hierarchical spatial index."""

    def __init__(self, resolution: int = 9):
        self.resolution = resolution

    def point_to_cell(self, point: Point) -> str:
        """Get H3 cell for a point."""
        return h3.latlng_to_cell(point.latitude, point.longitude, self.resolution)

    def cell_to_boundary(self, cell: str) -> Polygon:
        """Get polygon boundary of H3 cell."""
        boundary = h3.cell_to_boundary(cell)
        # h3 returns (lat, lng), we need (lng, lat)
        coords = [(lng, lat) for lat, lng in boundary]
        coords.append(coords[0])  # Close ring
        return Polygon(coordinates=[coords])

    def cells_in_polygon(self, polygon: Polygon) -> list[str]:
        """Get all H3 cells within a polygon."""
        geojson = polygon.to_geojson()
        return list(h3.polygon_to_cells(geojson, self.resolution))

    def cell_ring(self, cell: str, k: int = 1) -> list[str]:
        """Get ring of cells at distance k."""
        return list(h3.grid_ring(cell, k))

    def cell_neighbors(self, cell: str, k: int = 1) -> list[str]:
        """Get all neighbors within distance k."""
        return list(h3.grid_disk(cell, k))

    def cells_to_multipolygon(self, cells: list[str]) -> dict:
        """Convert cells to unified polygon (GeoJSON)."""
        return h3.cells_to_h3shape(cells).__geo_interface__

    def compact_cells(self, cells: list[str]) -> list[str]:
        """Compact cells to larger cells where possible."""
        return list(h3.compact_cells(cells))

    def parent_cell(self, cell: str, parent_res: int | None = None) -> str:
        """Get parent cell at lower resolution."""
        if parent_res is None:
            parent_res = h3.get_resolution(cell) - 1
        return h3.cell_to_parent(cell, parent_res)
```

```python
# queries/distance.py
from typing import AsyncIterator
import asyncpg

class DistanceQuery:
    """Spatial distance queries using PostGIS."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def points_within_distance(
        self,
        center: Point,
        distance_km: float,
        table: str,
        geom_column: str = "geom",
        limit: int = 1000
    ) -> list[dict]:
        """Find all points within distance of center."""
        query = f"""
        SELECT *,
               ST_Distance(
                   {geom_column}::geography,
                   ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
               ) / 1000 as distance_km
        FROM {table}
        WHERE ST_DWithin(
            {geom_column}::geography,
            ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
            $3 * 1000
        )
        ORDER BY distance_km
        LIMIT $4
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                query,
                center.longitude,
                center.latitude,
                distance_km,
                limit
            )
            return [dict(row) for row in rows]

    async def k_nearest_neighbors(
        self,
        point: Point,
        table: str,
        k: int = 10,
        geom_column: str = "geom"
    ) -> list[dict]:
        """Find k nearest neighbors using KNN index."""
        query = f"""
        SELECT *,
               ST_Distance(
                   {geom_column}::geography,
                   ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
               ) / 1000 as distance_km
        FROM {table}
        ORDER BY {geom_column} <-> ST_SetSRID(ST_MakePoint($1, $2), 4326)
        LIMIT $3
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                query,
                point.longitude,
                point.latitude,
                k
            )
            return [dict(row) for row in rows]

    async def distance_matrix(
        self,
        origins: list[Point],
        destinations: list[Point]
    ) -> list[list[float]]:
        """Calculate distance matrix between points."""
        matrix = []

        for origin in origins:
            row = []
            for dest in destinations:
                dist = origin.distance_to(dest)
                row.append(dist)
            matrix.append(row)

        return matrix
```

```python
# queries/intersection.py
class IntersectionQuery:
    """Spatial intersection queries."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def polygons_intersecting(
        self,
        polygon: Polygon,
        table: str,
        geom_column: str = "geom"
    ) -> list[dict]:
        """Find all geometries intersecting a polygon."""
        query = f"""
        SELECT *
        FROM {table}
        WHERE ST_Intersects(
            {geom_column},
            ST_SetSRID(ST_GeomFromGeoJSON($1), 4326)
        )
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, json.dumps(polygon.to_geojson()))
            return [dict(row) for row in rows]

    async def points_in_polygon(
        self,
        polygon: Polygon,
        table: str,
        geom_column: str = "geom"
    ) -> list[dict]:
        """Find all points within a polygon."""
        query = f"""
        SELECT *
        FROM {table}
        WHERE ST_Within(
            {geom_column},
            ST_SetSRID(ST_GeomFromGeoJSON($1), 4326)
        )
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, json.dumps(polygon.to_geojson()))
            return [dict(row) for row in rows]

    async def intersection_area(
        self,
        polygon1: Polygon,
        polygon2: Polygon
    ) -> float:
        """Calculate intersection area between two polygons."""
        query = """
        SELECT ST_Area(
            ST_Intersection(
                ST_SetSRID(ST_GeomFromGeoJSON($1), 4326)::geography,
                ST_SetSRID(ST_GeomFromGeoJSON($2), 4326)::geography
            )
        ) / 1000000 as area_km2
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                json.dumps(polygon1.to_geojson()),
                json.dumps(polygon2.to_geojson())
            )
            return row["area_km2"]
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/geo", tags=["geo"])

@router.post("/distance")
async def calculate_distance(
    point1: Point,
    point2: Point,
    unit: Literal["km", "m", "mi"] = "km"
) -> dict:
    """Calculate distance between two points."""
    pass

@router.post("/within-distance")
async def points_within_distance(
    center: Point,
    distance_km: float,
    dataset_id: str,
    limit: int = 1000
) -> list[dict]:
    """Find points within distance of center."""
    pass

@router.post("/nearest")
async def find_nearest(
    point: Point,
    dataset_id: str,
    k: int = 10
) -> list[dict]:
    """Find k nearest neighbors."""
    pass

@router.post("/in-polygon")
async def points_in_polygon(
    polygon: Polygon,
    dataset_id: str
) -> list[dict]:
    """Find points within polygon."""
    pass

@router.post("/h3/cell")
async def point_to_h3(
    point: Point,
    resolution: int = 9
) -> dict:
    """Get H3 cell for point."""
    pass

@router.post("/h3/polygon")
async def h3_polygon(
    polygon: Polygon,
    resolution: int = 9
) -> list[str]:
    """Get H3 cells covering polygon."""
    pass

@router.post("/buffer")
async def buffer_geometry(
    geometry: dict,
    distance_km: float
) -> dict:
    """Create buffer around geometry."""
    pass
```

---

## Package 2: Forge Atlas

### Purpose

Interactive map visualization application with multiple layer types, drawing tools, and ontology integration.

### Module Structure

```
packages/forge-atlas/
├── src/
│   ├── components/
│   │   ├── Map.tsx                # Main map component
│   │   ├── layers/
│   │   │   ├── PointLayer.tsx
│   │   │   ├── PolygonLayer.tsx
│   │   │   ├── LineLayer.tsx
│   │   │   ├── ClusterLayer.tsx
│   │   │   ├── HeatmapLayer.tsx
│   │   │   ├── GridLayer.tsx
│   │   │   └── RasterLayer.tsx
│   │   ├── controls/
│   │   │   ├── ZoomControl.tsx
│   │   │   ├── LayerControl.tsx
│   │   │   ├── DrawControl.tsx
│   │   │   ├── MeasureControl.tsx
│   │   │   └── SearchControl.tsx
│   │   ├── popups/
│   │   │   ├── ObjectPopup.tsx
│   │   │   └── ClusterPopup.tsx
│   │   └── panels/
│   │       ├── LayerPanel.tsx
│   │       ├── FilterPanel.tsx
│   │       └── LegendPanel.tsx
│   ├── hooks/
│   │   ├── useMapData.ts
│   │   ├── useViewport.ts
│   │   ├── useLayers.ts
│   │   └── useDrawing.ts
│   ├── lib/
│   │   ├── mapbox.ts
│   │   ├── deckgl.ts
│   │   └── turf.ts
│   └── index.ts
├── package.json
└── tsconfig.json
```

### Core Components

```typescript
// components/Map.tsx
import { useRef, useEffect, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import { Deck } from '@deck.gl/core';
import { MapboxOverlay } from '@deck.gl/mapbox';

interface MapProps {
  initialViewport: {
    longitude: number;
    latitude: number;
    zoom: number;
    pitch?: number;
    bearing?: number;
  };
  layers: LayerConfig[];
  onViewportChange?: (viewport: Viewport) => void;
  onFeatureClick?: (feature: GeoFeature) => void;
  onFeatureHover?: (feature: GeoFeature | null) => void;
  basemap?: 'streets' | 'satellite' | 'dark' | 'light';
  interactive?: boolean;
}

export function ForgeMap({
  initialViewport,
  layers,
  onViewportChange,
  onFeatureClick,
  onFeatureHover,
  basemap = 'streets',
  interactive = true,
}: MapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const deckOverlay = useRef<MapboxOverlay | null>(null);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: getBasemapStyle(basemap),
      center: [initialViewport.longitude, initialViewport.latitude],
      zoom: initialViewport.zoom,
      pitch: initialViewport.pitch || 0,
      bearing: initialViewport.bearing || 0,
      interactive,
    });

    // Add deck.gl overlay
    deckOverlay.current = new MapboxOverlay({
      interleaved: true,
      onClick: (info) => {
        if (info.object && onFeatureClick) {
          onFeatureClick(info.object);
        }
      },
      onHover: (info) => {
        if (onFeatureHover) {
          onFeatureHover(info.object || null);
        }
      },
    });

    map.current.addControl(deckOverlay.current);

    map.current.on('move', () => {
      if (onViewportChange && map.current) {
        const center = map.current.getCenter();
        onViewportChange({
          longitude: center.lng,
          latitude: center.lat,
          zoom: map.current.getZoom(),
          pitch: map.current.getPitch(),
          bearing: map.current.getBearing(),
        });
      }
    });

    return () => {
      map.current?.remove();
    };
  }, []);

  // Update layers
  useEffect(() => {
    if (!deckOverlay.current) return;

    const deckLayers = layers.map(config => createDeckLayer(config));
    deckOverlay.current.setProps({ layers: deckLayers });
  }, [layers]);

  return (
    <div ref={mapContainer} className="w-full h-full" />
  );
}
```

```typescript
// components/layers/PointLayer.tsx
import { ScatterplotLayer, IconLayer } from '@deck.gl/layers';

interface PointLayerConfig {
  type: 'point';
  id: string;
  data: GeoFeature[];
  getPosition: (d: GeoFeature) => [number, number];
  getRadius?: (d: GeoFeature) => number;
  getColor?: (d: GeoFeature) => [number, number, number, number];
  radiusScale?: number;
  radiusMinPixels?: number;
  radiusMaxPixels?: number;
  pickable?: boolean;
  filled?: boolean;
  stroked?: boolean;
  lineWidthMinPixels?: number;
  // Icon mode
  iconAtlas?: string;
  iconMapping?: Record<string, IconDefinition>;
  getIcon?: (d: GeoFeature) => string;
}

export function createPointLayer(config: PointLayerConfig) {
  if (config.iconAtlas) {
    return new IconLayer({
      id: config.id,
      data: config.data,
      getPosition: config.getPosition,
      iconAtlas: config.iconAtlas,
      iconMapping: config.iconMapping,
      getIcon: config.getIcon,
      getSize: config.getRadius || 32,
      pickable: config.pickable ?? true,
    });
  }

  return new ScatterplotLayer({
    id: config.id,
    data: config.data,
    getPosition: config.getPosition,
    getRadius: config.getRadius || 100,
    getFillColor: config.getColor || [255, 140, 0, 200],
    getLineColor: [0, 0, 0, 255],
    radiusScale: config.radiusScale || 1,
    radiusMinPixels: config.radiusMinPixels || 2,
    radiusMaxPixels: config.radiusMaxPixels || 100,
    pickable: config.pickable ?? true,
    filled: config.filled ?? true,
    stroked: config.stroked ?? true,
    lineWidthMinPixels: config.lineWidthMinPixels || 1,
  });
}
```

```typescript
// components/layers/HeatmapLayer.tsx
import { HeatmapLayer as DeckHeatmapLayer } from '@deck.gl/aggregation-layers';

interface HeatmapConfig {
  type: 'heatmap';
  id: string;
  data: GeoFeature[];
  getPosition: (d: GeoFeature) => [number, number];
  getWeight?: (d: GeoFeature) => number;
  radiusPixels?: number;
  intensity?: number;
  threshold?: number;
  colorRange?: [number, number, number, number][];
}

export function createHeatmapLayer(config: HeatmapConfig) {
  return new DeckHeatmapLayer({
    id: config.id,
    data: config.data,
    getPosition: config.getPosition,
    getWeight: config.getWeight || 1,
    radiusPixels: config.radiusPixels || 30,
    intensity: config.intensity || 1,
    threshold: config.threshold || 0.05,
    colorRange: config.colorRange || [
      [255, 255, 178, 255],
      [254, 217, 118, 255],
      [254, 178, 76, 255],
      [253, 141, 60, 255],
      [252, 78, 42, 255],
      [227, 26, 28, 255],
      [177, 0, 38, 255],
    ],
    aggregation: 'SUM',
  });
}
```

```typescript
// components/layers/ClusterLayer.tsx
import Supercluster from 'supercluster';
import { useMemo, useEffect, useState } from 'react';

interface ClusterLayerProps {
  data: GeoFeature[];
  radius?: number;
  maxZoom?: number;
  minPoints?: number;
  getColor?: (count: number) => [number, number, number, number];
  getSize?: (count: number) => number;
  onClusterClick?: (cluster: ClusterFeature) => void;
}

export function useClusterLayer({
  data,
  radius = 40,
  maxZoom = 16,
  minPoints = 2,
}: ClusterLayerProps) {
  const [clusters, setClusters] = useState<ClusterFeature[]>([]);
  const [zoom, setZoom] = useState(0);
  const [bounds, setBounds] = useState<[number, number, number, number] | null>(null);

  const supercluster = useMemo(() => {
    const index = new Supercluster({
      radius,
      maxZoom,
      minPoints,
    });

    const points = data.map(d => ({
      type: 'Feature' as const,
      geometry: {
        type: 'Point' as const,
        coordinates: [d.geometry.coordinates[0], d.geometry.coordinates[1]],
      },
      properties: d.properties,
    }));

    index.load(points);
    return index;
  }, [data, radius, maxZoom, minPoints]);

  useEffect(() => {
    if (!bounds) return;

    const clusters = supercluster.getClusters(bounds, Math.floor(zoom));
    setClusters(clusters);
  }, [supercluster, bounds, zoom]);

  const expandCluster = (clusterId: number) => {
    const expansionZoom = supercluster.getClusterExpansionZoom(clusterId);
    return expansionZoom;
  };

  const getClusterLeaves = (clusterId: number, limit = 100) => {
    return supercluster.getLeaves(clusterId, limit);
  };

  return {
    clusters,
    setZoom,
    setBounds,
    expandCluster,
    getClusterLeaves,
  };
}
```

```typescript
// components/controls/DrawControl.tsx
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import { useEffect, useRef } from 'react';

interface DrawControlProps {
  map: mapboxgl.Map;
  onDrawCreate?: (features: GeoJSON.Feature[]) => void;
  onDrawUpdate?: (features: GeoJSON.Feature[]) => void;
  onDrawDelete?: (features: GeoJSON.Feature[]) => void;
  modes?: ('point' | 'line' | 'polygon' | 'circle')[];
}

export function useDrawControl({
  map,
  onDrawCreate,
  onDrawUpdate,
  onDrawDelete,
  modes = ['point', 'line', 'polygon'],
}: DrawControlProps) {
  const draw = useRef<MapboxDraw | null>(null);

  useEffect(() => {
    if (!map) return;

    draw.current = new MapboxDraw({
      displayControlsDefault: false,
      controls: {
        point: modes.includes('point'),
        line_string: modes.includes('line'),
        polygon: modes.includes('polygon'),
        trash: true,
      },
    });

    map.addControl(draw.current);

    map.on('draw.create', (e) => {
      onDrawCreate?.(e.features);
    });

    map.on('draw.update', (e) => {
      onDrawUpdate?.(e.features);
    });

    map.on('draw.delete', (e) => {
      onDrawDelete?.(e.features);
    });

    return () => {
      if (draw.current) {
        map.removeControl(draw.current);
      }
    };
  }, [map]);

  const setMode = (mode: string) => {
    draw.current?.changeMode(mode);
  };

  const getAll = () => {
    return draw.current?.getAll();
  };

  const deleteAll = () => {
    draw.current?.deleteAll();
  };

  const add = (geojson: GeoJSON.Feature | GeoJSON.FeatureCollection) => {
    return draw.current?.add(geojson);
  };

  return { setMode, getAll, deleteAll, add };
}
```

```typescript
// hooks/useMapData.ts
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';

interface UseMapDataOptions {
  datasetId: string;
  viewport?: Viewport;
  filters?: Record<string, any>;
  clustering?: boolean;
  clusterRadius?: number;
  simplify?: boolean;
  simplifyTolerance?: number;
}

export function useMapData({
  datasetId,
  viewport,
  filters,
  clustering = false,
  clusterRadius = 40,
  simplify = false,
  simplifyTolerance = 0.001,
}: UseMapDataOptions) {
  const bbox = useMemo(() => {
    if (!viewport) return null;
    return calculateBbox(viewport);
  }, [viewport]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['map-data', datasetId, bbox, filters, clustering],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (bbox) {
        params.set('bbox', bbox.join(','));
      }
      if (filters) {
        params.set('filters', JSON.stringify(filters));
      }
      if (clustering) {
        params.set('cluster', 'true');
        params.set('cluster_radius', String(clusterRadius));
      }
      if (simplify) {
        params.set('simplify', 'true');
        params.set('tolerance', String(simplifyTolerance));
      }

      const response = await fetch(
        `/api/v1/geo/datasets/${datasetId}/features?${params}`
      );
      return response.json();
    },
    enabled: !!datasetId,
  });

  return { features: data?.features || [], isLoading, error };
}
```

---

## Package 3: Forge Tracks

### Purpose

Movement tracking, trajectory analysis, flow visualization, and anomaly detection.

### Module Structure

```
packages/forge-tracks/
├── src/
│   └── forge_tracks/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── trajectory.py      # Trajectory model
│       │   ├── movement.py        # Movement events
│       │   └── flow.py            # Flow aggregation
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── clustering.py      # Trajectory clustering
│       │   ├── similarity.py      # Trajectory similarity
│       │   ├── anomaly.py         # Anomaly detection
│       │   └── prediction.py      # Movement prediction
│       ├── visualization/
│       │   ├── __init__.py
│       │   ├── flow_map.py        # Flow visualization
│       │   └── animation.py       # Animated tracks
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/trajectory.py
from pydantic import BaseModel
from datetime import datetime

class TrajectoryPoint(BaseModel):
    timestamp: datetime
    longitude: float
    latitude: float
    altitude: float | None = None
    speed: float | None = None
    heading: float | None = None
    accuracy: float | None = None
    properties: dict = {}

class Trajectory(BaseModel):
    id: str
    object_id: str
    points: list[TrajectoryPoint]
    start_time: datetime
    end_time: datetime
    properties: dict = {}

    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()

    @property
    def total_distance_km(self) -> float:
        """Calculate total distance traveled."""
        total = 0.0
        for i in range(1, len(self.points)):
            p1 = Point(longitude=self.points[i-1].longitude, latitude=self.points[i-1].latitude)
            p2 = Point(longitude=self.points[i].longitude, latitude=self.points[i].latitude)
            total += p1.distance_to(p2)
        return total

    @property
    def average_speed_kmh(self) -> float:
        """Calculate average speed."""
        hours = self.duration_seconds / 3600
        if hours == 0:
            return 0
        return self.total_distance_km / hours

    def simplify(self, tolerance: float = 0.0001) -> "Trajectory":
        """Simplify trajectory using Douglas-Peucker."""
        from shapely.geometry import LineString

        coords = [(p.longitude, p.latitude) for p in self.points]
        line = LineString(coords)
        simplified = line.simplify(tolerance, preserve_topology=True)

        # Match back to original points (keep timestamps)
        simplified_points = []
        for coord in simplified.coords:
            for p in self.points:
                if abs(p.longitude - coord[0]) < 1e-9 and abs(p.latitude - coord[1]) < 1e-9:
                    simplified_points.append(p)
                    break

        return Trajectory(
            id=self.id,
            object_id=self.object_id,
            points=simplified_points,
            start_time=self.start_time,
            end_time=self.end_time,
            properties=self.properties
        )

    def to_geojson(self) -> dict:
        """Convert to GeoJSON LineString."""
        return {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [p.longitude, p.latitude] for p in self.points
                ]
            },
            "properties": {
                "id": self.id,
                "object_id": self.object_id,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                **self.properties
            }
        }
```

```python
# analysis/clustering.py
from sklearn.cluster import DBSCAN
import numpy as np

class TrajectoryClustering:
    """Cluster trajectories by similarity."""

    def __init__(self, distance_metric: str = "frechet"):
        self.distance_metric = distance_metric

    def cluster(
        self,
        trajectories: list[Trajectory],
        eps: float = 0.5,
        min_samples: int = 2
    ) -> dict[int, list[Trajectory]]:
        """Cluster trajectories using DBSCAN."""
        # Compute pairwise distance matrix
        n = len(trajectories)
        distance_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                dist = self._trajectory_distance(trajectories[i], trajectories[j])
                distance_matrix[i, j] = dist
                distance_matrix[j, i] = dist

        # Run DBSCAN
        clustering = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric="precomputed"
        ).fit(distance_matrix)

        # Group by cluster
        clusters = {}
        for idx, label in enumerate(clustering.labels_):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(trajectories[idx])

        return clusters

    def _trajectory_distance(self, t1: Trajectory, t2: Trajectory) -> float:
        """Calculate distance between two trajectories."""
        if self.distance_metric == "frechet":
            return self._frechet_distance(t1, t2)
        elif self.distance_metric == "dtw":
            return self._dtw_distance(t1, t2)
        elif self.distance_metric == "hausdorff":
            return self._hausdorff_distance(t1, t2)
        raise ValueError(f"Unknown metric: {self.distance_metric}")

    def _frechet_distance(self, t1: Trajectory, t2: Trajectory) -> float:
        """Calculate Fréchet distance between trajectories."""
        import frechetdist

        coords1 = np.array([[p.longitude, p.latitude] for p in t1.points])
        coords2 = np.array([[p.longitude, p.latitude] for p in t2.points])

        return frechetdist.frdist(coords1, coords2)
```

```python
# analysis/anomaly.py
class TrajectoryAnomalyDetector:
    """Detect anomalous trajectories or movements."""

    def __init__(self):
        self._normal_patterns = []

    def fit(self, normal_trajectories: list[Trajectory]):
        """Learn normal movement patterns."""
        self._normal_patterns = normal_trajectories

    def detect_anomalies(
        self,
        trajectories: list[Trajectory],
        threshold: float = 2.0
    ) -> list[dict]:
        """Detect anomalous trajectories."""
        anomalies = []

        for traj in trajectories:
            # Check for various anomaly types
            speed_anomaly = self._check_speed_anomaly(traj, threshold)
            route_anomaly = self._check_route_anomaly(traj, threshold)
            time_anomaly = self._check_time_anomaly(traj, threshold)
            stop_anomaly = self._check_stop_anomaly(traj)

            if any([speed_anomaly, route_anomaly, time_anomaly, stop_anomaly]):
                anomalies.append({
                    "trajectory_id": traj.id,
                    "anomaly_types": {
                        "speed": speed_anomaly,
                        "route": route_anomaly,
                        "time": time_anomaly,
                        "stop": stop_anomaly
                    },
                    "score": self._calculate_anomaly_score(traj)
                })

        return anomalies

    def _check_speed_anomaly(self, traj: Trajectory, threshold: float) -> bool:
        """Check for unusual speeds."""
        for i in range(1, len(traj.points)):
            p1, p2 = traj.points[i-1], traj.points[i]
            point1 = Point(longitude=p1.longitude, latitude=p1.latitude)
            point2 = Point(longitude=p2.longitude, latitude=p2.latitude)

            dist = point1.distance_to(point2)
            time_diff = (p2.timestamp - p1.timestamp).total_seconds() / 3600

            if time_diff > 0:
                speed = dist / time_diff
                if speed > 200:  # > 200 km/h
                    return True

        return False

    def _check_stop_anomaly(self, traj: Trajectory) -> bool:
        """Detect unusual stops."""
        stops = []
        current_stop = None

        for i, point in enumerate(traj.points):
            if point.speed is not None and point.speed < 1:  # Stopped
                if current_stop is None:
                    current_stop = {"start": i, "points": [point]}
                else:
                    current_stop["points"].append(point)
            else:
                if current_stop and len(current_stop["points"]) > 2:
                    stop_duration = (
                        current_stop["points"][-1].timestamp -
                        current_stop["points"][0].timestamp
                    ).total_seconds()
                    stops.append({"duration": stop_duration, **current_stop})
                current_stop = None

        # Check for unusually long stops
        for stop in stops:
            if stop["duration"] > 3600:  # > 1 hour
                return True

        return False
```

```python
# models/flow.py
class FlowAggregator:
    """Aggregate trajectories into flow data."""

    def __init__(self, h3_resolution: int = 7):
        self.h3_resolution = h3_resolution

    def aggregate_flows(
        self,
        trajectories: list[Trajectory],
        time_bucket: str = "hour"  # hour, day, week
    ) -> list["FlowEdge"]:
        """Aggregate trajectories into origin-destination flows."""
        flows = {}

        for traj in trajectories:
            if len(traj.points) < 2:
                continue

            origin = traj.points[0]
            destination = traj.points[-1]

            origin_cell = h3.latlng_to_cell(origin.latitude, origin.longitude, self.h3_resolution)
            dest_cell = h3.latlng_to_cell(destination.latitude, destination.longitude, self.h3_resolution)

            time_key = self._get_time_bucket(traj.start_time, time_bucket)
            flow_key = (origin_cell, dest_cell, time_key)

            if flow_key not in flows:
                flows[flow_key] = {
                    "origin": origin_cell,
                    "destination": dest_cell,
                    "time_bucket": time_key,
                    "count": 0,
                    "total_duration": 0,
                    "total_distance": 0,
                    "trajectory_ids": []
                }

            flows[flow_key]["count"] += 1
            flows[flow_key]["total_duration"] += traj.duration_seconds
            flows[flow_key]["total_distance"] += traj.total_distance_km
            flows[flow_key]["trajectory_ids"].append(traj.id)

        return [FlowEdge(**f) for f in flows.values()]

    def create_flow_network(
        self,
        flows: list["FlowEdge"]
    ) -> "FlowNetwork":
        """Create network graph from flows."""
        import networkx as nx

        G = nx.DiGraph()

        for flow in flows:
            if G.has_edge(flow.origin, flow.destination):
                G[flow.origin][flow.destination]["weight"] += flow.count
            else:
                G.add_edge(
                    flow.origin,
                    flow.destination,
                    weight=flow.count,
                    avg_duration=flow.avg_duration,
                    avg_distance=flow.avg_distance
                )

        return FlowNetwork(graph=G, flows=flows)
```

---

## Package 4: Forge Routes

### Purpose

Network analysis, routing, isochrone generation, and accessibility analysis.

### Module Structure

```
packages/forge-routes/
├── src/
│   └── forge_routes/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── network.py         # Road network model
│       │   ├── route.py           # Route result
│       │   └── isochrone.py       # Isochrone model
│       ├── routing/
│       │   ├── __init__.py
│       │   ├── engine.py          # Routing engine
│       │   ├── dijkstra.py        # Dijkstra's algorithm
│       │   ├── astar.py           # A* algorithm
│       │   └── osrm.py            # OSRM integration
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── isochrone.py       # Isochrone generation
│       │   ├── accessibility.py   # Accessibility analysis
│       │   └── optimization.py    # Route optimization
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# routing/engine.py
from abc import ABC, abstractmethod

class RouteResult(BaseModel):
    distance_km: float
    duration_minutes: float
    geometry: list[tuple[float, float]]
    instructions: list[dict] = []
    waypoints: list[Point]

class RoutingEngine(ABC):
    """Abstract routing engine."""

    @abstractmethod
    async def route(
        self,
        origin: Point,
        destination: Point,
        waypoints: list[Point] | None = None,
        mode: str = "driving"
    ) -> RouteResult:
        pass

    @abstractmethod
    async def matrix(
        self,
        origins: list[Point],
        destinations: list[Point],
        mode: str = "driving"
    ) -> list[list[dict]]:
        pass

class OSRMRouter(RoutingEngine):
    """OSRM-based routing."""

    def __init__(self, osrm_url: str = "http://router.project-osrm.org"):
        self.osrm_url = osrm_url

    async def route(
        self,
        origin: Point,
        destination: Point,
        waypoints: list[Point] | None = None,
        mode: str = "driving"
    ) -> RouteResult:
        import httpx

        coords = [f"{origin.longitude},{origin.latitude}"]
        if waypoints:
            coords.extend([f"{wp.longitude},{wp.latitude}" for wp in waypoints])
        coords.append(f"{destination.longitude},{destination.latitude}")

        coords_str = ";".join(coords)
        url = f"{self.osrm_url}/route/v1/{mode}/{coords_str}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "true"
            })
            data = response.json()

        if data["code"] != "Ok":
            raise RoutingError(data.get("message", "Routing failed"))

        route = data["routes"][0]

        return RouteResult(
            distance_km=route["distance"] / 1000,
            duration_minutes=route["duration"] / 60,
            geometry=route["geometry"]["coordinates"],
            instructions=self._parse_instructions(route.get("legs", [])),
            waypoints=[
                Point(longitude=wp["location"][0], latitude=wp["location"][1])
                for wp in data["waypoints"]
            ]
        )

    async def matrix(
        self,
        origins: list[Point],
        destinations: list[Point],
        mode: str = "driving"
    ) -> list[list[dict]]:
        """Calculate distance/duration matrix."""
        import httpx

        all_coords = origins + destinations
        coords_str = ";".join([f"{p.longitude},{p.latitude}" for p in all_coords])

        sources = ";".join([str(i) for i in range(len(origins))])
        destinations_idx = ";".join([str(i) for i in range(len(origins), len(all_coords))])

        url = f"{self.osrm_url}/table/v1/{mode}/{coords_str}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={
                "sources": sources,
                "destinations": destinations_idx
            })
            data = response.json()

        if data["code"] != "Ok":
            raise RoutingError(data.get("message", "Matrix calculation failed"))

        # Build result matrix
        result = []
        for i, row in enumerate(data["durations"]):
            result_row = []
            for j, duration in enumerate(row):
                result_row.append({
                    "duration_minutes": duration / 60 if duration else None,
                    "distance_km": data["distances"][i][j] / 1000 if "distances" in data else None
                })
            result.append(result_row)

        return result
```

```python
# analysis/isochrone.py
class IsochroneGenerator:
    """Generate isochrones (reachability polygons)."""

    def __init__(self, router: RoutingEngine):
        self.router = router

    async def generate(
        self,
        center: Point,
        time_minutes: list[int],
        mode: str = "driving",
        resolution: int = 12  # Number of radial directions
    ) -> list[Polygon]:
        """Generate isochrone polygons for given travel times."""
        import numpy as np

        isochrones = []

        for max_time in time_minutes:
            # Sample points in radial directions
            boundary_points = []

            for angle in np.linspace(0, 360, resolution, endpoint=False):
                # Binary search for maximum reachable distance
                point = await self._find_boundary_point(
                    center, angle, max_time, mode
                )
                if point:
                    boundary_points.append(point)

            if len(boundary_points) >= 3:
                # Create polygon from boundary points
                coords = [(p.longitude, p.latitude) for p in boundary_points]
                coords.append(coords[0])  # Close ring
                isochrones.append(Polygon(
                    coordinates=[coords],
                    properties={"time_minutes": max_time}
                ))

        return isochrones

    async def _find_boundary_point(
        self,
        center: Point,
        bearing: float,
        max_time: float,
        mode: str
    ) -> Point | None:
        """Find the furthest reachable point in a direction."""
        import geopy.distance

        # Binary search for max reachable distance
        min_dist = 0
        max_dist = 100  # km

        for _ in range(10):  # Binary search iterations
            test_dist = (min_dist + max_dist) / 2

            # Calculate point at distance and bearing
            destination = geopy.distance.distance(kilometers=test_dist).destination(
                (center.latitude, center.longitude),
                bearing
            )
            test_point = Point(
                longitude=destination.longitude,
                latitude=destination.latitude
            )

            try:
                route = await self.router.route(center, test_point, mode=mode)
                if route.duration_minutes <= max_time:
                    min_dist = test_dist
                else:
                    max_dist = test_dist
            except:
                max_dist = test_dist

        if min_dist > 0:
            final = geopy.distance.distance(kilometers=min_dist).destination(
                (center.latitude, center.longitude),
                bearing
            )
            return Point(longitude=final.longitude, latitude=final.latitude)

        return None
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/routes", tags=["routes"])

@router.post("/route")
async def calculate_route(
    origin: Point,
    destination: Point,
    waypoints: list[Point] | None = None,
    mode: Literal["driving", "walking", "cycling"] = "driving"
) -> RouteResult:
    """Calculate route between points."""
    pass

@router.post("/matrix")
async def calculate_matrix(
    origins: list[Point],
    destinations: list[Point],
    mode: Literal["driving", "walking", "cycling"] = "driving"
) -> list[list[dict]]:
    """Calculate distance/duration matrix."""
    pass

@router.post("/isochrone")
async def generate_isochrone(
    center: Point,
    time_minutes: list[int] = [5, 10, 15],
    mode: Literal["driving", "walking", "cycling"] = "driving"
) -> list[dict]:
    """Generate isochrone polygons."""
    pass

@router.post("/optimize")
async def optimize_route(
    waypoints: list[Point],
    start: Point | None = None,
    end: Point | None = None,
    mode: Literal["driving", "walking", "cycling"] = "driving"
) -> dict:
    """Optimize waypoint order (TSP)."""
    pass
```

---

## Implementation Roadmap

### Phase E1: Geo Core + Atlas (Weeks 1-3)

**Deliverables:**
1. forge-geo-core with spatial types and queries
2. forge-atlas with map components
3. PostGIS and H3 integration
4. Basic layer types (point, polygon, line)

### Phase E2: Tracks + Routes (Weeks 4-6)

**Deliverables:**
1. forge-tracks with trajectory analysis
2. forge-routes with OSRM integration
3. Flow visualization
4. Isochrone generation

### Phase E3: Atlas Studio Widget (Week 7)

**Deliverables:**
1. Map widget for Forge Studio
2. Layer configuration UI
3. Drawing tools integration
