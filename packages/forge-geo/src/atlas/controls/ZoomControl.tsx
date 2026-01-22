/**
 * Zoom Control Component
 *
 * Map control for zooming and compass functionality.
 */

import React from 'react';
import type { ZoomControlProps, ControlPosition } from '../types';

// ============================================================================
// Types
// ============================================================================

export interface ZoomControlPropsExtended extends ZoomControlProps {
  /** Callback when zoom in is clicked */
  onZoomIn?: () => void;
  /** Callback when zoom out is clicked */
  onZoomOut?: () => void;
  /** Callback when compass is clicked */
  onResetBearing?: () => void;
  /** Current bearing (for compass rotation) */
  bearing?: number;
  /** Additional CSS class */
  className?: string;
}

// ============================================================================
// Position Styles
// ============================================================================

const POSITION_STYLES: Record<ControlPosition, React.CSSProperties> = {
  'top-left': { top: 10, left: 10 },
  'top-right': { top: 10, right: 10 },
  'bottom-left': { bottom: 30, left: 10 },
  'bottom-right': { bottom: 30, right: 10 },
};

// ============================================================================
// Component: ZoomControl
// ============================================================================

/**
 * Zoom Control
 *
 * Provides zoom in/out buttons and an optional compass for bearing reset.
 *
 * @example
 * ```tsx
 * <ForgeMap initialViewport={viewport} onViewportChange={setViewport}>
 *   <ZoomControl
 *     position="top-right"
 *     showCompass
 *     onZoomIn={() => setViewport({ ...viewport, zoom: viewport.zoom + 1 })}
 *     onZoomOut={() => setViewport({ ...viewport, zoom: viewport.zoom - 1 })}
 *   />
 * </ForgeMap>
 * ```
 */
export function ZoomControl({
  position = 'top-right',
  showCompass = true,
  showZoom = true,
  onZoomIn,
  onZoomOut,
  onResetBearing,
  bearing = 0,
  className = '',
}: ZoomControlPropsExtended): React.ReactElement {
  const positionStyle = POSITION_STYLES[position];

  return (
    <div
      className={`forge-atlas-zoom-control ${className}`}
      style={{
        position: 'absolute',
        ...positionStyle,
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
        zIndex: 1,
      }}
    >
      {showCompass && (
        <button
          type="button"
          onClick={onResetBearing}
          title="Reset bearing"
          style={{
            width: 32,
            height: 32,
            border: '1px solid #ccc',
            borderRadius: 4,
            backgroundColor: 'white',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `rotate(${-bearing}deg)`,
            transition: 'transform 0.2s ease',
          }}
          aria-label="Reset bearing"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="12,2 19,21 12,17 5,21" />
          </svg>
        </button>
      )}

      {showZoom && (
        <>
          <button
            type="button"
            onClick={onZoomIn}
            title="Zoom in"
            style={{
              width: 32,
              height: 32,
              border: '1px solid #ccc',
              borderRadius: 4,
              backgroundColor: 'white',
              cursor: 'pointer',
              fontSize: 18,
              fontWeight: 'bold',
            }}
            aria-label="Zoom in"
          >
            +
          </button>
          <button
            type="button"
            onClick={onZoomOut}
            title="Zoom out"
            style={{
              width: 32,
              height: 32,
              border: '1px solid #ccc',
              borderRadius: 4,
              backgroundColor: 'white',
              cursor: 'pointer',
              fontSize: 18,
              fontWeight: 'bold',
            }}
            aria-label="Zoom out"
          >
            -
          </button>
        </>
      )}
    </div>
  );
}

// ============================================================================
// Exports
// ============================================================================

export default ZoomControl;
