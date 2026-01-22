/**
 * Forge Atlas
 *
 * Map visualization module for Open Forge with Mapbox/deck.gl integration.
 *
 * @example
 * ```tsx
 * import { ForgeMap, PointLayer, useMapData, useViewport } from '@open-forge/forge-geo/atlas';
 *
 * function MapView() {
 *   const { viewport, setViewport } = useViewport({
 *     initial: { longitude: -122.4, latitude: 37.8, zoom: 10 }
 *   });
 *
 *   const { features, isLoading } = useMapData({
 *     datasetId: 'locations',
 *     viewport,
 *   });
 *
 *   return (
 *     <ForgeMap
 *       initialViewport={viewport}
 *       onViewportChange={setViewport}
 *       layers={[
 *         { type: 'point', id: 'locations', data: features }
 *       ]}
 *     >
 *       <ZoomControl position="top-right" />
 *       <LayerControl position="top-left" layers={[...]} />
 *     </ForgeMap>
 *   );
 * }
 * ```
 *
 * @packageDocumentation
 */

// ============================================================================
// Types
// ============================================================================

export * from './types';

// ============================================================================
// Components
// ============================================================================

export * from './components';

// ============================================================================
// Layers
// ============================================================================

export * from './layers';

// ============================================================================
// Controls
// ============================================================================

export * from './controls';

// ============================================================================
// Hooks
// ============================================================================

export * from './hooks';

// ============================================================================
// Version
// ============================================================================

export const ATLAS_VERSION = '0.1.0';
