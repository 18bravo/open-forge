/**
 * Point Layer Component
 *
 * Renders point features on the map using deck.gl ScatterplotLayer.
 */

import React from 'react';
import type { PointLayerConfig, GeoJSONFeature, RGBAColor, Coordinate } from '../types';

// ============================================================================
// Types
// ============================================================================

export interface PointLayerProps {
  /** Layer ID */
  id: string;
  /** Point feature data */
  data: GeoJSONFeature[];
  /** Point fill color */
  color?: RGBAColor | ((feature: GeoJSONFeature) => RGBAColor);
  /** Point radius in pixels or meters */
  radius?: number | ((feature: GeoJSONFeature) => number);
  /** Use meters instead of pixels */
  radiusUnits?: 'pixels' | 'meters';
  /** Minimum radius in pixels */
  radiusMinPixels?: number;
  /** Maximum radius in pixels */
  radiusMaxPixels?: number;
  /** Stroke color */
  strokeColor?: RGBAColor;
  /** Stroke width */
  strokeWidth?: number;
  /** Enable picking */
  pickable?: boolean;
  /** Layer visibility */
  visible?: boolean;
  /** Layer opacity */
  opacity?: number;
  /** Click handler */
  onClick?: (feature: GeoJSONFeature, coordinate: Coordinate) => void;
  /** Hover handler */
  onHover?: (feature: GeoJSONFeature | null, coordinate?: Coordinate) => void;
}

// ============================================================================
// Default Accessors
// ============================================================================

const DEFAULT_COLOR: RGBAColor = [255, 140, 0, 200];
const DEFAULT_STROKE_COLOR: RGBAColor = [0, 0, 0, 255];
const DEFAULT_RADIUS = 100;

/**
 * Default position accessor for GeoJSON Point features
 */
export function getPositionFromFeature(feature: GeoJSONFeature): Coordinate {
  const coords = feature.geometry.coordinates as Coordinate;
  return coords;
}

// ============================================================================
// Hook: usePointLayer
// ============================================================================

/**
 * Hook to create a point layer configuration
 *
 * @example
 * ```tsx
 * const { config } = usePointLayer({
 *   id: 'locations',
 *   data: features,
 *   color: [255, 0, 0, 200],
 *   radius: 50,
 * });
 *
 * return <ForgeMap layers={[config]} />;
 * ```
 */
export function usePointLayer(props: PointLayerProps): { config: PointLayerConfig } {
  const {
    id,
    data,
    color = DEFAULT_COLOR,
    radius = DEFAULT_RADIUS,
    radiusUnits = 'meters',
    radiusMinPixels = 2,
    radiusMaxPixels = 100,
    strokeColor = DEFAULT_STROKE_COLOR,
    strokeWidth = 1,
    pickable = true,
    visible = true,
    opacity = 1,
  } = props;

  const config: PointLayerConfig = {
    type: 'point',
    id,
    data,
    visible,
    opacity,
    pickable,
    getFillColor: typeof color === 'function' ? color : color,
    getRadius: typeof radius === 'function' ? radius : radius,
    getLineColor: strokeColor,
    radiusUnits,
    radiusMinPixels,
    radiusMaxPixels,
    filled: true,
    stroked: true,
    lineWidthMinPixels: strokeWidth,
  };

  return { config };
}

// ============================================================================
// Component: PointLayer
// ============================================================================

/**
 * Point Layer
 *
 * A declarative component for rendering point features.
 * Must be used as a child of ForgeMap.
 *
 * Note: This is a configuration component that doesn't render DOM elements directly.
 * The actual rendering is handled by the parent ForgeMap component.
 *
 * @example
 * ```tsx
 * <ForgeMap initialViewport={viewport}>
 *   <PointLayer
 *     id="locations"
 *     data={features}
 *     color={[255, 0, 0, 200]}
 *     radius={50}
 *     onClick={(feature) => console.log('Clicked:', feature)}
 *   />
 * </ForgeMap>
 * ```
 */
export function PointLayer(_props: PointLayerProps): React.ReactElement | null {
  // This component is a declarative configuration wrapper.
  // The parent ForgeMap reads props from children and creates layers.
  // It doesn't render anything itself.
  return null;
}

// Mark as layer component for parent detection
PointLayer.isForgeLayer = true;
PointLayer.layerType = 'point';

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Create a color scale function for point values
 */
export function createColorScale(
  minValue: number,
  maxValue: number,
  colorStops: RGBAColor[]
): (value: number) => RGBAColor {
  return (value: number): RGBAColor => {
    const normalized = Math.max(0, Math.min(1, (value - minValue) / (maxValue - minValue)));
    const stopIndex = Math.floor(normalized * (colorStops.length - 1));
    const nextStopIndex = Math.min(stopIndex + 1, colorStops.length - 1);
    const t = (normalized * (colorStops.length - 1)) - stopIndex;

    const c1 = colorStops[stopIndex];
    const c2 = colorStops[nextStopIndex];

    return [
      Math.round(c1[0] + (c2[0] - c1[0]) * t),
      Math.round(c1[1] + (c2[1] - c1[1]) * t),
      Math.round(c1[2] + (c2[2] - c1[2]) * t),
      Math.round(c1[3] + (c2[3] - c1[3]) * t),
    ];
  };
}

/**
 * Create a radius scale function for point values
 */
export function createRadiusScale(
  minValue: number,
  maxValue: number,
  minRadius: number,
  maxRadius: number
): (value: number) => number {
  return (value: number): number => {
    const normalized = Math.max(0, Math.min(1, (value - minValue) / (maxValue - minValue)));
    return minRadius + (maxRadius - minRadius) * normalized;
  };
}

// ============================================================================
// Exports
// ============================================================================

export default PointLayer;
