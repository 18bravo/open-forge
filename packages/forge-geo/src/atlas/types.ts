/**
 * Forge Geo Atlas Type Definitions
 *
 * Core type definitions for map visualization components.
 */

// ============================================================================
// Geometry Types
// ============================================================================

/**
 * Geographic coordinate (longitude, latitude)
 */
export type Coordinate = [number, number];

/**
 * Geographic coordinate with optional altitude
 */
export type Coordinate3D = [number, number, number];

/**
 * Bounding box [minLon, minLat, maxLon, maxLat]
 */
export type BoundingBox = [number, number, number, number];

/**
 * RGBA color as [r, g, b, a] where each value is 0-255
 */
export type RGBAColor = [number, number, number, number];

/**
 * RGB color as [r, g, b] where each value is 0-255
 */
export type RGBColor = [number, number, number];

// ============================================================================
// GeoJSON Types (subset for map rendering)
// ============================================================================

export interface GeoJSONGeometry {
  type: 'Point' | 'LineString' | 'Polygon' | 'MultiPoint' | 'MultiLineString' | 'MultiPolygon';
  coordinates: unknown;
}

export interface GeoJSONFeature<G extends GeoJSONGeometry = GeoJSONGeometry, P = Record<string, unknown>> {
  type: 'Feature';
  geometry: G;
  properties: P;
  id?: string | number;
}

export interface GeoJSONFeatureCollection<G extends GeoJSONGeometry = GeoJSONGeometry, P = Record<string, unknown>> {
  type: 'FeatureCollection';
  features: GeoJSONFeature<G, P>[];
}

// ============================================================================
// Viewport Types
// ============================================================================

/**
 * Map viewport state
 */
export interface Viewport {
  /** Longitude of map center */
  longitude: number;
  /** Latitude of map center */
  latitude: number;
  /** Zoom level (0-22) */
  zoom: number;
  /** Pitch angle in degrees (0-85) */
  pitch?: number;
  /** Bearing angle in degrees (0-360) */
  bearing?: number;
}

/**
 * Extended viewport with transition info
 */
export interface ViewportState extends Viewport {
  /** Width in pixels */
  width?: number;
  /** Height in pixels */
  height?: number;
  /** Transition duration in ms */
  transitionDuration?: number;
}

// ============================================================================
// Layer Types
// ============================================================================

/**
 * Base configuration shared by all layers
 */
export interface BaseLayerConfig {
  /** Unique layer identifier */
  id: string;
  /** Layer visibility */
  visible?: boolean;
  /** Layer opacity (0-1) */
  opacity?: number;
  /** Enable picking (click/hover) */
  pickable?: boolean;
  /** Minimum zoom level for layer visibility */
  minZoom?: number;
  /** Maximum zoom level for layer visibility */
  maxZoom?: number;
}

/**
 * Point layer configuration
 */
export interface PointLayerConfig extends BaseLayerConfig {
  type: 'point';
  /** Feature data */
  data: GeoJSONFeature[] | GeoJSONFeatureCollection;
  /** Get position from feature */
  getPosition?: (feature: GeoJSONFeature) => Coordinate;
  /** Point radius in pixels or meters */
  getRadius?: number | ((feature: GeoJSONFeature) => number);
  /** Point fill color */
  getFillColor?: RGBAColor | ((feature: GeoJSONFeature) => RGBAColor);
  /** Point stroke color */
  getLineColor?: RGBAColor | ((feature: GeoJSONFeature) => RGBAColor);
  /** Use meters instead of pixels for radius */
  radiusUnits?: 'pixels' | 'meters';
  /** Minimum radius in pixels */
  radiusMinPixels?: number;
  /** Maximum radius in pixels */
  radiusMaxPixels?: number;
  /** Fill the points */
  filled?: boolean;
  /** Stroke the points */
  stroked?: boolean;
  /** Stroke width in pixels */
  lineWidthMinPixels?: number;
}

/**
 * Polygon layer configuration
 */
export interface PolygonLayerConfig extends BaseLayerConfig {
  type: 'polygon';
  /** Feature data */
  data: GeoJSONFeature[] | GeoJSONFeatureCollection;
  /** Get polygon coordinates from feature */
  getPolygon?: (feature: GeoJSONFeature) => Coordinate[][];
  /** Polygon fill color */
  getFillColor?: RGBAColor | ((feature: GeoJSONFeature) => RGBAColor);
  /** Polygon stroke color */
  getLineColor?: RGBAColor | ((feature: GeoJSONFeature) => RGBAColor);
  /** Fill the polygons */
  filled?: boolean;
  /** Stroke the polygons */
  stroked?: boolean;
  /** Stroke width in pixels */
  lineWidthMinPixels?: number;
  /** Extrusion height (for 3D) */
  getElevation?: number | ((feature: GeoJSONFeature) => number);
  /** Enable extrusion */
  extruded?: boolean;
}

/**
 * Cluster layer configuration
 */
export interface ClusterLayerConfig extends BaseLayerConfig {
  type: 'cluster';
  /** Point feature data */
  data: GeoJSONFeature[] | GeoJSONFeatureCollection;
  /** Get position from feature */
  getPosition?: (feature: GeoJSONFeature) => Coordinate;
  /** Cluster radius in pixels */
  clusterRadius?: number;
  /** Max zoom to cluster */
  clusterMaxZoom?: number;
  /** Min points to form cluster */
  clusterMinPoints?: number;
  /** Get color based on cluster point count */
  getClusterColor?: (pointCount: number) => RGBAColor;
  /** Get radius based on cluster point count */
  getClusterRadius?: (pointCount: number) => number;
  /** Unclustered point color */
  getPointColor?: RGBAColor | ((feature: GeoJSONFeature) => RGBAColor);
  /** Unclustered point radius */
  getPointRadius?: number | ((feature: GeoJSONFeature) => number);
}

/**
 * Heatmap layer configuration
 */
export interface HeatmapLayerConfig extends BaseLayerConfig {
  type: 'heatmap';
  /** Point feature data */
  data: GeoJSONFeature[] | GeoJSONFeatureCollection;
  /** Get position from feature */
  getPosition?: (feature: GeoJSONFeature) => Coordinate;
  /** Get weight value for each point */
  getWeight?: number | ((feature: GeoJSONFeature) => number);
  /** Radius of influence in pixels */
  radiusPixels?: number;
  /** Intensity multiplier */
  intensity?: number;
  /** Threshold for visibility */
  threshold?: number;
  /** Color gradient (array of RGBA colors) */
  colorRange?: RGBAColor[];
  /** Aggregation method */
  aggregation?: 'SUM' | 'MEAN';
}

/**
 * Union of all layer configurations
 */
export type LayerConfig =
  | PointLayerConfig
  | PolygonLayerConfig
  | ClusterLayerConfig
  | HeatmapLayerConfig;

// ============================================================================
// Map Component Types
// ============================================================================

/**
 * Basemap style options
 */
export type BasemapStyle = 'streets' | 'satellite' | 'dark' | 'light' | 'outdoors';

/**
 * Pick info returned when clicking/hovering features
 */
export interface PickInfo<T = GeoJSONFeature> {
  /** Picked object (feature) */
  object?: T;
  /** Index of picked object */
  index: number;
  /** Layer ID */
  layer: string;
  /** Screen x coordinate */
  x: number;
  /** Screen y coordinate */
  y: number;
  /** Geographic coordinate */
  coordinate?: Coordinate;
}

/**
 * Map component props
 */
export interface MapProps {
  /** Initial viewport configuration */
  initialViewport: Viewport;
  /** Array of layer configurations */
  layers: LayerConfig[];
  /** Callback when viewport changes */
  onViewportChange?: (viewport: Viewport) => void;
  /** Callback when a feature is clicked */
  onFeatureClick?: (info: PickInfo) => void;
  /** Callback when hovering over a feature */
  onFeatureHover?: (info: PickInfo | null) => void;
  /** Basemap style */
  basemap?: BasemapStyle;
  /** Enable map interactions */
  interactive?: boolean;
  /** Mapbox access token */
  mapboxAccessToken?: string;
  /** Additional CSS class */
  className?: string;
  /** Children (controls, popups) */
  children?: React.ReactNode;
}

// ============================================================================
// Control Types
// ============================================================================

/**
 * Control position on the map
 */
export type ControlPosition = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';

/**
 * Zoom control props
 */
export interface ZoomControlProps {
  /** Control position */
  position?: ControlPosition;
  /** Show compass */
  showCompass?: boolean;
  /** Show zoom buttons */
  showZoom?: boolean;
}

/**
 * Layer control props
 */
export interface LayerControlProps {
  /** Control position */
  position?: ControlPosition;
  /** Available layers */
  layers: Array<{
    id: string;
    label: string;
    visible: boolean;
  }>;
  /** Callback when layer visibility changes */
  onLayerToggle?: (layerId: string, visible: boolean) => void;
}

/**
 * Draw control mode
 */
export type DrawMode = 'point' | 'line' | 'polygon' | 'rectangle' | 'circle' | 'select';

/**
 * Draw control props
 */
export interface DrawControlProps {
  /** Control position */
  position?: ControlPosition;
  /** Enabled drawing modes */
  modes?: DrawMode[];
  /** Active drawing mode */
  activeMode?: DrawMode | null;
  /** Callback when mode changes */
  onModeChange?: (mode: DrawMode | null) => void;
  /** Callback when drawing is created */
  onDrawCreate?: (features: GeoJSONFeature[]) => void;
  /** Callback when drawing is updated */
  onDrawUpdate?: (features: GeoJSONFeature[]) => void;
  /** Callback when drawing is deleted */
  onDrawDelete?: (featureIds: (string | number)[]) => void;
}

// ============================================================================
// Hook Types
// ============================================================================

/**
 * Options for useMapData hook
 */
export interface UseMapDataOptions {
  /** Dataset identifier */
  datasetId: string;
  /** Current viewport (for bbox filtering) */
  viewport?: Viewport;
  /** Additional filters */
  filters?: Record<string, unknown>;
  /** Enable server-side clustering */
  clustering?: boolean;
  /** Cluster radius (if clustering enabled) */
  clusterRadius?: number;
  /** Enable geometry simplification */
  simplify?: boolean;
  /** Simplification tolerance */
  simplifyTolerance?: number;
  /** Auto-refetch on viewport change */
  refetchOnViewportChange?: boolean;
}

/**
 * Return type for useMapData hook
 */
export interface UseMapDataReturn {
  /** Feature data */
  features: GeoJSONFeature[];
  /** Loading state */
  isLoading: boolean;
  /** Error state */
  error: Error | null;
  /** Refetch data */
  refetch: () => void;
  /** Total feature count (server-side) */
  totalCount?: number;
}

/**
 * Options for useViewport hook
 */
export interface UseViewportOptions {
  /** Initial viewport */
  initial: Viewport;
  /** Viewport change callback */
  onChange?: (viewport: Viewport) => void;
  /** Debounce delay in ms */
  debounceMs?: number;
}

/**
 * Return type for useViewport hook
 */
export interface UseViewportReturn {
  /** Current viewport */
  viewport: Viewport;
  /** Set viewport */
  setViewport: (viewport: Viewport) => void;
  /** Fly to location */
  flyTo: (target: Partial<Viewport>, duration?: number) => void;
  /** Fit to bounds */
  fitBounds: (bounds: BoundingBox, padding?: number) => void;
  /** Reset to initial viewport */
  reset: () => void;
}
