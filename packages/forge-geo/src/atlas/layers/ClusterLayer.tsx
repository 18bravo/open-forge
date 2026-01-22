/**
 * Cluster Layer Component
 *
 * Renders clustered point features using Supercluster for efficient client-side clustering.
 */

import React, { useMemo, useState, useCallback } from 'react';
import type { ClusterLayerConfig, GeoJSONFeature, RGBAColor, Coordinate, Viewport, BoundingBox } from '../types';

// ============================================================================
// Types
// ============================================================================

export interface ClusterLayerProps {
  /** Layer ID */
  id: string;
  /** Point feature data */
  data: GeoJSONFeature[];
  /** Cluster radius in pixels */
  clusterRadius?: number;
  /** Max zoom level to cluster at */
  clusterMaxZoom?: number;
  /** Min points to form a cluster */
  clusterMinPoints?: number;
  /** Get cluster color based on point count */
  getClusterColor?: (pointCount: number) => RGBAColor;
  /** Get cluster radius based on point count */
  getClusterRadius?: (pointCount: number) => number;
  /** Unclustered point color */
  pointColor?: RGBAColor | ((feature: GeoJSONFeature) => RGBAColor);
  /** Unclustered point radius */
  pointRadius?: number | ((feature: GeoJSONFeature) => number);
  /** Enable picking */
  pickable?: boolean;
  /** Layer visibility */
  visible?: boolean;
  /** Layer opacity */
  opacity?: number;
  /** Cluster click handler */
  onClusterClick?: (cluster: ClusterFeature) => void;
  /** Point click handler */
  onPointClick?: (feature: GeoJSONFeature) => void;
}

export interface ClusterFeature {
  /** Cluster ID */
  id: number;
  /** Cluster center coordinates */
  coordinates: Coordinate;
  /** Number of points in cluster */
  pointCount: number;
  /** Is this a cluster or single point */
  isCluster: boolean;
  /** Expansion zoom level */
  expansionZoom?: number;
  /** Original features (if single point) */
  properties?: Record<string, unknown>;
}

// ============================================================================
// Default Values
// ============================================================================

const DEFAULT_CLUSTER_RADIUS = 40;
const DEFAULT_MAX_ZOOM = 16;
const DEFAULT_MIN_POINTS = 2;

const DEFAULT_CLUSTER_COLORS: [number, RGBAColor][] = [
  [10, [255, 255, 178, 255]],
  [50, [254, 204, 92, 255]],
  [100, [253, 141, 60, 255]],
  [500, [240, 59, 32, 255]],
  [Infinity, [189, 0, 38, 255]],
];

/**
 * Default cluster color function based on point count
 */
export function defaultClusterColor(pointCount: number): RGBAColor {
  for (const [threshold, color] of DEFAULT_CLUSTER_COLORS) {
    if (pointCount < threshold) {
      return color;
    }
  }
  return DEFAULT_CLUSTER_COLORS[DEFAULT_CLUSTER_COLORS.length - 1][1];
}

/**
 * Default cluster radius function based on point count
 */
export function defaultClusterRadius(pointCount: number): number {
  return Math.min(100, 10 + Math.sqrt(pointCount) * 3);
}

// ============================================================================
// Hook: useClusterLayer
// ============================================================================

export interface UseClusterLayerOptions extends ClusterLayerProps {
  /** Current viewport for bounds calculation */
  viewport?: Viewport;
}

export interface UseClusterLayerReturn {
  /** Layer configuration */
  config: ClusterLayerConfig;
  /** Clustered features for current viewport */
  clusters: ClusterFeature[];
  /** Set viewport bounds */
  setBounds: (bounds: BoundingBox, zoom: number) => void;
  /** Expand a cluster */
  expandCluster: (clusterId: number) => number;
  /** Get cluster children */
  getClusterChildren: (clusterId: number) => GeoJSONFeature[];
}

/**
 * Hook for cluster layer with Supercluster integration
 *
 * @example
 * ```tsx
 * const { config, clusters, setBounds } = useClusterLayer({
 *   id: 'earthquakes',
 *   data: earthquakeData,
 *   clusterRadius: 50,
 * });
 *
 * useEffect(() => {
 *   if (viewport) {
 *     setBounds(calculateBounds(viewport), viewport.zoom);
 *   }
 * }, [viewport, setBounds]);
 *
 * return <ForgeMap layers={[config]} />;
 * ```
 */
export function useClusterLayer(options: UseClusterLayerOptions): UseClusterLayerReturn {
  const {
    id,
    data,
    clusterRadius = DEFAULT_CLUSTER_RADIUS,
    clusterMaxZoom = DEFAULT_MAX_ZOOM,
    clusterMinPoints = DEFAULT_MIN_POINTS,
    getClusterColor = defaultClusterColor,
    getClusterRadius = defaultClusterRadius,
    pointColor = [255, 140, 0, 200],
    pointRadius = 8,
    pickable = true,
    visible = true,
    opacity = 1,
  } = options;

  const [bounds, setBoundsState] = useState<BoundingBox | null>(null);
  const [zoom, setZoom] = useState(0);

  // Stub for supercluster index
  // In production, this would use the supercluster library
  const clusterIndex = useMemo(() => {
    // const index = new Supercluster({
    //   radius: clusterRadius,
    //   maxZoom: clusterMaxZoom,
    //   minPoints: clusterMinPoints,
    // });
    // const points = data.map(f => ({
    //   type: 'Feature',
    //   geometry: f.geometry,
    //   properties: f.properties,
    // }));
    // index.load(points);
    // return index;
    return null;
  }, [data, clusterRadius, clusterMaxZoom, clusterMinPoints]);

  // Calculate clusters for current viewport
  const clusters = useMemo((): ClusterFeature[] => {
    if (!clusterIndex || !bounds) {
      // Return all points as individual features when clustering not available
      return data.map((f, i) => ({
        id: i,
        coordinates: f.geometry.coordinates as Coordinate,
        pointCount: 1,
        isCluster: false,
        properties: f.properties,
      }));
    }

    // const rawClusters = clusterIndex.getClusters(bounds, Math.floor(zoom));
    // return rawClusters.map(c => ({
    //   id: c.id ?? c.properties.cluster_id,
    //   coordinates: c.geometry.coordinates,
    //   pointCount: c.properties.point_count ?? 1,
    //   isCluster: !!c.properties.cluster,
    //   expansionZoom: c.properties.cluster ? clusterIndex.getClusterExpansionZoom(c.id) : undefined,
    //   properties: c.properties,
    // }));
    return [];
  }, [clusterIndex, bounds, zoom, data]);

  const setBounds = useCallback((newBounds: BoundingBox, newZoom: number) => {
    setBoundsState(newBounds);
    setZoom(newZoom);
  }, []);

  const expandCluster = useCallback((clusterId: number): number => {
    // if (clusterIndex) {
    //   return clusterIndex.getClusterExpansionZoom(clusterId);
    // }
    return zoom + 2;
  }, [zoom]);

  const getClusterChildren = useCallback((clusterId: number): GeoJSONFeature[] => {
    // if (clusterIndex) {
    //   return clusterIndex.getLeaves(clusterId, 100);
    // }
    return [];
  }, []);

  const config: ClusterLayerConfig = {
    type: 'cluster',
    id,
    data,
    visible,
    opacity,
    pickable,
    clusterRadius,
    clusterMaxZoom,
    clusterMinPoints,
    getClusterColor,
    getClusterRadius,
    getPointColor: typeof pointColor === 'function' ? pointColor : pointColor,
    getPointRadius: typeof pointRadius === 'function' ? pointRadius : pointRadius,
  };

  return {
    config,
    clusters,
    setBounds,
    expandCluster,
    getClusterChildren,
  };
}

// ============================================================================
// Component: ClusterLayer
// ============================================================================

/**
 * Cluster Layer
 *
 * A declarative component for rendering clustered point features.
 * Must be used as a child of ForgeMap.
 *
 * @example
 * ```tsx
 * <ForgeMap initialViewport={viewport}>
 *   <ClusterLayer
 *     id="earthquakes"
 *     data={earthquakeData}
 *     clusterRadius={50}
 *     onClusterClick={(cluster) => {
 *       // Zoom to expand cluster
 *       setViewport({ ...viewport, zoom: cluster.expansionZoom });
 *     }}
 *   />
 * </ForgeMap>
 * ```
 */
export function ClusterLayer(_props: ClusterLayerProps): React.ReactElement | null {
  // Declarative configuration wrapper - parent ForgeMap handles rendering
  return null;
}

// Mark as layer component for parent detection
ClusterLayer.isForgeLayer = true;
ClusterLayer.layerType = 'cluster';

// ============================================================================
// Exports
// ============================================================================

export default ClusterLayer;
