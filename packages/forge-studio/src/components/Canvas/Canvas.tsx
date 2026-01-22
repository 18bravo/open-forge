/**
 * Canvas Component
 *
 * Drag-and-drop canvas for placing and arranging widgets.
 * Uses @dnd-kit for drag-and-drop functionality.
 */

import React from 'react';
import type {
  WidgetInstance,
  PageSection,
  GridConfig,
  WidgetLayout,
} from '../../types';

// ============================================================================
// Props Interfaces
// ============================================================================

export interface CanvasProps {
  /** Sections to render */
  sections: PageSection[];

  /** Currently selected widget ID */
  selectedWidgetId?: string | null;

  /** Callback when a widget is selected */
  onWidgetSelect?: (widgetId: string | null) => void;

  /** Callback when a widget is dropped */
  onWidgetDrop?: (widget: WidgetInstance, position: WidgetLayout) => void;

  /** Callback when a widget is moved */
  onWidgetMove?: (widgetId: string, newLayout: WidgetLayout) => void;

  /** Callback when a widget is resized */
  onWidgetResize?: (widgetId: string, newLayout: WidgetLayout) => void;

  /** Callback when widget order changes */
  onWidgetReorder?: (sectionId: string, widgetIds: string[]) => void;

  /** Grid configuration */
  gridConfig?: GridConfig;

  /** Enable snap to grid */
  snapToGrid?: boolean;

  /** Show grid lines */
  showGrid?: boolean;

  /** Zoom level (1 = 100%) */
  zoom?: number;

  /** Read-only mode */
  readOnly?: boolean;

  /** Preview mode (render actual widgets) */
  previewMode?: boolean;

  /** Custom class name */
  className?: string;
}

export interface CanvasContextValue {
  /** Current grid configuration */
  gridConfig: GridConfig;

  /** Current zoom level */
  zoom: number;

  /** Whether in preview mode */
  isPreviewMode: boolean;

  /** Whether in read-only mode */
  isReadOnly: boolean;

  /** Get widget by ID */
  getWidget: (widgetId: string) => WidgetInstance | undefined;

  /** Check if a position is available */
  isPositionAvailable: (layout: WidgetLayout, excludeWidgetId?: string) => boolean;
}

// ============================================================================
// Context
// ============================================================================

export const CanvasContext = React.createContext<CanvasContextValue | null>(null);

/**
 * Hook to access canvas context
 */
export function useCanvas(): CanvasContextValue {
  const context = React.useContext(CanvasContext);
  if (!context) {
    throw new Error('useCanvas must be used within a Canvas');
  }
  return context;
}

// ============================================================================
// Sub-components
// ============================================================================

export interface CanvasSectionProps {
  /** Section to render */
  section: PageSection;

  /** Currently selected widget ID */
  selectedWidgetId?: string | null;

  /** Callback when a widget is selected */
  onWidgetSelect?: (widgetId: string | null) => void;
}

/**
 * Renders a section within the canvas
 */
export const CanvasSection: React.FC<CanvasSectionProps> = ({
  section: _section,
  selectedWidgetId: _selectedWidgetId,
  onWidgetSelect: _onWidgetSelect,
}) => {
  // TODO: Implement section rendering
  // TODO: Implement collapsible behavior
  // TODO: Implement section header

  return (
    <div data-testid="canvas-section">
      {/* TODO: Implement section content */}
    </div>
  );
};

export interface CanvasWidgetProps {
  /** Widget instance to render */
  widget: WidgetInstance;

  /** Whether widget is selected */
  isSelected?: boolean;

  /** Callback when widget is selected */
  onSelect?: () => void;

  /** Preview mode */
  previewMode?: boolean;
}

/**
 * Renders a widget within the canvas (design-time wrapper)
 */
export const CanvasWidget: React.FC<CanvasWidgetProps> = ({
  widget: _widget,
  isSelected: _isSelected = false,
  onSelect: _onSelect,
  previewMode: _previewMode = false,
}) => {
  // TODO: Implement widget wrapper with selection
  // TODO: Implement resize handles
  // TODO: Implement drag handle
  // TODO: Implement widget toolbar (delete, duplicate, etc.)

  return (
    <div data-testid="canvas-widget">
      {/* TODO: Implement widget wrapper content */}
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

/**
 * Canvas component for arranging widgets
 *
 * @example
 * ```tsx
 * <Canvas
 *   sections={page.sections}
 *   selectedWidgetId={selectedId}
 *   onWidgetSelect={setSelectedId}
 *   onWidgetDrop={handleDrop}
 * />
 * ```
 */
export const Canvas: React.FC<CanvasProps> = ({
  sections: _sections,
  selectedWidgetId: _selectedWidgetId,
  onWidgetSelect: _onWidgetSelect,
  onWidgetDrop: _onWidgetDrop,
  onWidgetMove: _onWidgetMove,
  onWidgetResize: _onWidgetResize,
  onWidgetReorder: _onWidgetReorder,
  gridConfig: _gridConfig,
  snapToGrid: _snapToGrid = true,
  showGrid: _showGrid = true,
  zoom: _zoom = 1,
  readOnly: _readOnly = false,
  previewMode: _previewMode = false,
  className: _className,
}) => {
  // TODO: Implement DndContext from @dnd-kit/core
  // TODO: Implement grid overlay
  // TODO: Implement zoom controls
  // TODO: Implement pan functionality
  // TODO: Implement selection box (for multi-select)

  return (
    <div data-testid="forge-studio-canvas">
      {/* TODO: Implement canvas layout */}
      {/* - Grid overlay */}
      {/* - Drop zones */}
      {/* - Sections */}
      {/* - Widgets */}
    </div>
  );
};

Canvas.displayName = 'Canvas';

export default Canvas;
