/**
 * Forge Atlas Map Component
 *
 * Main map component wrapping Mapbox GL and deck.gl for visualization.
 */

import React, { useRef, useEffect, useCallback, useState } from 'react';
import type {
  MapProps,
  Viewport,
  PickInfo,
  BasemapStyle,
  LayerConfig,
} from '../types';

// ============================================================================
// Constants
// ============================================================================

const BASEMAP_STYLES: Record<BasemapStyle, string> = {
  streets: 'mapbox://styles/mapbox/streets-v12',
  satellite: 'mapbox://styles/mapbox/satellite-streets-v12',
  dark: 'mapbox://styles/mapbox/dark-v11',
  light: 'mapbox://styles/mapbox/light-v11',
  outdoors: 'mapbox://styles/mapbox/outdoors-v12',
};

const DEFAULT_VIEWPORT: Viewport = {
  longitude: -122.4,
  latitude: 37.8,
  zoom: 10,
  pitch: 0,
  bearing: 0,
};

// ============================================================================
// Map Component
// ============================================================================

/**
 * Forge Atlas Map
 *
 * A React component for rendering interactive maps with Mapbox GL and deck.gl layers.
 *
 * @example
 * ```tsx
 * <ForgeMap
 *   initialViewport={{ longitude: -122.4, latitude: 37.8, zoom: 10 }}
 *   layers={[
 *     {
 *       type: 'point',
 *       id: 'locations',
 *       data: features,
 *       getFillColor: [255, 140, 0, 200],
 *     }
 *   ]}
 *   onFeatureClick={(info) => console.log('Clicked:', info.object)}
 * />
 * ```
 */
export function ForgeMap({
  initialViewport = DEFAULT_VIEWPORT,
  layers = [],
  onViewportChange,
  onFeatureClick,
  onFeatureHover,
  basemap = 'streets',
  interactive = true,
  mapboxAccessToken,
  className = '',
  children,
}: MapProps): React.ReactElement {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);
  const deckOverlayRef = useRef<unknown>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Get basemap style URL
  const basemapStyle = BASEMAP_STYLES[basemap] || BASEMAP_STYLES.streets;

  // Initialize map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const initializeMap = async () => {
      // Dynamic imports for map libraries (tree-shaking friendly)
      const mapboxgl = await import('mapbox-gl');
      const { MapboxOverlay } = await import('@deck.gl/mapbox');

      // Set access token
      if (mapboxAccessToken) {
        mapboxgl.default.accessToken = mapboxAccessToken;
      }

      // Create map instance
      const map = new mapboxgl.default.Map({
        container: containerRef.current!,
        style: basemapStyle,
        center: [initialViewport.longitude, initialViewport.latitude],
        zoom: initialViewport.zoom,
        pitch: initialViewport.pitch || 0,
        bearing: initialViewport.bearing || 0,
        interactive,
      });

      // Create deck.gl overlay
      const overlay = new MapboxOverlay({
        interleaved: true,
        onClick: (info: PickInfo) => {
          if (info.object && onFeatureClick) {
            onFeatureClick(info);
          }
        },
        onHover: (info: PickInfo) => {
          if (onFeatureHover) {
            onFeatureHover(info.object ? info : null);
          }
        },
      });

      map.addControl(overlay as unknown as mapboxgl.IControl);

      // Handle viewport changes
      map.on('move', () => {
        if (onViewportChange) {
          const center = map.getCenter();
          onViewportChange({
            longitude: center.lng,
            latitude: center.lat,
            zoom: map.getZoom(),
            pitch: map.getPitch(),
            bearing: map.getBearing(),
          });
        }
      });

      map.on('load', () => {
        setIsLoaded(true);
      });

      mapRef.current = map;
      deckOverlayRef.current = overlay;
    };

    initializeMap().catch(console.error);

    return () => {
      if (mapRef.current) {
        (mapRef.current as { remove: () => void }).remove();
        mapRef.current = null;
        deckOverlayRef.current = null;
      }
    };
  }, [basemapStyle, initialViewport, interactive, mapboxAccessToken, onFeatureClick, onFeatureHover, onViewportChange]);

  // Update layers when they change
  useEffect(() => {
    if (!deckOverlayRef.current || !isLoaded) return;

    const updateLayers = async () => {
      const deckLayers = await Promise.all(
        layers.map((config) => createDeckLayer(config))
      );
      (deckOverlayRef.current as { setProps: (props: { layers: unknown[] }) => void }).setProps({ layers: deckLayers });
    };

    updateLayers().catch(console.error);
  }, [layers, isLoaded]);

  return (
    <div
      ref={containerRef}
      className={`forge-atlas-map ${className}`}
      style={{ width: '100%', height: '100%', position: 'relative' }}
    >
      {children}
    </div>
  );
}

// ============================================================================
// Layer Creation
// ============================================================================

/**
 * Create a deck.gl layer from configuration.
 *
 * This is a factory function that maps our LayerConfig types to deck.gl layer instances.
 */
async function createDeckLayer(config: LayerConfig): Promise<unknown> {
  const { ScatterplotLayer, PolygonLayer, GeoJsonLayer } = await import('@deck.gl/layers');
  const { HeatmapLayer } = await import('@deck.gl/aggregation-layers');

  // Normalize data to array of features
  const features = Array.isArray(config.data)
    ? config.data
    : (config.data as { features: unknown[] }).features || [];

  switch (config.type) {
    case 'point':
      return new ScatterplotLayer({
        id: config.id,
        data: features,
        visible: config.visible ?? true,
        opacity: config.opacity ?? 1,
        pickable: config.pickable ?? true,
        getPosition: (d: unknown) => {
          const feature = d as { geometry: { coordinates: [number, number] } };
          return feature.geometry.coordinates;
        },
        getRadius: config.getRadius ?? 100,
        getFillColor: config.getFillColor ?? [255, 140, 0, 200],
        getLineColor: config.getLineColor ?? [0, 0, 0, 255],
        radiusUnits: config.radiusUnits ?? 'meters',
        radiusMinPixels: config.radiusMinPixels ?? 2,
        radiusMaxPixels: config.radiusMaxPixels ?? 100,
        filled: config.filled ?? true,
        stroked: config.stroked ?? true,
        lineWidthMinPixels: config.lineWidthMinPixels ?? 1,
      });

    case 'polygon':
      return new PolygonLayer({
        id: config.id,
        data: features,
        visible: config.visible ?? true,
        opacity: config.opacity ?? 1,
        pickable: config.pickable ?? true,
        getPolygon: (d: unknown) => {
          const feature = d as { geometry: { coordinates: number[][][] } };
          return feature.geometry.coordinates;
        },
        getFillColor: config.getFillColor ?? [100, 150, 200, 128],
        getLineColor: config.getLineColor ?? [0, 0, 0, 255],
        filled: config.filled ?? true,
        stroked: config.stroked ?? true,
        lineWidthMinPixels: config.lineWidthMinPixels ?? 1,
        extruded: config.extruded ?? false,
        getElevation: config.getElevation ?? 0,
      });

    case 'cluster':
      // Cluster layer requires supercluster integration
      // For scaffold, use GeoJsonLayer as placeholder
      return new GeoJsonLayer({
        id: config.id,
        data: { type: 'FeatureCollection', features },
        visible: config.visible ?? true,
        opacity: config.opacity ?? 1,
        pickable: config.pickable ?? true,
        pointRadiusMinPixels: 5,
        pointRadiusMaxPixels: 50,
        getFillColor: [255, 140, 0, 200],
      });

    case 'heatmap':
      return new HeatmapLayer({
        id: config.id,
        data: features,
        visible: config.visible ?? true,
        opacity: config.opacity ?? 1,
        pickable: false, // Heatmaps don't support picking
        getPosition: (d: unknown) => {
          const feature = d as { geometry: { coordinates: [number, number] } };
          return feature.geometry.coordinates;
        },
        getWeight: config.getWeight ?? 1,
        radiusPixels: config.radiusPixels ?? 30,
        intensity: config.intensity ?? 1,
        threshold: config.threshold ?? 0.05,
        colorRange: config.colorRange ?? [
          [255, 255, 178, 255],
          [254, 217, 118, 255],
          [254, 178, 76, 255],
          [253, 141, 60, 255],
          [252, 78, 42, 255],
          [227, 26, 28, 255],
          [177, 0, 38, 255],
        ],
        aggregation: config.aggregation ?? 'SUM',
      });

    default:
      throw new Error(`Unknown layer type: ${(config as { type: string }).type}`);
  }
}

// ============================================================================
// Exports
// ============================================================================

export default ForgeMap;
