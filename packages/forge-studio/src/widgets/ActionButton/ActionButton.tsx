/**
 * ActionButton Widget
 *
 * A button that triggers configured actions when clicked.
 * Supports confirmation dialogs, loading states, and various styles.
 */

import React from 'react';
import type {
  ActionButtonConfig,
  WidgetDefinition,
} from '../../types';
import {
  defineWidget,
  type WidgetComponentProps,
} from '../registry';

// ============================================================================
// Widget Definition
// ============================================================================

export const actionButtonDefinition = defineWidget<ActionButtonConfig>({
  type: 'action-button',
  displayName: 'Action Button',
  description: 'A button that triggers actions when clicked',
  icon: 'play-circle',
  category: 'action',

  defaultConfig: {
    label: 'Click Me',
    variant: 'primary',
    size: 'md',
    showLoading: true,
    disabled: false,
  },

  defaultLayout: {
    width: 2,
    height: 1,
    minWidth: 1,
    minHeight: 1,
  },

  bindingSlots: [
    {
      name: 'disabled',
      label: 'Disabled',
      description: 'Whether the button is disabled',
      required: false,
      acceptedTypes: ['property', 'static'],
    },
  ],

  eventHandlers: [
    {
      name: 'onClick',
      label: 'Click',
      description: 'Triggered when the button is clicked',
    },
    {
      name: 'onSuccess',
      label: 'Success',
      description: 'Triggered when the action completes successfully',
      payloadType: 'unknown',
    },
    {
      name: 'onError',
      label: 'Error',
      description: 'Triggered when the action fails',
      payloadType: 'Error',
    },
  ],

  configSchema: {
    properties: {
      label: {
        type: 'string',
        label: 'Label',
        default: 'Click Me',
      },
      variant: {
        type: 'enum',
        label: 'Variant',
        enum: ['primary', 'secondary', 'outline', 'ghost', 'destructive'],
        enumLabels: ['Primary', 'Secondary', 'Outline', 'Ghost', 'Destructive'],
        default: 'primary',
      },
      size: {
        type: 'enum',
        label: 'Size',
        enum: ['sm', 'md', 'lg'],
        enumLabels: ['Small', 'Medium', 'Large'],
        default: 'md',
      },
      icon: {
        type: 'string',
        label: 'Icon',
        description: 'Icon name from icon library',
      },
      showLoading: {
        type: 'boolean',
        label: 'Show Loading',
        description: 'Show loading spinner during action',
        default: true,
      },
      disabled: {
        type: 'boolean',
        label: 'Disabled',
        default: false,
      },
      confirmation: {
        type: 'object',
        label: 'Confirmation Dialog',
        properties: {
          title: { type: 'string', label: 'Title' },
          message: { type: 'string', label: 'Message' },
          confirmLabel: { type: 'string', label: 'Confirm Button', default: 'Confirm' },
          cancelLabel: { type: 'string', label: 'Cancel Button', default: 'Cancel' },
        },
      },
    },
    required: ['label'],
  },
});

// ============================================================================
// Component Props
// ============================================================================

export type ActionButtonProps = WidgetComponentProps<ActionButtonConfig>;

// ============================================================================
// Component
// ============================================================================

/**
 * ActionButton widget component
 */
export const ActionButton: React.FC<ActionButtonProps> = ({
  widget: _widget,
  data: _data,
  onStateChange: _onStateChange,
  onAction: _onAction,
  isLoading: _isLoading = false,
  error: _error,
  isPreview: _isPreview = false,
}) => {
  // TODO: Implement button rendering
  // TODO: Implement button variants
  // TODO: Implement button sizes
  // TODO: Implement icon display
  // TODO: Implement loading state
  // TODO: Implement disabled state
  // TODO: Implement confirmation dialog
  // TODO: Implement action execution

  return (
    <div data-testid="widget-action-button">
      {/* TODO: Implement action button */}
    </div>
  );
};

ActionButton.displayName = 'ActionButton';

export default ActionButton;
