'use client';

import * as React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';

import { cn } from '@/lib/utils';

interface MetricDataPoint {
  timestamp: string;
  cpu: number;
  memory: number;
  requests: number;
  latency: number;
}

interface MetricsChartProps {
  className?: string;
  height?: number;
  showLegend?: boolean;
  metrics?: ('cpu' | 'memory' | 'requests' | 'latency')[];
  chartType?: 'line' | 'area';
}

export function MetricsChart({
  className,
  height = 300,
  showLegend = true,
  metrics = ['cpu', 'memory'],
  chartType = 'area',
}: MetricsChartProps) {
  // Generate mock time-series data
  const generateData = (): MetricDataPoint[] => {
    const data: MetricDataPoint[] = [];
    const now = new Date();

    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      data.push({
        timestamp: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        cpu: Math.floor(Math.random() * 40) + 30 + (i % 6 === 0 ? 20 : 0),
        memory: Math.floor(Math.random() * 30) + 45 + (i % 4 === 0 ? 15 : 0),
        requests: Math.floor(Math.random() * 500) + 200,
        latency: Math.floor(Math.random() * 100) + 50,
      });
    }

    return data;
  };

  const [data, setData] = React.useState<MetricDataPoint[]>([]);
  const [selectedMetrics, setSelectedMetrics] = React.useState<string[]>(metrics);

  React.useEffect(() => {
    setData(generateData());

    // Simulate real-time updates
    const interval = setInterval(() => {
      setData((prev) => {
        const newData = [...prev.slice(1)];
        const now = new Date();
        newData.push({
          timestamp: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          cpu: Math.floor(Math.random() * 40) + 30,
          memory: Math.floor(Math.random() * 30) + 45,
          requests: Math.floor(Math.random() * 500) + 200,
          latency: Math.floor(Math.random() * 100) + 50,
        });
        return newData;
      });
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  const metricConfig: Record<string, { color: string; label: string; unit: string }> = {
    cpu: { color: '#3b82f6', label: 'CPU Usage', unit: '%' },
    memory: { color: '#10b981', label: 'Memory Usage', unit: '%' },
    requests: { color: '#8b5cf6', label: 'Requests/min', unit: '' },
    latency: { color: '#f59e0b', label: 'Latency', unit: 'ms' },
  };

  const toggleMetric = (metric: string) => {
    setSelectedMetrics((prev) =>
      prev.includes(metric) ? prev.filter((m) => m !== metric) : [...prev, metric]
    );
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border bg-background p-3 shadow-lg">
          <p className="text-sm font-medium mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-4 text-sm">
              <span className="flex items-center gap-2">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                {metricConfig[entry.dataKey]?.label || entry.dataKey}
              </span>
              <span className="font-medium">
                {entry.value}{metricConfig[entry.dataKey]?.unit || ''}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const ChartComponent = chartType === 'area' ? AreaChart : LineChart;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Metric toggles */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(metricConfig).map(([key, config]) => (
          <button
            key={key}
            onClick={() => toggleMetric(key)}
            className={cn(
              'flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium transition-colors',
              selectedMetrics.includes(key)
                ? 'border-transparent'
                : 'border-border text-muted-foreground'
            )}
            style={{
              backgroundColor: selectedMetrics.includes(key)
                ? `${config.color}20`
                : undefined,
              color: selectedMetrics.includes(key) ? config.color : undefined,
            }}
          >
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: config.color }}
            />
            {config.label}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div style={{ height, minWidth: 0 }}>
        <ResponsiveContainer width="100%" height="100%" minWidth={1} minHeight={1}>
          <ChartComponent
            data={data}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="timestamp"
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
            />
            <YAxis tick={{ fontSize: 12 }} className="text-muted-foreground" />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && (
              <Legend
                wrapperStyle={{ fontSize: '12px' }}
                formatter={(value) => metricConfig[value]?.label || value}
              />
            )}
            {selectedMetrics.includes('cpu') && (
              chartType === 'area' ? (
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stroke={metricConfig.cpu.color}
                  fill={metricConfig.cpu.color}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              ) : (
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke={metricConfig.cpu.color}
                  strokeWidth={2}
                  dot={false}
                />
              )
            )}
            {selectedMetrics.includes('memory') && (
              chartType === 'area' ? (
                <Area
                  type="monotone"
                  dataKey="memory"
                  stroke={metricConfig.memory.color}
                  fill={metricConfig.memory.color}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              ) : (
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke={metricConfig.memory.color}
                  strokeWidth={2}
                  dot={false}
                />
              )
            )}
            {selectedMetrics.includes('requests') && (
              chartType === 'area' ? (
                <Area
                  type="monotone"
                  dataKey="requests"
                  stroke={metricConfig.requests.color}
                  fill={metricConfig.requests.color}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              ) : (
                <Line
                  type="monotone"
                  dataKey="requests"
                  stroke={metricConfig.requests.color}
                  strokeWidth={2}
                  dot={false}
                />
              )
            )}
            {selectedMetrics.includes('latency') && (
              chartType === 'area' ? (
                <Area
                  type="monotone"
                  dataKey="latency"
                  stroke={metricConfig.latency.color}
                  fill={metricConfig.latency.color}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              ) : (
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke={metricConfig.latency.color}
                  strokeWidth={2}
                  dot={false}
                />
              )
            )}
          </ChartComponent>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
