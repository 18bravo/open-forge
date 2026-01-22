/**
 * ObjectTable Widget
 *
 * Displays a table of objects from the ontology with sorting,
 * filtering, pagination, and row selection capabilities.
 */

import React from 'react';
import type {
  ObjectTableConfig,
  WidgetDefinition,
} from '../../types';
import {
  defineWidget,
  type WidgetComponentProps,
} from '../registry';

// ============================================================================
// Widget Definition
// ============================================================================

export const objectTableDefinition = defineWidget<ObjectTableConfig>({
  type: 'object-table',
  displayName: 'Object Table',
  description: 'Display objects in a sortable, filterable table with row selection',
  icon: 'table',
  category: 'data',

  defaultConfig: {
    columns: [],
    selectable: false,
    selectionMode: 'single',
    rowClickAction: false,
    editable: false,
    showPagination: true,
    resizableColumns: true,
    reorderableColumns: false,
  },

  defaultLayout: {
    width: 8,
    height: 4,
    minWidth: 4,
    minHeight: 2,
  },

  bindingSlots: [
    {
      name: 'data',
      label: 'Data Source',
      description: 'Object set to display in the table',
      required: true,
      acceptedTypes: ['object-set'],
    },
  ],

  eventHandlers: [
    {
      name: 'onRowClick',
      label: 'Row Click',
      description: 'Triggered when a row is clicked',
      payloadType: 'object',
    },
    {
      name: 'onRowSelect',
      label: 'Row Select',
      description: 'Triggered when row selection changes',
      payloadType: 'object[]',
    },
    {
      name: 'onCellEdit',
      label: 'Cell Edit',
      description: 'Triggered when a cell is edited',
      payloadType: '{ object: object, property: string, value: unknown }',
    },
  ],

  configSchema: {
    properties: {
      columns: {
        type: 'array',
        label: 'Columns',
        description: 'Table columns to display',
        items: {
          type: 'object',
          label: 'Column',
          properties: {
            property: { type: 'string', label: 'Property' },
            label: { type: 'string', label: 'Header Label' },
            width: { type: 'number', label: 'Width' },
            sortable: { type: 'boolean', label: 'Sortable', default: true },
            renderer: {
              type: 'enum',
              label: 'Renderer',
              enum: ['text', 'number', 'date', 'boolean', 'link', 'badge', 'custom'],
              default: 'text',
            },
          },
        },
      },
      selectable: {
        type: 'boolean',
        label: 'Enable Selection',
        default: false,
      },
      selectionMode: {
        type: 'enum',
        label: 'Selection Mode',
        enum: ['single', 'multiple'],
        enumLabels: ['Single', 'Multiple'],
        default: 'single',
      },
      showPagination: {
        type: 'boolean',
        label: 'Show Pagination',
        default: true,
      },
      rowClickAction: {
        type: 'boolean',
        label: 'Enable Row Click',
        default: false,
      },
      editable: {
        type: 'boolean',
        label: 'Enable Editing',
        default: false,
      },
    },
    required: ['columns'],
  },
});

// ============================================================================
// Component Props
// ============================================================================

export type ObjectTableProps = WidgetComponentProps<ObjectTableConfig>;

// ============================================================================
// Component
// ============================================================================

/**
 * ObjectTable widget component
 */
export const ObjectTable: React.FC<ObjectTableProps> = ({
  widget: _widget,
  data: _data,
  onStateChange: _onStateChange,
  onAction: _onAction,
  isLoading: _isLoading = false,
  error: _error,
  isPreview: _isPreview = false,
}) => {
  // TODO: Implement table rendering
  // TODO: Implement sorting
  // TODO: Implement pagination
  // TODO: Implement row selection
  // TODO: Implement cell editing
  // TODO: Implement column resizing
  // TODO: Implement loading state
  // TODO: Implement error state

  return (
    <div data-testid="widget-object-table">
      {/* TODO: Implement table */}
    </div>
  );
};

ObjectTable.displayName = 'ObjectTable';

export default ObjectTable;
