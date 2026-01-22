/**
 * WidgetPanel Component
 *
 * Sidebar panel displaying available widgets that can be dragged onto the canvas.
 * Organized by category with search functionality.
 */

import React from 'react';
import type {
  WidgetType,
  WidgetCategory,
  WidgetDefinition,
} from '../../types';

// ============================================================================
// Props Interfaces
// ============================================================================

export interface WidgetPanelProps {
  /** Widget definitions to display */
  widgets?: WidgetDefinition[];

  /** Categories to show (undefined = all) */
  categories?: WidgetCategory[];

  /** Search query */
  searchQuery?: string;

  /** Callback when search query changes */
  onSearchChange?: (query: string) => void;

  /** Callback when a widget starts being dragged */
  onWidgetDragStart?: (widgetType: WidgetType) => void;

  /** Callback when a widget is clicked (for quick-add) */
  onWidgetClick?: (widgetType: WidgetType) => void;

  /** Custom class name */
  className?: string;

  /** Collapsed state */
  collapsed?: boolean;

  /** Callback when collapse state changes */
  onCollapsedChange?: (collapsed: boolean) => void;
}

export interface WidgetPanelItemProps {
  /** Widget definition */
  widget: WidgetDefinition;

  /** Callback when drag starts */
  onDragStart?: () => void;

  /** Callback when clicked */
  onClick?: () => void;

  /** Whether the item is being dragged */
  isDragging?: boolean;
}

export interface WidgetPanelCategoryProps {
  /** Category name */
  category: WidgetCategory;

  /** Category display label */
  label: string;

  /** Widgets in this category */
  widgets: WidgetDefinition[];

  /** Collapsed state */
  collapsed?: boolean;

  /** Callback when collapse state changes */
  onCollapsedChange?: (collapsed: boolean) => void;

  /** Callback when widget drag starts */
  onWidgetDragStart?: (widgetType: WidgetType) => void;

  /** Callback when widget is clicked */
  onWidgetClick?: (widgetType: WidgetType) => void;
}

// ============================================================================
// Sub-components
// ============================================================================

/**
 * Individual widget item in the panel
 */
export const WidgetPanelItem: React.FC<WidgetPanelItemProps> = ({
  widget: _widget,
  onDragStart: _onDragStart,
  onClick: _onClick,
  isDragging: _isDragging = false,
}) => {
  // TODO: Implement draggable behavior with @dnd-kit
  // TODO: Implement widget icon and label
  // TODO: Implement tooltip with description

  return (
    <div data-testid="widget-panel-item">
      {/* TODO: Implement widget item content */}
    </div>
  );
};

/**
 * Category section in the panel
 */
export const WidgetPanelCategory: React.FC<WidgetPanelCategoryProps> = ({
  category: _category,
  label: _label,
  widgets: _widgets,
  collapsed: _collapsed = false,
  onCollapsedChange: _onCollapsedChange,
  onWidgetDragStart: _onWidgetDragStart,
  onWidgetClick: _onWidgetClick,
}) => {
  // TODO: Implement collapsible category
  // TODO: Implement category header with icon

  return (
    <div data-testid="widget-panel-category">
      {/* TODO: Implement category content */}
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

/**
 * Widget panel for selecting and dragging widgets
 *
 * @example
 * ```tsx
 * <WidgetPanel
 *   widgets={registeredWidgets}
 *   onWidgetDragStart={handleDragStart}
 *   searchQuery={search}
 *   onSearchChange={setSearch}
 * />
 * ```
 */
export const WidgetPanel: React.FC<WidgetPanelProps> = ({
  widgets: _widgets,
  categories: _categories,
  searchQuery: _searchQuery,
  onSearchChange: _onSearchChange,
  onWidgetDragStart: _onWidgetDragStart,
  onWidgetClick: _onWidgetClick,
  className: _className,
  collapsed: _collapsed = false,
  onCollapsedChange: _onCollapsedChange,
}) => {
  // TODO: Implement search filtering
  // TODO: Implement category grouping
  // TODO: Implement drag source with @dnd-kit

  return (
    <div data-testid="forge-studio-widget-panel">
      {/* TODO: Implement panel layout */}
      {/* - Search input */}
      {/* - Category sections */}
      {/* - Widget items */}
    </div>
  );
};

WidgetPanel.displayName = 'WidgetPanel';

export default WidgetPanel;
