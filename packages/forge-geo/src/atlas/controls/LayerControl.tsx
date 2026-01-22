/**
 * Layer Control Component
 *
 * Map control for toggling layer visibility.
 */

import React, { useState } from 'react';
import type { LayerControlProps, ControlPosition } from '../types';

// ============================================================================
// Types
// ============================================================================

export interface LayerControlPropsExtended extends LayerControlProps {
  /** Control title */
  title?: string;
  /** Start collapsed */
  defaultCollapsed?: boolean;
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
// Component: LayerControl
// ============================================================================

/**
 * Layer Control
 *
 * Provides a panel for toggling layer visibility on the map.
 *
 * @example
 * ```tsx
 * const [layers, setLayers] = useState([
 *   { id: 'points', label: 'Points', visible: true },
 *   { id: 'heatmap', label: 'Heatmap', visible: false },
 * ]);
 *
 * <ForgeMap initialViewport={viewport}>
 *   <LayerControl
 *     position="top-left"
 *     layers={layers}
 *     onLayerToggle={(id, visible) => {
 *       setLayers(layers.map(l => l.id === id ? { ...l, visible } : l));
 *     }}
 *   />
 * </ForgeMap>
 * ```
 */
export function LayerControl({
  position = 'top-left',
  layers,
  onLayerToggle,
  title = 'Layers',
  defaultCollapsed = false,
  className = '',
}: LayerControlPropsExtended): React.ReactElement {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const positionStyle = POSITION_STYLES[position];

  return (
    <div
      className={`forge-atlas-layer-control ${className}`}
      style={{
        position: 'absolute',
        ...positionStyle,
        backgroundColor: 'white',
        borderRadius: 4,
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        minWidth: 150,
        zIndex: 1,
      }}
    >
      {/* Header */}
      <button
        type="button"
        onClick={() => setCollapsed(!collapsed)}
        style={{
          width: '100%',
          padding: '8px 12px',
          border: 'none',
          backgroundColor: 'transparent',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontWeight: 600,
          fontSize: 14,
          borderBottom: collapsed ? 'none' : '1px solid #eee',
        }}
        aria-expanded={!collapsed}
        aria-controls="layer-control-list"
      >
        <span>{title}</span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          style={{
            transform: collapsed ? 'rotate(-90deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s ease',
          }}
        >
          <polyline points="6,9 12,15 18,9" />
        </svg>
      </button>

      {/* Layer List */}
      {!collapsed && (
        <div
          id="layer-control-list"
          style={{
            padding: '4px 0',
          }}
        >
          {layers.map((layer) => (
            <label
              key={layer.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '6px 12px',
                cursor: 'pointer',
                fontSize: 13,
              }}
            >
              <input
                type="checkbox"
                checked={layer.visible}
                onChange={(e) => onLayerToggle?.(layer.id, e.target.checked)}
                style={{
                  marginRight: 8,
                }}
              />
              {layer.label}
            </label>
          ))}
          {layers.length === 0 && (
            <div
              style={{
                padding: '8px 12px',
                color: '#999',
                fontSize: 13,
              }}
            >
              No layers available
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Exports
// ============================================================================

export default LayerControl;
