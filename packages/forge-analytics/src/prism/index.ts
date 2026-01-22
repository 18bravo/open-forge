/**
 * Prism Module
 *
 * Large-scale tabular analysis components including data grids,
 * pivot tables, and aggregation displays.
 */

// ============================================================================
// Components
// ============================================================================

export {
  DataGrid,
  DataGridHeader,
  DataGridRow,
  DataGridCell,
  DataGridPagination,
  DataGridToolbar,
  ColumnFilter,
  type DataGridProps,
  type DataGridHeaderProps,
  type DataGridRowProps,
  type DataGridCellProps,
  type DataGridPaginationProps,
  type DataGridToolbarProps,
  type ColumnFilterProps,
  type CellRendererType,
  type CellRendererConfig,
} from './DataGrid';

export {
  Pivot,
  PivotHeader,
  PivotRow,
  PivotCellComponent,
  PivotDimensionChip,
  PivotConfigPanel,
  type PivotProps,
  type PivotData,
  type PivotDimensionValue,
  type PivotCellValue,
  type PivotCell,
  type DrillDownPath,
  type PivotHeaderProps,
  type PivotRowProps,
  type PivotCellComponentProps,
  type PivotDimensionChipProps,
  type PivotConfigPanelProps,
} from './Pivot';

export {
  Aggregations,
  AggregationCard,
  AggregationTable,
  AggregationChart,
  TrendIndicator,
  AggregationValue,
  type AggregationsProps,
  type GroupedAggregationResults,
  type AggregationGroup,
  type AggregationCardProps,
  type AggregationTableProps,
  type AggregationChartProps,
  type TrendIndicatorProps,
  type AggregationValueProps,
} from './Aggregations';
