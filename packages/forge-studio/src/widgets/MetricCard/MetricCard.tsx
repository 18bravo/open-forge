/**
 * MetricCard Widget
 *
 * Displays a single metric value with optional trend indicator,
 * formatting, and visual styling.
 */

import React from 'react';
import type {
  MetricCardConfig,
  WidgetDefinition,
} from '../../types';
import {
  defineWidget,
  type WidgetComponentProps,
} from '../registry';

// ============================================================================
// Widget Definition
// ============================================================================

export const metricCardDefinition = defineWidget<MetricCardConfig>({
  type: 'metric-card',
  displayName: 'Metric Card',
  description: 'Display a key metric with optional trend indicator',
  icon: 'trending-up',
  category: 'visualization',

  defaultConfig: {
    label: 'Metric',
    format: 'number',
    decimals: 0,
    showTrend: false,
    colorScheme: 'default',
  },

  defaultLayout: {
    width: 2,
    height: 2,
    minWidth: 2,
    minHeight: 1,
  },

  bindingSlots: [
    {
      name: 'value',
      label: 'Value',
      description: 'Metric value to display',
      required: true,
      acceptedTypes: ['aggregation', 'property', 'static'],
    },
    {
      name: 'comparison',
      label: 'Comparison Value',
      description: 'Previous value for trend calculation',
      required: false,
      acceptedTypes: ['aggregation', 'property', 'static'],
    },
  ],

  eventHandlers: [
    {
      name: 'onClick',
      label: 'Click',
      description: 'Triggered when the card is clicked',
    },
  ],

  configSchema: {
    properties: {
      label: {
        type: 'string',
        label: 'Label',
        description: 'Metric label',
        default: 'Metric',
      },
      format: {
        type: 'enum',
        label: 'Format',
        enum: ['number', 'currency', 'percentage'],
        enumLabels: ['Number', 'Currency', 'Percentage'],
        default: 'number',
      },
      decimals: {
        type: 'number',
        label: 'Decimal Places',
        default: 0,
      },
      currency: {
        type: 'string',
        label: 'Currency Code',
        description: 'ISO currency code (e.g., USD, EUR)',
        default: 'USD',
      },
      showTrend: {
        type: 'boolean',
        label: 'Show Trend',
        default: false,
      },
      icon: {
        type: 'string',
        label: 'Icon',
        description: 'Icon name from icon library',
      },
      colorScheme: {
        type: 'enum',
        label: 'Color Scheme',
        enum: ['default', 'success', 'warning', 'error', 'info'],
        enumLabels: ['Default', 'Success', 'Warning', 'Error', 'Info'],
        default: 'default',
      },
    },
    required: ['label'],
  },
});

// ============================================================================
// Component Props
// ============================================================================

export type MetricCardProps = WidgetComponentProps<MetricCardConfig>;

// ============================================================================
// Component
// ============================================================================

/**
 * MetricCard widget component
 */
export const MetricCard: React.FC<MetricCardProps> = ({
  widget: _widget,
  data: _data,
  onStateChange: _onStateChange,
  onAction: _onAction,
  isLoading: _isLoading = false,
  error: _error,
  isPreview: _isPreview = false,
}) => {
  // TODO: Implement metric display
  // TODO: Implement number formatting
  // TODO: Implement trend calculation
  // TODO: Implement trend indicator
  // TODO: Implement icon display
  // TODO: Implement color schemes
  // TODO: Implement loading state

  return (
    <div data-testid="widget-metric-card">
      {/* TODO: Implement metric card */}
    </div>
  );
};

MetricCard.displayName = 'MetricCard';

export default MetricCard;
