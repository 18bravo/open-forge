/**
 * Text Widget
 *
 * Displays text content with optional markdown rendering
 * and data binding support.
 */

import React from 'react';
import type {
  TextConfig,
  WidgetDefinition,
} from '../../types';
import {
  defineWidget,
  type WidgetComponentProps,
} from '../registry';

// ============================================================================
// Widget Definition
// ============================================================================

export const textDefinition = defineWidget<TextConfig>({
  type: 'text',
  displayName: 'Text',
  description: 'Display static or dynamic text with optional markdown',
  icon: 'type',
  category: 'layout',

  defaultConfig: {
    content: 'Enter your text here...',
    variant: 'body',
    align: 'left',
    markdown: false,
  },

  defaultLayout: {
    width: 4,
    height: 1,
    minWidth: 1,
    minHeight: 1,
  },

  bindingSlots: [
    {
      name: 'content',
      label: 'Content',
      description: 'Dynamic text content',
      required: false,
      acceptedTypes: ['property', 'static'],
    },
  ],

  eventHandlers: [
    {
      name: 'onLinkClick',
      label: 'Link Click',
      description: 'Triggered when a link in markdown is clicked',
      payloadType: '{ href: string }',
    },
  ],

  configSchema: {
    properties: {
      content: {
        type: 'string',
        label: 'Content',
        description: 'Text content (supports markdown if enabled)',
        default: 'Enter your text here...',
      },
      variant: {
        type: 'enum',
        label: 'Variant',
        enum: ['heading1', 'heading2', 'heading3', 'body', 'caption'],
        enumLabels: ['Heading 1', 'Heading 2', 'Heading 3', 'Body', 'Caption'],
        default: 'body',
      },
      align: {
        type: 'enum',
        label: 'Alignment',
        enum: ['left', 'center', 'right'],
        enumLabels: ['Left', 'Center', 'Right'],
        default: 'left',
      },
      markdown: {
        type: 'boolean',
        label: 'Enable Markdown',
        default: false,
      },
    },
  },
});

// ============================================================================
// Component Props
// ============================================================================

export type TextProps = WidgetComponentProps<TextConfig>;

// ============================================================================
// Component
// ============================================================================

/**
 * Text widget component
 */
export const Text: React.FC<TextProps> = ({
  widget: _widget,
  data: _data,
  onStateChange: _onStateChange,
  onAction: _onAction,
  isLoading: _isLoading = false,
  error: _error,
  isPreview: _isPreview = false,
}) => {
  // TODO: Implement text rendering
  // TODO: Implement markdown rendering
  // TODO: Implement text variants
  // TODO: Implement alignment
  // TODO: Implement dynamic content binding

  return (
    <div data-testid="widget-text">
      {/* TODO: Implement text display */}
    </div>
  );
};

Text.displayName = 'Text';

export default Text;
