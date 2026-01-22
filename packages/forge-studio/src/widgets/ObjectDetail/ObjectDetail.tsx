/**
 * ObjectDetail Widget
 *
 * Displays detailed information about a single object with
 * configurable field layout and formatting.
 */

import React from 'react';
import type {
  ObjectDetailConfig,
  WidgetDefinition,
} from '../../types';
import {
  defineWidget,
  type WidgetComponentProps,
} from '../registry';

// ============================================================================
// Widget Definition
// ============================================================================

export const objectDetailDefinition = defineWidget<ObjectDetailConfig>({
  type: 'object-detail',
  displayName: 'Object Detail',
  description: 'Display detailed properties of a single object',
  icon: 'file-text',
  category: 'data',

  defaultConfig: {
    fields: [],
    layout: 'vertical',
    columns: 2,
  },

  defaultLayout: {
    width: 4,
    height: 3,
    minWidth: 2,
    minHeight: 2,
  },

  bindingSlots: [
    {
      name: 'object',
      label: 'Object',
      description: 'Single object to display',
      required: true,
      acceptedTypes: ['object'],
    },
  ],

  eventHandlers: [
    {
      name: 'onFieldClick',
      label: 'Field Click',
      description: 'Triggered when a field value is clicked',
      payloadType: '{ property: string, value: unknown }',
    },
  ],

  configSchema: {
    properties: {
      fields: {
        type: 'array',
        label: 'Fields',
        description: 'Fields to display',
        items: {
          type: 'object',
          label: 'Field',
          properties: {
            property: { type: 'string', label: 'Property' },
            label: { type: 'string', label: 'Label' },
            format: {
              type: 'enum',
              label: 'Format',
              enum: ['text', 'number', 'date', 'datetime', 'currency', 'percentage', 'custom'],
              default: 'text',
            },
            colSpan: { type: 'number', label: 'Column Span', default: 1 },
          },
        },
      },
      layout: {
        type: 'enum',
        label: 'Layout',
        enum: ['vertical', 'horizontal', 'grid'],
        enumLabels: ['Vertical', 'Horizontal', 'Grid'],
        default: 'vertical',
      },
      columns: {
        type: 'number',
        label: 'Columns',
        description: 'Number of columns (grid layout)',
        default: 2,
      },
    },
    required: ['fields'],
  },
});

// ============================================================================
// Component Props
// ============================================================================

export type ObjectDetailProps = WidgetComponentProps<ObjectDetailConfig>;

// ============================================================================
// Component
// ============================================================================

/**
 * ObjectDetail widget component
 */
export const ObjectDetail: React.FC<ObjectDetailProps> = ({
  widget: _widget,
  data: _data,
  onStateChange: _onStateChange,
  onAction: _onAction,
  isLoading: _isLoading = false,
  error: _error,
  isPreview: _isPreview = false,
}) => {
  // TODO: Implement detail rendering
  // TODO: Implement field formatting
  // TODO: Implement layout modes
  // TODO: Implement loading state
  // TODO: Implement error state

  return (
    <div data-testid="widget-object-detail">
      {/* TODO: Implement detail view */}
    </div>
  );
};

ObjectDetail.displayName = 'ObjectDetail';

export default ObjectDetail;
