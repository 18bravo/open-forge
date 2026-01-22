/**
 * Form Widget
 *
 * Configurable form for creating and editing objects with
 * validation, field types, and submission handling.
 */

import React from 'react';
import type {
  FormConfig,
  WidgetDefinition,
} from '../../types';
import {
  defineWidget,
  type WidgetComponentProps,
} from '../registry';

// ============================================================================
// Widget Definition
// ============================================================================

export const formDefinition = defineWidget<FormConfig>({
  type: 'form',
  displayName: 'Form',
  description: 'Create and edit objects with a configurable form',
  icon: 'clipboard-list',
  category: 'input',

  defaultConfig: {
    fields: [],
    submitLabel: 'Submit',
    cancelLabel: 'Cancel',
    showCancel: true,
    layout: 'vertical',
    columns: 1,
  },

  defaultLayout: {
    width: 4,
    height: 4,
    minWidth: 3,
    minHeight: 2,
  },

  bindingSlots: [
    {
      name: 'initialValues',
      label: 'Initial Values',
      description: 'Object with initial field values (for edit mode)',
      required: false,
      acceptedTypes: ['object', 'static'],
    },
    {
      name: 'objectType',
      label: 'Object Type',
      description: 'Object type for form schema',
      required: false,
      acceptedTypes: ['static'],
    },
  ],

  eventHandlers: [
    {
      name: 'onSubmit',
      label: 'Submit',
      description: 'Triggered when form is submitted',
      payloadType: 'Record<string, unknown>',
    },
    {
      name: 'onCancel',
      label: 'Cancel',
      description: 'Triggered when form is cancelled',
    },
    {
      name: 'onChange',
      label: 'Change',
      description: 'Triggered when any field value changes',
      payloadType: '{ field: string, value: unknown, values: Record<string, unknown> }',
    },
    {
      name: 'onValidationError',
      label: 'Validation Error',
      description: 'Triggered when validation fails',
      payloadType: 'Record<string, string>',
    },
  ],

  configSchema: {
    properties: {
      fields: {
        type: 'array',
        label: 'Fields',
        description: 'Form fields',
        items: {
          type: 'object',
          label: 'Field',
          properties: {
            property: { type: 'string', label: 'Property' },
            label: { type: 'string', label: 'Label' },
            placeholder: { type: 'string', label: 'Placeholder' },
            inputType: {
              type: 'enum',
              label: 'Input Type',
              enum: ['text', 'number', 'date', 'datetime', 'select', 'multiselect', 'checkbox', 'textarea', 'rich-text'],
              default: 'text',
            },
            required: { type: 'boolean', label: 'Required', default: false },
            disabled: { type: 'boolean', label: 'Disabled', default: false },
            colSpan: { type: 'number', label: 'Column Span', default: 1 },
          },
        },
      },
      submitLabel: {
        type: 'string',
        label: 'Submit Button Label',
        default: 'Submit',
      },
      cancelLabel: {
        type: 'string',
        label: 'Cancel Button Label',
        default: 'Cancel',
      },
      showCancel: {
        type: 'boolean',
        label: 'Show Cancel Button',
        default: true,
      },
      layout: {
        type: 'enum',
        label: 'Layout',
        enum: ['vertical', 'horizontal', 'grid'],
        default: 'vertical',
      },
      columns: {
        type: 'number',
        label: 'Columns',
        default: 1,
      },
    },
    required: ['fields'],
  },
});

// ============================================================================
// Component Props
// ============================================================================

export type FormProps = WidgetComponentProps<FormConfig>;

// ============================================================================
// Component
// ============================================================================

/**
 * Form widget component
 */
export const Form: React.FC<FormProps> = ({
  widget: _widget,
  data: _data,
  onStateChange: _onStateChange,
  onAction: _onAction,
  isLoading: _isLoading = false,
  error: _error,
  isPreview: _isPreview = false,
}) => {
  // TODO: Implement form rendering
  // TODO: Implement field types
  // TODO: Implement validation
  // TODO: Implement form state management
  // TODO: Implement submission handling
  // TODO: Implement loading state

  return (
    <div data-testid="widget-form">
      {/* TODO: Implement form */}
    </div>
  );
};

Form.displayName = 'Form';

export default Form;
