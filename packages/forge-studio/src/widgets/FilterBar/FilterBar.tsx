/**
 * FilterBar Widget
 *
 * A horizontal or vertical bar of filter inputs that can be
 * linked to other widgets to filter their data.
 */

import React from 'react';
import type {
  FilterBarConfig,
  WidgetDefinition,
} from '../../types';
import {
  defineWidget,
  type WidgetComponentProps,
} from '../registry';

// ============================================================================
// Widget Definition
// ============================================================================

export const filterBarDefinition = defineWidget<FilterBarConfig>({
  type: 'filter-bar',
  displayName: 'Filter Bar',
  description: 'Add filters to control data displayed in other widgets',
  icon: 'filter',
  category: 'input',

  defaultConfig: {
    filters: [],
    direction: 'horizontal',
    showClearAll: true,
    autoApply: true,
  },

  defaultLayout: {
    width: 8,
    height: 1,
    minWidth: 4,
    minHeight: 1,
  },

  bindingSlots: [
    {
      name: 'options',
      label: 'Filter Options',
      description: 'Dynamic options for select filters',
      required: false,
      acceptedTypes: ['object-set', 'static'],
    },
  ],

  eventHandlers: [
    {
      name: 'onFilterChange',
      label: 'Filter Change',
      description: 'Triggered when filter values change',
      payloadType: 'Record<string, unknown>',
    },
    {
      name: 'onClearAll',
      label: 'Clear All',
      description: 'Triggered when all filters are cleared',
    },
    {
      name: 'onApply',
      label: 'Apply',
      description: 'Triggered when filters are applied (manual mode)',
      payloadType: 'Record<string, unknown>',
    },
  ],

  configSchema: {
    properties: {
      filters: {
        type: 'array',
        label: 'Filters',
        items: {
          type: 'object',
          label: 'Filter',
          properties: {
            id: { type: 'string', label: 'ID' },
            property: { type: 'string', label: 'Property' },
            label: { type: 'string', label: 'Label' },
            inputType: {
              type: 'enum',
              label: 'Input Type',
              enum: ['text', 'select', 'multiselect', 'date-range', 'number-range'],
              default: 'text',
            },
            placeholder: { type: 'string', label: 'Placeholder' },
          },
        },
      },
      direction: {
        type: 'enum',
        label: 'Direction',
        enum: ['horizontal', 'vertical'],
        enumLabels: ['Horizontal', 'Vertical'],
        default: 'horizontal',
      },
      showClearAll: {
        type: 'boolean',
        label: 'Show Clear All',
        default: true,
      },
      autoApply: {
        type: 'boolean',
        label: 'Auto Apply',
        description: 'Apply filters automatically as values change',
        default: true,
      },
    },
    required: ['filters'],
  },
});

// ============================================================================
// Component Props
// ============================================================================

export type FilterBarProps = WidgetComponentProps<FilterBarConfig>;

// ============================================================================
// Component
// ============================================================================

/**
 * FilterBar widget component
 */
export const FilterBar: React.FC<FilterBarProps> = ({
  widget: _widget,
  data: _data,
  onStateChange: _onStateChange,
  onAction: _onAction,
  isLoading: _isLoading = false,
  error: _error,
  isPreview: _isPreview = false,
}) => {
  // TODO: Implement filter bar rendering
  // TODO: Implement filter input types
  // TODO: Implement filter state management
  // TODO: Implement auto-apply logic
  // TODO: Implement clear all functionality
  // TODO: Implement filter linking to other widgets

  return (
    <div data-testid="widget-filter-bar">
      {/* TODO: Implement filter bar */}
    </div>
  );
};

FilterBar.displayName = 'FilterBar';

export default FilterBar;
