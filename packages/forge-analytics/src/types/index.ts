/**
 * Forge Analytics Type Definitions
 *
 * Core type definitions for analytics tools including Lens (object analysis),
 * Prism (tabular analysis), and Browser (object exploration).
 */

// ============================================================================
// Core Identifiers
// ============================================================================

/** Unique identifier for analytics entities */
export type AnalyticsId = string;

/** Reference to an ontology object type */
export type ObjectTypeRef = string;

/** Reference to a property within an object type */
export type PropertyRef = string;

/** Reference to a relationship link type */
export type LinkTypeRef = string;

// ============================================================================
// Common Data Types
// ============================================================================

/**
 * Represents a single object from the ontology
 */
export interface OntologyObject {
  /** Unique object identifier */
  id: string;

  /** Object type reference */
  objectType: ObjectTypeRef;

  /** Object properties as key-value pairs */
  properties: Record<string, unknown>;

  /** Primary display title */
  title?: string;

  /** Object description */
  description?: string;

  /** Creation timestamp */
  createdAt?: string;

  /** Last updated timestamp */
  updatedAt?: string;
}

/**
 * Represents a relationship between two objects
 */
export interface ObjectRelationship {
  /** Unique relationship identifier */
  id: string;

  /** Source object ID */
  sourceId: string;

  /** Target object ID */
  targetId: string;

  /** Relationship/link type */
  linkType: LinkTypeRef;

  /** Relationship properties */
  properties?: Record<string, unknown>;

  /** Direction of the relationship */
  direction: 'outgoing' | 'incoming' | 'bidirectional';
}

/**
 * Timeline event for object history
 */
export interface TimelineEvent {
  /** Unique event identifier */
  id: string;

  /** Associated object ID */
  objectId: string;

  /** Event type */
  type: 'created' | 'updated' | 'deleted' | 'linked' | 'unlinked' | 'custom';

  /** Event timestamp */
  timestamp: string;

  /** User who performed the action */
  userId?: string;

  /** User display name */
  userName?: string;

  /** Changed properties (for updates) */
  changes?: PropertyChange[];

  /** Related object (for link events) */
  relatedObjectId?: string;

  /** Custom event description */
  description?: string;

  /** Additional event metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Represents a property change in a timeline event
 */
export interface PropertyChange {
  /** Property that was changed */
  property: PropertyRef;

  /** Previous value */
  oldValue?: unknown;

  /** New value */
  newValue?: unknown;
}

// ============================================================================
// Filter and Sort Types
// ============================================================================

/**
 * Filter condition for data queries
 */
export interface FilterCondition {
  /** Property to filter on */
  property: PropertyRef;

  /** Filter operator */
  operator: FilterOperator;

  /** Value(s) to filter by */
  value: unknown;
}

export type FilterOperator =
  | 'equals'
  | 'notEquals'
  | 'contains'
  | 'notContains'
  | 'startsWith'
  | 'endsWith'
  | 'greaterThan'
  | 'greaterThanOrEqual'
  | 'lessThan'
  | 'lessThanOrEqual'
  | 'in'
  | 'notIn'
  | 'isNull'
  | 'isNotNull'
  | 'between';

/**
 * Sort configuration
 */
export interface SortConfig {
  /** Property to sort by */
  property: PropertyRef;

  /** Sort direction */
  direction: 'asc' | 'desc';
}

/**
 * Pagination configuration
 */
export interface PaginationConfig {
  /** Current page (0-indexed) */
  page: number;

  /** Number of items per page */
  pageSize: number;

  /** Total items (set by server) */
  totalItems?: number;

  /** Total pages (set by server) */
  totalPages?: number;
}

// ============================================================================
// Lens Types (Object-Driven Analysis)
// ============================================================================

/**
 * Configuration for ObjectView component
 */
export interface ObjectViewConfig {
  /** Object type to display */
  objectType: ObjectTypeRef;

  /** Fields to display in detail view */
  fields: ObjectViewField[];

  /** Layout mode */
  layout: 'vertical' | 'horizontal' | 'grid';

  /** Number of columns (for grid layout) */
  columns?: number;

  /** Show related objects section */
  showRelated?: boolean;

  /** Show timeline section */
  showTimeline?: boolean;

  /** Enable inline editing */
  editable?: boolean;
}

/**
 * Field configuration for ObjectView
 */
export interface ObjectViewField {
  /** Property reference */
  property: PropertyRef;

  /** Display label */
  label?: string;

  /** Field format */
  format?: 'text' | 'number' | 'date' | 'datetime' | 'currency' | 'percentage' | 'boolean' | 'link' | 'custom';

  /** Column span (for grid layout) */
  colSpan?: number;

  /** Whether field is editable */
  editable?: boolean;

  /** Custom renderer name */
  customRenderer?: string;
}

/**
 * Configuration for RelationshipGraph component
 */
export interface RelationshipGraphConfig {
  /** Root object ID to start from */
  rootObjectId?: string;

  /** Object types to include */
  objectTypes?: ObjectTypeRef[];

  /** Link types to include */
  linkTypes?: LinkTypeRef[];

  /** Maximum depth to traverse */
  maxDepth: number;

  /** Maximum nodes to display */
  maxNodes: number;

  /** Layout algorithm */
  layout: 'force' | 'hierarchical' | 'radial' | 'circular';

  /** Enable node clustering */
  enableClustering?: boolean;

  /** Node size based on property */
  nodeSizeProperty?: PropertyRef;

  /** Node color based on property */
  nodeColorProperty?: PropertyRef;

  /** Enable zoom and pan */
  interactive?: boolean;

  /** Show labels on nodes */
  showLabels?: boolean;

  /** Show labels on edges */
  showEdgeLabels?: boolean;
}

/**
 * Node in the relationship graph
 */
export interface GraphNode {
  /** Node ID (object ID) */
  id: string;

  /** Object type */
  objectType: ObjectTypeRef;

  /** Display label */
  label: string;

  /** Node properties for rendering */
  properties?: Record<string, unknown>;

  /** Computed node size */
  size?: number;

  /** Computed node color */
  color?: string;

  /** X position (set by layout) */
  x?: number;

  /** Y position (set by layout) */
  y?: number;

  /** Cluster ID (if clustering enabled) */
  clusterId?: string;
}

/**
 * Edge in the relationship graph
 */
export interface GraphEdge {
  /** Source node ID */
  source: string;

  /** Target node ID */
  target: string;

  /** Relationship type */
  linkType: LinkTypeRef;

  /** Edge label */
  label?: string;

  /** Edge weight */
  weight?: number;
}

/**
 * Complete graph data structure
 */
export interface GraphData {
  /** Graph nodes */
  nodes: GraphNode[];

  /** Graph edges */
  edges: GraphEdge[];
}

/**
 * Configuration for TimelineView component
 */
export interface TimelineViewConfig {
  /** Object ID to show timeline for */
  objectId?: string;

  /** Object type (for filtering) */
  objectType?: ObjectTypeRef;

  /** Event types to include */
  eventTypes?: TimelineEvent['type'][];

  /** Date range start */
  startDate?: string;

  /** Date range end */
  endDate?: string;

  /** Group events by time period */
  groupBy?: 'day' | 'week' | 'month' | 'year';

  /** Show user avatars */
  showAvatars?: boolean;

  /** Enable event details expansion */
  expandable?: boolean;

  /** Maximum events to display */
  maxEvents?: number;

  /** Sort order */
  sortOrder?: 'asc' | 'desc';
}

// ============================================================================
// Prism Types (Tabular Analysis)
// ============================================================================

/**
 * Configuration for DataGrid component
 */
export interface DataGridConfig {
  /** Object type to display */
  objectType: ObjectTypeRef;

  /** Columns to display */
  columns: DataGridColumn[];

  /** Enable row selection */
  selectable?: boolean;

  /** Selection mode */
  selectionMode?: 'single' | 'multiple';

  /** Enable sorting */
  sortable?: boolean;

  /** Enable column filtering */
  filterable?: boolean;

  /** Enable column resizing */
  resizable?: boolean;

  /** Enable column reordering */
  reorderable?: boolean;

  /** Enable row grouping */
  groupable?: boolean;

  /** Row height */
  rowHeight?: number;

  /** Header height */
  headerHeight?: number;

  /** Enable virtual scrolling */
  virtualScroll?: boolean;

  /** Enable inline editing */
  editable?: boolean;

  /** Enable row expansion */
  expandable?: boolean;
}

/**
 * Column configuration for DataGrid
 */
export interface DataGridColumn {
  /** Unique column ID */
  id: string;

  /** Property reference */
  property: PropertyRef;

  /** Column header */
  header: string;

  /** Column width */
  width?: number;

  /** Minimum width */
  minWidth?: number;

  /** Maximum width */
  maxWidth?: number;

  /** Enable sorting for this column */
  sortable?: boolean;

  /** Enable filtering for this column */
  filterable?: boolean;

  /** Enable resizing for this column */
  resizable?: boolean;

  /** Cell renderer type */
  cellRenderer?: 'text' | 'number' | 'date' | 'datetime' | 'boolean' | 'badge' | 'link' | 'progress' | 'custom';

  /** Custom cell renderer configuration */
  cellRendererConfig?: Record<string, unknown>;

  /** Alignment */
  align?: 'left' | 'center' | 'right';

  /** Whether column is pinned */
  pinned?: 'left' | 'right' | false;

  /** Whether column is visible */
  visible?: boolean;

  /** Aggregation function for grouped data */
  aggregation?: 'sum' | 'avg' | 'min' | 'max' | 'count' | 'first' | 'last';
}

/**
 * Configuration for Pivot component
 */
export interface PivotConfig {
  /** Object type to analyze */
  objectType: ObjectTypeRef;

  /** Row dimensions */
  rows: PivotDimension[];

  /** Column dimensions */
  columns: PivotDimension[];

  /** Value measures */
  values: PivotMeasure[];

  /** Enable drill-down */
  drillDown?: boolean;

  /** Show grand totals */
  showGrandTotals?: boolean;

  /** Show sub-totals */
  showSubTotals?: boolean;

  /** Enable value formatting */
  enableFormatting?: boolean;

  /** Enable conditional formatting */
  enableConditionalFormatting?: boolean;

  /** Conditional formatting rules */
  conditionalFormattingRules?: ConditionalFormattingRule[];
}

/**
 * Dimension configuration for pivot table
 */
export interface PivotDimension {
  /** Property reference */
  property: PropertyRef;

  /** Display label */
  label: string;

  /** Sort order */
  sortOrder?: 'asc' | 'desc';

  /** Show totals for this dimension */
  showTotals?: boolean;

  /** Date grouping (for date properties) */
  dateGrouping?: 'day' | 'week' | 'month' | 'quarter' | 'year';
}

/**
 * Measure configuration for pivot table
 */
export interface PivotMeasure {
  /** Property reference */
  property: PropertyRef;

  /** Display label */
  label: string;

  /** Aggregation function */
  aggregation: 'sum' | 'avg' | 'min' | 'max' | 'count' | 'countDistinct';

  /** Number format */
  format?: 'number' | 'currency' | 'percentage';

  /** Decimal places */
  decimals?: number;
}

/**
 * Conditional formatting rule
 */
export interface ConditionalFormattingRule {
  /** Rule ID */
  id: string;

  /** Measure to apply rule to */
  measureProperty: PropertyRef;

  /** Condition operator */
  operator: FilterOperator;

  /** Threshold value(s) */
  value: unknown;

  /** Background color */
  backgroundColor?: string;

  /** Text color */
  textColor?: string;

  /** Font weight */
  fontWeight?: 'normal' | 'bold';
}

/**
 * Configuration for Aggregations component
 */
export interface AggregationsConfig {
  /** Object type to aggregate */
  objectType: ObjectTypeRef;

  /** Aggregation definitions */
  aggregations: AggregationDefinition[];

  /** Group by dimensions */
  groupBy?: PropertyRef[];

  /** Filters to apply */
  filters?: FilterCondition[];

  /** Display layout */
  layout: 'cards' | 'table' | 'chart';

  /** Chart type (if layout is 'chart') */
  chartType?: 'bar' | 'line' | 'pie' | 'donut';
}

/**
 * Single aggregation definition
 */
export interface AggregationDefinition {
  /** Aggregation ID */
  id: string;

  /** Display label */
  label: string;

  /** Property to aggregate */
  property: PropertyRef;

  /** Aggregation function */
  function: 'sum' | 'avg' | 'min' | 'max' | 'count' | 'countDistinct' | 'stdDev' | 'variance';

  /** Result format */
  format?: 'number' | 'currency' | 'percentage';

  /** Decimal places */
  decimals?: number;

  /** Icon name */
  icon?: string;

  /** Color scheme */
  colorScheme?: 'default' | 'success' | 'warning' | 'error' | 'info';
}

/**
 * Aggregation result
 */
export interface AggregationResult {
  /** Aggregation ID */
  id: string;

  /** Computed value */
  value: number;

  /** Previous value (for comparison) */
  previousValue?: number;

  /** Trend direction */
  trend?: 'up' | 'down' | 'flat';

  /** Trend percentage */
  trendPercentage?: number;

  /** Group values (if grouped) */
  groupValues?: Record<PropertyRef, unknown>;
}

// ============================================================================
// Browser Types (Object Explorer)
// ============================================================================

/**
 * Configuration for Search component
 */
export interface SearchConfig {
  /** Object types to search */
  objectTypes?: ObjectTypeRef[];

  /** Properties to search in */
  searchableProperties?: PropertyRef[];

  /** Enable fuzzy matching */
  fuzzyMatch?: boolean;

  /** Minimum characters before search */
  minCharacters?: number;

  /** Debounce delay in ms */
  debounceMs?: number;

  /** Maximum results to show */
  maxResults?: number;

  /** Show recent searches */
  showRecentSearches?: boolean;

  /** Show search suggestions */
  showSuggestions?: boolean;

  /** Placeholder text */
  placeholder?: string;
}

/**
 * Search result item
 */
export interface SearchResult {
  /** Object ID */
  id: string;

  /** Object type */
  objectType: ObjectTypeRef;

  /** Display title */
  title: string;

  /** Subtitle/description */
  subtitle?: string;

  /** Search score */
  score: number;

  /** Highlighted matches */
  highlights?: SearchHighlight[];

  /** Object properties */
  properties?: Record<string, unknown>;
}

/**
 * Highlighted match in search result
 */
export interface SearchHighlight {
  /** Property that matched */
  property: PropertyRef;

  /** Original text */
  text: string;

  /** Match positions */
  matches: Array<{ start: number; end: number }>;
}

/**
 * Configuration for ObjectList component
 */
export interface ObjectListConfig {
  /** Object type to display */
  objectType: ObjectTypeRef;

  /** Display mode */
  displayMode: 'list' | 'grid' | 'compact';

  /** Fields to display in list items */
  displayFields: ObjectListField[];

  /** Enable selection */
  selectable?: boolean;

  /** Selection mode */
  selectionMode?: 'single' | 'multiple';

  /** Enable grouping */
  groupBy?: PropertyRef;

  /** Sort configuration */
  defaultSort?: SortConfig;

  /** Items per page (for pagination) */
  pageSize?: number;

  /** Show item count */
  showCount?: boolean;

  /** Enable drag and drop reordering */
  reorderable?: boolean;

  /** Empty state message */
  emptyMessage?: string;
}

/**
 * Field configuration for ObjectList items
 */
export interface ObjectListField {
  /** Property reference */
  property: PropertyRef;

  /** Display role */
  role: 'title' | 'subtitle' | 'description' | 'meta' | 'badge' | 'avatar';

  /** Format */
  format?: 'text' | 'number' | 'date' | 'datetime' | 'relative';

  /** Maximum length (for text truncation) */
  maxLength?: number;
}

/**
 * Configuration for Filters component
 */
export interface FiltersConfig {
  /** Object type being filtered */
  objectType: ObjectTypeRef;

  /** Filter definitions */
  filters: FilterDefinition[];

  /** Layout direction */
  direction: 'horizontal' | 'vertical';

  /** Show clear all button */
  showClearAll?: boolean;

  /** Auto-apply filters */
  autoApply?: boolean;

  /** Collapsible in vertical layout */
  collapsible?: boolean;

  /** Default collapsed state */
  defaultCollapsed?: boolean;
}

/**
 * Single filter definition
 */
export interface FilterDefinition {
  /** Filter ID */
  id: string;

  /** Property to filter */
  property: PropertyRef;

  /** Display label */
  label: string;

  /** Filter input type */
  inputType: 'text' | 'select' | 'multiselect' | 'checkbox' | 'date' | 'dateRange' | 'numberRange' | 'slider';

  /** Options for select types */
  options?: FilterOption[];

  /** Dynamic options from API */
  dynamicOptions?: boolean;

  /** Placeholder text */
  placeholder?: string;

  /** Default value */
  defaultValue?: unknown;

  /** Range configuration (for range types) */
  rangeConfig?: RangeConfig;
}

/**
 * Filter option for select/multiselect
 */
export interface FilterOption {
  /** Option value */
  value: unknown;

  /** Display label */
  label: string;

  /** Option count (for facets) */
  count?: number;
}

/**
 * Range configuration
 */
export interface RangeConfig {
  /** Minimum value */
  min?: number;

  /** Maximum value */
  max?: number;

  /** Step increment */
  step?: number;

  /** Show inputs alongside slider */
  showInputs?: boolean;
}

/**
 * Active filter state
 */
export interface ActiveFilter {
  /** Filter ID */
  filterId: string;

  /** Property being filtered */
  property: PropertyRef;

  /** Filter operator */
  operator: FilterOperator;

  /** Filter value(s) */
  value: unknown;
}

// ============================================================================
// Shared Component Props Types
// ============================================================================

/**
 * Common props for all analytics components
 */
export interface BaseAnalyticsProps {
  /** Component ID */
  id?: string;

  /** CSS class name */
  className?: string;

  /** Inline styles */
  style?: React.CSSProperties;

  /** Loading state */
  isLoading?: boolean;

  /** Error state */
  error?: Error | null;

  /** Disabled state */
  disabled?: boolean;
}

/**
 * Props for components that support selection
 */
export interface SelectableProps<T = unknown> {
  /** Selected items */
  selectedItems?: T[];

  /** Selection change handler */
  onSelectionChange?: (items: T[]) => void;
}

/**
 * Props for components with pagination
 */
export interface PaginatedProps {
  /** Pagination configuration */
  pagination?: PaginationConfig;

  /** Pagination change handler */
  onPaginationChange?: (pagination: PaginationConfig) => void;
}

/**
 * Props for components with sorting
 */
export interface SortableProps {
  /** Current sort configuration */
  sort?: SortConfig[];

  /** Sort change handler */
  onSortChange?: (sort: SortConfig[]) => void;
}

/**
 * Props for components with filtering
 */
export interface FilterableProps {
  /** Active filters */
  filters?: ActiveFilter[];

  /** Filter change handler */
  onFilterChange?: (filters: ActiveFilter[]) => void;
}

// ============================================================================
// API Response Types
// ============================================================================

/**
 * Standard API response wrapper
 */
export interface ApiResponse<T> {
  /** Response data */
  data: T;

  /** Success flag */
  success: boolean;

  /** Error message (if any) */
  error?: string;

  /** Additional metadata */
  meta?: Record<string, unknown>;
}

/**
 * Paginated API response
 */
export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  /** Pagination info */
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}

/**
 * Object query request
 */
export interface ObjectQueryRequest {
  /** Object type to query */
  objectType: ObjectTypeRef;

  /** Filters to apply */
  filters?: FilterCondition[];

  /** Sort configuration */
  sort?: SortConfig[];

  /** Pagination */
  pagination?: PaginationConfig;

  /** Properties to include */
  properties?: PropertyRef[];

  /** Include related objects */
  includeRelated?: boolean;
}

/**
 * Relationship query request
 */
export interface RelationshipQueryRequest {
  /** Starting object ID */
  objectId: string;

  /** Link types to traverse */
  linkTypes?: LinkTypeRef[];

  /** Direction to traverse */
  direction?: 'outgoing' | 'incoming' | 'both';

  /** Maximum depth */
  maxDepth?: number;

  /** Maximum results */
  maxResults?: number;
}

/**
 * Timeline query request
 */
export interface TimelineQueryRequest {
  /** Object ID */
  objectId?: string;

  /** Object type filter */
  objectType?: ObjectTypeRef;

  /** Event types to include */
  eventTypes?: TimelineEvent['type'][];

  /** Start date */
  startDate?: string;

  /** End date */
  endDate?: string;

  /** Pagination */
  pagination?: PaginationConfig;
}
