/**
 * Forge Atlas Layers
 *
 * Layer components and hooks for map visualization.
 */

// Point Layer
export {
  PointLayer,
  usePointLayer,
  createColorScale,
  createRadiusScale,
  getPositionFromFeature,
  default as PointLayerDefault,
} from './PointLayer';
export type { PointLayerProps } from './PointLayer';

// Polygon Layer
export {
  PolygonLayer,
  usePolygonLayer,
  createChoroplethColor,
  default as PolygonLayerDefault,
} from './PolygonLayer';
export type { PolygonLayerProps } from './PolygonLayer';

// Cluster Layer
export {
  ClusterLayer,
  useClusterLayer,
  defaultClusterColor,
  defaultClusterRadius,
  default as ClusterLayerDefault,
} from './ClusterLayer';
export type { ClusterLayerProps, ClusterFeature, UseClusterLayerOptions, UseClusterLayerReturn } from './ClusterLayer';

// Heatmap Layer
export {
  HeatmapLayer,
  useHeatmapLayer,
  createColorGradient,
  DEFAULT_HEATMAP_COLORS,
  COOL_HEATMAP_COLORS,
  VIRIDIS_HEATMAP_COLORS,
  default as HeatmapLayerDefault,
} from './HeatmapLayer';
export type { HeatmapLayerProps } from './HeatmapLayer';
