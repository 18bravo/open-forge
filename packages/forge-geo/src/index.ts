/**
 * Forge Geo
 *
 * Geospatial capabilities for Open Forge platform.
 *
 * This is a HYBRID package with both Python and TypeScript components:
 *
 * - **Python backend** (src/forge_geo/): Spatial primitives, indexes, queries, and API routes
 * - **TypeScript frontend** (src/atlas/): Map visualization with Mapbox/deck.gl
 *
 * ## Python Usage
 *
 * ```python
 * from forge_geo import GeoPoint, GeoPolygon, SpatialQuery, H3Index
 *
 * # Create spatial primitives
 * point = GeoPoint(longitude=-122.4, latitude=37.8)
 * polygon = GeoPolygon(coordinates=[[(-122.5, 37.7), (-122.3, 37.7), (-122.3, 37.9), (-122.5, 37.9), (-122.5, 37.7)]])
 *
 * # Calculate distance
 * point2 = GeoPoint(longitude=-122.0, latitude=37.5)
 * distance = point.distance_to(point2)  # in km
 *
 * # Use H3 indexing
 * h3 = H3Index(resolution=9)
 * cell_id = h3.index_point(point)
 *
 * # Build spatial queries
 * query = (
 *     SpatialQuery(table="locations")
 *     .bbox(-122.5, 37.7, -122.3, 37.9)
 *     .within_distance(point, 1000)
 *     .limit(100)
 * )
 * results = await query.execute(pool)
 * ```
 *
 * ## TypeScript Usage
 *
 * ```tsx
 * import { ForgeMap, PointLayer, HeatmapLayer, useMapData } from '@open-forge/forge-geo';
 *
 * function MapView() {
 *   const { features, isLoading } = useMapData({
 *     datasetId: 'earthquakes',
 *     viewport,
 *   });
 *
 *   return (
 *     <ForgeMap
 *       initialViewport={{ longitude: -122.4, latitude: 37.8, zoom: 10 }}
 *       layers={[
 *         { type: 'heatmap', id: 'density', data: features },
 *         { type: 'point', id: 'points', data: features },
 *       ]}
 *     />
 *   );
 * }
 * ```
 *
 * @packageDocumentation
 */

// ============================================================================
// Atlas Module (TypeScript Map Visualization)
// ============================================================================

export * from './atlas';

// ============================================================================
// Version
// ============================================================================

export const VERSION = '0.1.0';
