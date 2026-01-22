/**
 * useViewport Hook
 *
 * Hook for managing map viewport state with transitions.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type { Viewport, BoundingBox, UseViewportOptions, UseViewportReturn } from '../types';

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Calculate viewport to fit bounds
 */
export function fitBoundsToViewport(
  bounds: BoundingBox,
  containerWidth: number,
  containerHeight: number,
  padding: number = 20
): Viewport {
  const [minLon, minLat, maxLon, maxLat] = bounds;

  const centerLon = (minLon + maxLon) / 2;
  const centerLat = (minLat + maxLat) / 2;

  const lonRange = maxLon - minLon;
  const latRange = maxLat - minLat;

  // Calculate zoom to fit bounds
  const paddedWidth = containerWidth - padding * 2;
  const paddedHeight = containerHeight - padding * 2;

  const lonZoom = Math.log2(360 / lonRange * paddedWidth / 512);
  const latZoom = Math.log2(180 / latRange * paddedHeight / 512);

  const zoom = Math.min(lonZoom, latZoom, 20);

  return {
    longitude: centerLon,
    latitude: centerLat,
    zoom: Math.max(0, zoom),
  };
}

/**
 * Debounce function
 */
function debounce<T extends (...args: unknown[]) => void>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

// ============================================================================
// Hook: useViewport
// ============================================================================

/**
 * Hook for managing map viewport state
 *
 * @example
 * ```tsx
 * const { viewport, setViewport, flyTo, fitBounds, reset } = useViewport({
 *   initial: { longitude: -122.4, latitude: 37.8, zoom: 10 },
 *   onChange: (v) => console.log('Viewport changed:', v),
 * });
 *
 * return (
 *   <ForgeMap
 *     initialViewport={viewport}
 *     onViewportChange={setViewport}
 *   >
 *     <button onClick={() => flyTo({ longitude: 0, latitude: 0, zoom: 2 })}>
 *       Go to Origin
 *     </button>
 *   </ForgeMap>
 * );
 * ```
 */
export function useViewport(options: UseViewportOptions): UseViewportReturn {
  const { initial, onChange, debounceMs = 100 } = options;

  const [viewport, setViewportState] = useState<Viewport>(initial);
  const initialRef = useRef(initial);

  // Debounced onChange callback
  const debouncedOnChange = useCallback(
    debounceMs > 0 && onChange
      ? debounce((v: Viewport) => onChange(v), debounceMs)
      : onChange || (() => {}),
    [onChange, debounceMs]
  );

  // Set viewport with callback
  const setViewport = useCallback(
    (newViewport: Viewport) => {
      setViewportState(newViewport);
      debouncedOnChange(newViewport);
    },
    [debouncedOnChange]
  );

  // Fly to a location with animation
  const flyTo = useCallback(
    (target: Partial<Viewport>, duration: number = 1000) => {
      const newViewport: Viewport = {
        ...viewport,
        ...target,
      };

      // In a full implementation, this would use mapbox-gl's flyTo
      // For the scaffold, we just set the viewport directly
      setViewport(newViewport);
    },
    [viewport, setViewport]
  );

  // Fit viewport to bounds
  const fitBounds = useCallback(
    (bounds: BoundingBox, padding: number = 20) => {
      // In a full implementation, this would calculate proper zoom
      // based on actual map container size
      const newViewport = fitBoundsToViewport(bounds, 800, 600, padding);
      setViewport(newViewport);
    },
    [setViewport]
  );

  // Reset to initial viewport
  const reset = useCallback(() => {
    setViewport(initialRef.current);
  }, [setViewport]);

  // Update initial ref if it changes
  useEffect(() => {
    initialRef.current = initial;
  }, [initial]);

  return {
    viewport,
    setViewport,
    flyTo,
    fitBounds,
    reset,
  };
}

// ============================================================================
// Exports
// ============================================================================

export default useViewport;
