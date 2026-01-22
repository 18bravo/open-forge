/**
 * Polygon Layer Component
 *
 * Renders polygon features on the map using deck.gl PolygonLayer.
 */

import React from 'react';
import type { PolygonLayerConfig, GeoJSONFeature, RGBAColor, Coordinate } from '../types';

// ============================================================================
// Types
// ============================================================================

export interface PolygonLayerProps {
  /** Layer ID */
  id: string;
  /** Polygon feature data */
  data: GeoJSONFeature[];
  /** Fill color */
  fillColor?: RGBAColor | ((feature: GeoJSONFeature) => RGBAColor);
  /** Stroke color */
  strokeColor?: RGBAColor | ((feature: GeoJSONFeature) => RGBAColor);
  /** Stroke width in pixels */
  strokeWidth?: number;
  /** Fill polygons */
  filled?: boolean;
  /** Stroke polygons */
  stroked?: boolean;
  /** Enable 3D extrusion */
  extruded?: boolean;
  /** Extrusion height */
  elevation?: number | ((feature: GeoJSONFeature) => number);
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
// Default Values
// ============================================================================

const DEFAULT_FILL_COLOR: RGBAColor = [100, 150, 200, 128];
const DEFAULT_STROKE_COLOR: RGBAColor = [0, 0, 0, 255];

// ============================================================================
// Hook: usePolygonLayer
// ============================================================================

/**
 * Hook to create a polygon layer configuration
 *
 * @example
 * ```tsx
 * const { config } = usePolygonLayer({
 *   id: 'regions',
 *   data: polygonFeatures,
 *   fillColor: [100, 150, 200, 128],
 * });
 *
 * return <ForgeMap layers={[config]} />;
 * ```
 */
export function usePolygonLayer(props: PolygonLayerProps): { config: PolygonLayerConfig } {
  const {
    id,
    data,
    fillColor = DEFAULT_FILL_COLOR,
    strokeColor = DEFAULT_STROKE_COLOR,
    strokeWidth = 1,
    filled = true,
    stroked = true,
    extruded = false,
    elevation = 0,
    pickable = true,
    visible = true,
    opacity = 1,
  } = props;

  const config: PolygonLayerConfig = {
    type: 'polygon',
    id,
    data,
    visible,
    opacity,
    pickable,
    getFillColor: fillColor,
    getLineColor: strokeColor,
    filled,
    stroked,
    lineWidthMinPixels: strokeWidth,
    extruded,
    getElevation: elevation,
  };

  return { config };
}

// ============================================================================
// Component: PolygonLayer
// ============================================================================

/**
 * Polygon Layer
 *
 * A declarative component for rendering polygon features.
 * Must be used as a child of ForgeMap.
 *
 * @example
 * ```tsx
 * <ForgeMap initialViewport={viewport}>
 *   <PolygonLayer
 *     id="regions"
 *     data={polygonFeatures}
 *     fillColor={[100, 150, 200, 128]}
 *     strokeColor={[0, 0, 0, 255]}
 *     onClick={(feature) => console.log('Clicked:', feature)}
 *   />
 * </ForgeMap>
 * ```
 */
export function PolygonLayer(_props: PolygonLayerProps): React.ReactElement | null {
  // Declarative configuration wrapper - parent ForgeMap handles rendering
  return null;
}

// Mark as layer component for parent detection
PolygonLayer.isForgeLayer = true;
PolygonLayer.layerType = 'polygon';

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Create a choropleth color function based on feature property
 */
export function createChoroplethColor(
  propertyName: string,
  breaks: number[],
  colors: RGBAColor[]
): (feature: GeoJSONFeature) => RGBAColor {
  return (feature: GeoJSONFeature): RGBAColor => {
    const value = feature.properties?.[propertyName] as number;
    if (value === undefined || value === null) {
      return [128, 128, 128, 128]; // Default gray for missing values
    }

    for (let i = 0; i < breaks.length; i++) {
      if (value <= breaks[i]) {
        return colors[i] || colors[colors.length - 1];
      }
    }

    return colors[colors.length - 1];
  };
}

// ============================================================================
// Exports
// ============================================================================

export default PolygonLayer;
