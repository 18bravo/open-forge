/**
 * useMapData Hook
 *
 * Hook for fetching and managing geospatial data for map visualization.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import type {
  UseMapDataOptions,
  UseMapDataReturn,
  GeoJSONFeature,
  Viewport,
  BoundingBox,
} from '../types';

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Calculate bounding box from viewport
 */
export function viewportToBounds(viewport: Viewport): BoundingBox {
  // Simplified calculation - in production, use mapbox-gl's getBounds()
  const latRange = 180 / Math.pow(2, viewport.zoom);
  const lonRange = 360 / Math.pow(2, viewport.zoom);

  return [
    viewport.longitude - lonRange / 2,
    viewport.latitude - latRange / 2,
    viewport.longitude + lonRange / 2,
    viewport.latitude + latRange / 2,
  ];
}

/**
 * Check if viewport has changed significantly
 */
function viewportChanged(prev: Viewport | undefined, next: Viewport): boolean {
  if (!prev) return true;

  const zoomThreshold = 0.5;
  const positionThreshold = 0.01;

  return (
    Math.abs(prev.zoom - next.zoom) > zoomThreshold ||
    Math.abs(prev.longitude - next.longitude) > positionThreshold ||
    Math.abs(prev.latitude - next.latitude) > positionThreshold
  );
}

// ============================================================================
// Hook: useMapData
// ============================================================================

/**
 * Hook for fetching geospatial data based on viewport
 *
 * @example
 * ```tsx
 * const { features, isLoading, error, refetch } = useMapData({
 *   datasetId: 'locations',
 *   viewport,
 *   clustering: true,
 * });
 *
 * return (
 *   <ForgeMap
 *     layers={[{ type: 'point', id: 'locations', data: features }]}
 *     onViewportChange={setViewport}
 *   />
 * );
 * ```
 */
export function useMapData(options: UseMapDataOptions): UseMapDataReturn {
  const {
    datasetId,
    viewport,
    filters,
    clustering = false,
    clusterRadius = 40,
    simplify = false,
    simplifyTolerance = 0.001,
    refetchOnViewportChange = true,
  } = options;

  const [features, setFeatures] = useState<GeoJSONFeature[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [totalCount, setTotalCount] = useState<number | undefined>(undefined);
  const [lastViewport, setLastViewport] = useState<Viewport | undefined>(undefined);

  // Calculate bounds from viewport
  const bounds = useMemo(() => {
    return viewport ? viewportToBounds(viewport) : null;
  }, [viewport]);

  // Fetch data function
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();

      if (bounds) {
        params.set('bbox', bounds.join(','));
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

      if (!response.ok) {
        throw new Error(`Failed to fetch data: ${response.statusText}`);
      }

      const data = await response.json();

      setFeatures(data.features || []);
      setTotalCount(data.total_count);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
      setFeatures([]);
    } finally {
      setIsLoading(false);
    }
  }, [datasetId, bounds, filters, clustering, clusterRadius, simplify, simplifyTolerance]);

  // Refetch when viewport changes significantly
  useEffect(() => {
    if (!datasetId) return;

    if (!refetchOnViewportChange) {
      // Only fetch once
      if (features.length === 0 && !isLoading) {
        fetchData();
      }
      return;
    }

    if (viewport && viewportChanged(lastViewport, viewport)) {
      setLastViewport(viewport);
      fetchData();
    }
  }, [datasetId, viewport, refetchOnViewportChange, fetchData, lastViewport, features.length, isLoading]);

  // Initial fetch
  useEffect(() => {
    if (datasetId && features.length === 0 && !isLoading && !error) {
      fetchData();
    }
  }, [datasetId, fetchData, features.length, isLoading, error]);

  return {
    features,
    isLoading,
    error,
    refetch: fetchData,
    totalCount,
  };
}

// ============================================================================
// Exports
// ============================================================================

export default useMapData;
