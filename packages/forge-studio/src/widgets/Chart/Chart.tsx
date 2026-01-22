/**
 * Chart Widget
 *
 * Data visualization with multiple chart types using Recharts.
 * Supports bar, line, area, pie, donut, and scatter charts.
 */

import React from 'react';
import type {
  ChartConfig,
  WidgetDefinition,
} from '../../types';
import {
  defineWidget,
  type WidgetComponentProps,
} from '../registry';

// ============================================================================
// Widget Definition
// ============================================================================

export const chartDefinition = defineWidget<ChartConfig>({
  type: 'chart',
  displayName: 'Chart',
  description: 'Visualize data with various chart types',
  icon: 'bar-chart-2',
  category: 'visualization',

  defaultConfig: {
    chartType: 'bar',
    series: [],
    showLegend: true,
    legendPosition: 'bottom',
    showTooltips: true,
    animated: true,
  },

  defaultLayout: {
    width: 6,
    height: 4,
    minWidth: 3,
    minHeight: 2,
  },

  bindingSlots: [
    {
      name: 'data',
      label: 'Data Source',
      description: 'Data to visualize',
      required: true,
      acceptedTypes: ['object-set', 'aggregation'],
    },
  ],

  eventHandlers: [
    {
      name: 'onDataPointClick',
      label: 'Data Point Click',
      description: 'Triggered when a data point is clicked',
      payloadType: '{ dataKey: string, value: unknown, index: number }',
    },
    {
      name: 'onLegendClick',
      label: 'Legend Click',
      description: 'Triggered when a legend item is clicked',
      payloadType: '{ dataKey: string }',
    },
  ],

  configSchema: {
    properties: {
      chartType: {
        type: 'enum',
        label: 'Chart Type',
        enum: ['bar', 'line', 'area', 'pie', 'donut', 'scatter'],
        enumLabels: ['Bar', 'Line', 'Area', 'Pie', 'Donut', 'Scatter'],
        default: 'bar',
      },
      xAxis: {
        type: 'object',
        label: 'X Axis',
        properties: {
          label: { type: 'string', label: 'Label' },
          property: { type: 'string', label: 'Property' },
          type: {
            type: 'enum',
            label: 'Type',
            enum: ['category', 'number', 'time'],
            default: 'category',
          },
        },
      },
      yAxis: {
        type: 'object',
        label: 'Y Axis',
        properties: {
          label: { type: 'string', label: 'Label' },
          property: { type: 'string', label: 'Property' },
          type: {
            type: 'enum',
            label: 'Type',
            enum: ['category', 'number', 'time'],
            default: 'number',
          },
        },
      },
      series: {
        type: 'array',
        label: 'Series',
        items: {
          type: 'object',
          label: 'Series',
          properties: {
            name: { type: 'string', label: 'Name' },
            property: { type: 'string', label: 'Property' },
            color: { type: 'string', label: 'Color' },
          },
        },
      },
      showLegend: {
        type: 'boolean',
        label: 'Show Legend',
        default: true,
      },
      legendPosition: {
        type: 'enum',
        label: 'Legend Position',
        enum: ['top', 'bottom', 'left', 'right'],
        default: 'bottom',
      },
      showTooltips: {
        type: 'boolean',
        label: 'Show Tooltips',
        default: true,
      },
      animated: {
        type: 'boolean',
        label: 'Animated',
        default: true,
      },
    },
    required: ['chartType', 'series'],
  },
});

// ============================================================================
// Component Props
// ============================================================================

export type ChartProps = WidgetComponentProps<ChartConfig>;

// ============================================================================
// Component
// ============================================================================

/**
 * Chart widget component
 */
export const Chart: React.FC<ChartProps> = ({
  widget: _widget,
  data: _data,
  onStateChange: _onStateChange,
  onAction: _onAction,
  isLoading: _isLoading = false,
  error: _error,
  isPreview: _isPreview = false,
}) => {
  // TODO: Implement chart rendering with Recharts
  // TODO: Implement chart type switching
  // TODO: Implement responsive container
  // TODO: Implement tooltips
  // TODO: Implement legend
  // TODO: Implement animations
  // TODO: Implement loading state
  // TODO: Implement error state

  return (
    <div data-testid="widget-chart">
      {/* TODO: Implement chart */}
    </div>
  );
};

Chart.displayName = 'Chart';

export default Chart;
