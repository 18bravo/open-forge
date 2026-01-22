/**
 * Heatmap Layer Component
 *
 * Renders density heatmaps using deck.gl HeatmapLayer.
 */

import React from 'react';
import type { HeatmapLayerConfig, GeoJSONFeature, RGBAColor } from '../types';

// ============================================================================
// Types
// ============================================================================

export interface HeatmapLayerProps {
  /** Layer ID */
  id: string;
  /** Point feature data */
  data: GeoJSONFeature[];
  /** Property name for weight value */
  weightProperty?: string;
  /** Fixed weight value (if not using property) */
  weight?: number;
  /** Radius of influence in pixels */
  radiusPixels?: number;
  /** Intensity multiplier */
  intensity?: number;
  /** Threshold for visibility */
  threshold?: number;
  /** Color gradient */
  colorRange?: RGBAColor[];
  /** Aggregation method */
  aggregation?: 'SUM' | 'MEAN';
  /** Layer visibility */
  visible?: boolean;
  /** Layer opacity */
  opacity?: number;
}

// ============================================================================
// Default Values
// ============================================================================

/**
 * Default heatmap color gradient (yellow to red)
 */
export const DEFAULT_HEATMAP_COLORS: RGBAColor[] = [
  [255, 255, 178, 255],  // Light yellow
  [254, 217, 118, 255],  // Yellow
  [254, 178, 76, 255],   // Orange-yellow
  [253, 141, 60, 255],   // Orange
  [252, 78, 42, 255],    // Red-orange
  [227, 26, 28, 255],    // Red
  [177, 0, 38, 255],     // Dark red
];

/**
 * Cool color gradient (blue to cyan)
 */
export const COOL_HEATMAP_COLORS: RGBAColor[] = [
  [237, 248, 251, 255],
  [178, 226, 226, 255],
  [102, 194, 164, 255],
  [44, 162, 95, 255],
  [0, 109, 44, 255],
];

/**
 * Viridis-inspired color gradient
 */
export const VIRIDIS_HEATMAP_COLORS: RGBAColor[] = [
  [68, 1, 84, 255],
  [72, 40, 120, 255],
  [62, 74, 137, 255],
  [49, 104, 142, 255],
  [38, 130, 142, 255],
  [53, 183, 121, 255],
  [253, 231, 37, 255],
];

// ============================================================================
// Hook: useHeatmapLayer
// ============================================================================

/**
 * Hook to create a heatmap layer configuration
 *
 * @example
 * ```tsx
 * const { config } = useHeatmapLayer({
 *   id: 'density',
 *   data: pointData,
 *   weightProperty: 'magnitude',
 *   radiusPixels: 30,
 * });
 *
 * return <ForgeMap layers={[config]} />;
 * ```
 */
export function useHeatmapLayer(props: HeatmapLayerProps): { config: HeatmapLayerConfig } {
  const {
    id,
    data,
    weightProperty,
    weight = 1,
    radiusPixels = 30,
    intensity = 1,
    threshold = 0.05,
    colorRange = DEFAULT_HEATMAP_COLORS,
    aggregation = 'SUM',
    visible = true,
    opacity = 1,
  } = props;

  // Create weight accessor
  const getWeight = weightProperty
    ? (feature: GeoJSONFeature) => {
        const value = feature.properties?.[weightProperty];
        return typeof value === 'number' ? value : weight;
      }
    : weight;

  const config: HeatmapLayerConfig = {
    type: 'heatmap',
    id,
    data,
    visible,
    opacity,
    pickable: false, // Heatmaps don't support picking
    getWeight,
    radiusPixels,
    intensity,
    threshold,
    colorRange,
    aggregation,
  };

  return { config };
}

// ============================================================================
// Component: HeatmapLayer
// ============================================================================

/**
 * Heatmap Layer
 *
 * A declarative component for rendering density heatmaps.
 * Must be used as a child of ForgeMap.
 *
 * @example
 * ```tsx
 * <ForgeMap initialViewport={viewport}>
 *   <HeatmapLayer
 *     id="density"
 *     data={pointData}
 *     weightProperty="magnitude"
 *     radiusPixels={30}
 *     colorRange={VIRIDIS_HEATMAP_COLORS}
 *   />
 * </ForgeMap>
 * ```
 */
export function HeatmapLayer(_props: HeatmapLayerProps): React.ReactElement | null {
  // Declarative configuration wrapper - parent ForgeMap handles rendering
  return null;
}

// Mark as layer component for parent detection
HeatmapLayer.isForgeLayer = true;
HeatmapLayer.layerType = 'heatmap';

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Create a custom color gradient
 */
export function createColorGradient(
  startColor: RGBAColor,
  endColor: RGBAColor,
  steps: number = 7
): RGBAColor[] {
  const colors: RGBAColor[] = [];

  for (let i = 0; i < steps; i++) {
    const t = i / (steps - 1);
    colors.push([
      Math.round(startColor[0] + (endColor[0] - startColor[0]) * t),
      Math.round(startColor[1] + (endColor[1] - startColor[1]) * t),
      Math.round(startColor[2] + (endColor[2] - startColor[2]) * t),
      Math.round(startColor[3] + (endColor[3] - startColor[3]) * t),
    ]);
  }

  return colors;
}

// ============================================================================
// Exports
// ============================================================================

export default HeatmapLayer;
