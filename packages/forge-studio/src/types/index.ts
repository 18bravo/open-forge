/**
 * Forge Studio Type Definitions
 *
 * Core type definitions for the low-code app builder, including
 * application structure, widgets, data binding, and actions.
 */

// ============================================================================
// Core Identifiers
// ============================================================================

/** Unique identifier for studio entities */
export type StudioId = string;

/** Reference to an ontology object type */
export type ObjectTypeRef = string;

/** Reference to a property within an object type */
export type PropertyRef = string;

// ============================================================================
// Data Binding Types
// ============================================================================

/**
 * Represents a binding to a data source
 * Used for connecting widgets to ontology data
 */
export interface DataBinding {
  /** Unique identifier for this binding */
  id: StudioId;

  /** Human-readable name for this binding */
  name: string;

  /** Type of data source */
  sourceType: 'object-set' | 'object' | 'property' | 'aggregation' | 'static';

  /** Reference to the ontology object type */
  objectType?: ObjectTypeRef;

  /** Query filters to apply */
  filters?: DataFilter[];

  /** Sorting configuration */
  sort?: DataSort[];

  /** Pagination configuration */
  pagination?: PaginationConfig;

  /** Static value (for sourceType: 'static') */
  staticValue?: unknown;

  /** Expression for computed bindings */
  expression?: string;
}

/**
 * Filter configuration for data queries
 */
export interface DataFilter {
  /** Property to filter on */
  property: PropertyRef;

  /** Filter operator */
  operator: FilterOperator;

  /** Value to filter by */
  value: unknown;

  /** Whether this filter is linked to another widget's state */
  linkedWidgetId?: StudioId;
}

export type FilterOperator =
  | 'equals'
  | 'notEquals'
  | 'contains'
  | 'startsWith'
  | 'endsWith'
  | 'greaterThan'
  | 'lessThan'
  | 'greaterThanOrEqual'
  | 'lessThanOrEqual'
  | 'in'
  | 'notIn'
  | 'isNull'
  | 'isNotNull';

/**
 * Sort configuration for data queries
 */
export interface DataSort {
  /** Property to sort by */
  property: PropertyRef;

  /** Sort direction */
  direction: 'asc' | 'desc';
}

/**
 * Pagination configuration
 */
export interface PaginationConfig {
  /** Number of items per page */
  pageSize: number;

  /** Current page (0-indexed) */
  currentPage?: number;

  /** Enable infinite scroll instead of pagination */
  infiniteScroll?: boolean;
}

// ============================================================================
// Action Types
// ============================================================================

/**
 * Action that can be triggered by user interaction
 */
export interface StudioAction {
  /** Unique identifier for this action */
  id: StudioId;

  /** Human-readable name */
  name: string;

  /** Type of action to execute */
  type: ActionType;

  /** Action-specific configuration */
  config: ActionConfig;

  /** Conditions that must be met for action to execute */
  conditions?: ActionCondition[];
}

export type ActionType =
  | 'navigate'
  | 'create-object'
  | 'update-object'
  | 'delete-object'
  | 'execute-function'
  | 'set-state'
  | 'open-modal'
  | 'close-modal'
  | 'refresh-data'
  | 'custom-code';

/**
 * Union type for action configurations
 */
export type ActionConfig =
  | NavigateActionConfig
  | ObjectMutationConfig
  | ExecuteFunctionConfig
  | SetStateConfig
  | ModalActionConfig
  | RefreshDataConfig
  | CustomCodeConfig;

export interface NavigateActionConfig {
  type: 'navigate';
  /** Target page ID within the app */
  pageId?: StudioId;
  /** External URL to navigate to */
  externalUrl?: string;
  /** Query parameters to pass */
  params?: Record<string, DataBinding>;
}

export interface ObjectMutationConfig {
  type: 'create-object' | 'update-object' | 'delete-object';
  /** Object type to mutate */
  objectType: ObjectTypeRef;
  /** Property values for create/update */
  values?: Record<PropertyRef, DataBinding>;
  /** Object reference for update/delete */
  objectRef?: DataBinding;
}

export interface ExecuteFunctionConfig {
  type: 'execute-function';
  /** Ontology function to execute */
  functionId: string;
  /** Function parameters */
  parameters?: Record<string, DataBinding>;
}

export interface SetStateConfig {
  type: 'set-state';
  /** State variable to update */
  stateKey: string;
  /** New value */
  value: DataBinding;
}

export interface ModalActionConfig {
  type: 'open-modal' | 'close-modal';
  /** Modal ID to open/close */
  modalId?: StudioId;
}

export interface RefreshDataConfig {
  type: 'refresh-data';
  /** Specific binding IDs to refresh (empty = all) */
  bindingIds?: StudioId[];
}

export interface CustomCodeConfig {
  type: 'custom-code';
  /** TypeScript/JavaScript code to execute */
  code: string;
}

/**
 * Condition for conditional action execution
 */
export interface ActionCondition {
  /** Left-hand side of condition */
  left: DataBinding;
  /** Comparison operator */
  operator: FilterOperator;
  /** Right-hand side of condition */
  right: DataBinding;
}

// ============================================================================
// Widget Types
// ============================================================================

/**
 * Widget type identifier
 */
export type WidgetType =
  | 'object-table'
  | 'object-detail'
  | 'form'
  | 'chart'
  | 'metric-card'
  | 'text'
  | 'filter-bar'
  | 'action-button';

/**
 * Base widget configuration shared by all widgets
 */
export interface BaseWidgetConfig {
  /** Widget title (displayed in header) */
  title?: string;

  /** Whether the widget is visible */
  visible?: boolean | DataBinding;

  /** CSS class names to apply */
  className?: string;

  /** Inline styles */
  style?: React.CSSProperties;
}

/**
 * Instance of a widget placed on a page
 */
export interface WidgetInstance<T extends BaseWidgetConfig = BaseWidgetConfig> {
  /** Unique identifier */
  id: StudioId;

  /** Widget type */
  type: WidgetType;

  /** Widget-specific configuration */
  config: T;

  /** Data bindings for this widget */
  bindings: Record<string, DataBinding>;

  /** Actions triggered by widget events */
  actions: Record<string, StudioAction[]>;

  /** Position within the grid layout */
  layout: WidgetLayout;
}

/**
 * Widget position and size in grid layout
 */
export interface WidgetLayout {
  /** Column position (0-indexed) */
  x: number;

  /** Row position (0-indexed) */
  y: number;

  /** Width in grid columns */
  width: number;

  /** Height in grid rows */
  height: number;

  /** Minimum width */
  minWidth?: number;

  /** Minimum height */
  minHeight?: number;
}

// ============================================================================
// Widget-Specific Configurations
// ============================================================================

export interface ObjectTableConfig extends BaseWidgetConfig {
  /** Columns to display */
  columns: TableColumn[];

  /** Enable row selection */
  selectable?: boolean;

  /** Selection mode */
  selectionMode?: 'single' | 'multiple';

  /** Enable row click action */
  rowClickAction?: boolean;

  /** Enable inline editing */
  editable?: boolean;

  /** Show pagination controls */
  showPagination?: boolean;

  /** Enable column resizing */
  resizableColumns?: boolean;

  /** Enable column reordering */
  reorderableColumns?: boolean;
}

export interface TableColumn {
  /** Property to display */
  property: PropertyRef;

  /** Column header label */
  label?: string;

  /** Column width */
  width?: number | string;

  /** Enable sorting for this column */
  sortable?: boolean;

  /** Custom cell renderer type */
  renderer?: 'text' | 'number' | 'date' | 'boolean' | 'link' | 'badge' | 'custom';

  /** Custom renderer configuration */
  rendererConfig?: Record<string, unknown>;
}

export interface ObjectDetailConfig extends BaseWidgetConfig {
  /** Fields to display */
  fields: DetailField[];

  /** Layout mode */
  layout?: 'vertical' | 'horizontal' | 'grid';

  /** Number of columns (for grid layout) */
  columns?: number;
}

export interface DetailField {
  /** Property to display */
  property: PropertyRef;

  /** Field label */
  label?: string;

  /** Display format */
  format?: 'text' | 'number' | 'date' | 'datetime' | 'currency' | 'percentage' | 'custom';

  /** Span multiple columns (for grid layout) */
  colSpan?: number;
}

export interface FormConfig extends BaseWidgetConfig {
  /** Form fields */
  fields: FormField[];

  /** Submit button text */
  submitLabel?: string;

  /** Cancel button text */
  cancelLabel?: string;

  /** Show cancel button */
  showCancel?: boolean;

  /** Layout mode */
  layout?: 'vertical' | 'horizontal' | 'grid';

  /** Number of columns (for grid layout) */
  columns?: number;
}

export interface FormField {
  /** Property to bind */
  property: PropertyRef;

  /** Field label */
  label?: string;

  /** Placeholder text */
  placeholder?: string;

  /** Input type */
  inputType: 'text' | 'number' | 'date' | 'datetime' | 'select' | 'multiselect' | 'checkbox' | 'textarea' | 'rich-text';

  /** Whether field is required */
  required?: boolean;

  /** Validation rules */
  validation?: ValidationRule[];

  /** Options for select/multiselect */
  options?: SelectOption[] | DataBinding;

  /** Default value */
  defaultValue?: unknown | DataBinding;

  /** Disabled state */
  disabled?: boolean | DataBinding;

  /** Span multiple columns */
  colSpan?: number;
}

export interface SelectOption {
  label: string;
  value: unknown;
}

export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
  value?: unknown;
  message: string;
}

export interface ChartConfig extends BaseWidgetConfig {
  /** Chart type */
  chartType: 'bar' | 'line' | 'area' | 'pie' | 'donut' | 'scatter';

  /** X-axis configuration */
  xAxis?: AxisConfig;

  /** Y-axis configuration */
  yAxis?: AxisConfig;

  /** Series configurations */
  series: ChartSeries[];

  /** Show legend */
  showLegend?: boolean;

  /** Legend position */
  legendPosition?: 'top' | 'bottom' | 'left' | 'right';

  /** Enable tooltips */
  showTooltips?: boolean;

  /** Enable animation */
  animated?: boolean;
}

export interface AxisConfig {
  /** Axis label */
  label?: string;

  /** Property for axis values */
  property?: PropertyRef;

  /** Axis type */
  type?: 'category' | 'number' | 'time';

  /** Number format */
  format?: string;
}

export interface ChartSeries {
  /** Series name */
  name: string;

  /** Property for series values */
  property: PropertyRef;

  /** Series color */
  color?: string;
}

export interface MetricCardConfig extends BaseWidgetConfig {
  /** Metric label */
  label: string;

  /** Value format */
  format?: 'number' | 'currency' | 'percentage';

  /** Number of decimal places */
  decimals?: number;

  /** Currency code (for currency format) */
  currency?: string;

  /** Show trend indicator */
  showTrend?: boolean;

  /** Trend comparison binding */
  trendComparison?: DataBinding;

  /** Icon name */
  icon?: string;

  /** Card color scheme */
  colorScheme?: 'default' | 'success' | 'warning' | 'error' | 'info';
}

export interface TextConfig extends BaseWidgetConfig {
  /** Text content (supports markdown) */
  content: string | DataBinding;

  /** Text variant */
  variant?: 'heading1' | 'heading2' | 'heading3' | 'body' | 'caption';

  /** Text alignment */
  align?: 'left' | 'center' | 'right';

  /** Enable markdown rendering */
  markdown?: boolean;
}

export interface FilterBarConfig extends BaseWidgetConfig {
  /** Filter fields */
  filters: FilterField[];

  /** Layout direction */
  direction?: 'horizontal' | 'vertical';

  /** Show clear all button */
  showClearAll?: boolean;

  /** Auto-apply filters (vs manual apply button) */
  autoApply?: boolean;
}

export interface FilterField {
  /** Unique identifier */
  id: StudioId;

  /** Property to filter */
  property: PropertyRef;

  /** Filter label */
  label?: string;

  /** Input type */
  inputType: 'text' | 'select' | 'multiselect' | 'date-range' | 'number-range';

  /** Options for select types */
  options?: SelectOption[] | DataBinding;

  /** Placeholder text */
  placeholder?: string;

  /** Default value */
  defaultValue?: unknown;
}

export interface ActionButtonConfig extends BaseWidgetConfig {
  /** Button label */
  label: string;

  /** Button variant */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';

  /** Button size */
  size?: 'sm' | 'md' | 'lg';

  /** Icon name (before label) */
  icon?: string;

  /** Show loading state during action */
  showLoading?: boolean;

  /** Disabled state */
  disabled?: boolean | DataBinding;

  /** Confirmation dialog config */
  confirmation?: ConfirmationConfig;
}

export interface ConfirmationConfig {
  /** Dialog title */
  title: string;

  /** Dialog message */
  message: string;

  /** Confirm button label */
  confirmLabel?: string;

  /** Cancel button label */
  cancelLabel?: string;
}

// ============================================================================
// Page Structure Types
// ============================================================================

/**
 * Section within a page (for organizing widgets)
 */
export interface PageSection {
  /** Unique identifier */
  id: StudioId;

  /** Section title */
  title?: string;

  /** Section description */
  description?: string;

  /** Whether section is collapsible */
  collapsible?: boolean;

  /** Default collapsed state */
  defaultCollapsed?: boolean;

  /** Widgets in this section */
  widgets: WidgetInstance[];

  /** Grid configuration */
  gridConfig?: GridConfig;
}

/**
 * Grid layout configuration
 */
export interface GridConfig {
  /** Number of columns */
  columns: number;

  /** Gap between items (in pixels) */
  gap?: number;

  /** Row height (in pixels) */
  rowHeight?: number;
}

/**
 * Page within a studio application
 */
export interface StudioPage {
  /** Unique identifier */
  id: StudioId;

  /** Page name (displayed in navigation) */
  name: string;

  /** Page path (URL slug) */
  path: string;

  /** Page icon */
  icon?: string;

  /** Page description */
  description?: string;

  /** Whether page is visible in navigation */
  showInNav?: boolean;

  /** Page-level parameters (from URL or navigation) */
  parameters?: PageParameter[];

  /** Page sections containing widgets */
  sections: PageSection[];

  /** Page-level state variables */
  state?: Record<string, unknown>;

  /** Page-level data bindings (shared across widgets) */
  bindings?: Record<string, DataBinding>;
}

/**
 * Parameter that can be passed to a page
 */
export interface PageParameter {
  /** Parameter name */
  name: string;

  /** Parameter type */
  type: 'string' | 'number' | 'boolean' | 'object-ref';

  /** Whether parameter is required */
  required?: boolean;

  /** Default value */
  defaultValue?: unknown;
}

// ============================================================================
// Application Types
// ============================================================================

/**
 * Complete studio application definition
 */
export interface StudioApp {
  /** Unique identifier */
  id: StudioId;

  /** Application name */
  name: string;

  /** Application description */
  description?: string;

  /** Application icon */
  icon?: string;

  /** Application version */
  version: string;

  /** Application pages */
  pages: StudioPage[];

  /** Default page (landing page) */
  defaultPageId: StudioId;

  /** Application-level theme configuration */
  theme?: ThemeConfig;

  /** Application-level settings */
  settings?: AppSettings;

  /** Global state variables */
  globalState?: Record<string, unknown>;

  /** Global data bindings */
  globalBindings?: Record<string, DataBinding>;

  /** Created timestamp */
  createdAt: string;

  /** Last updated timestamp */
  updatedAt: string;

  /** Creator user ID */
  createdBy: string;
}

/**
 * Theme configuration for the application
 */
export interface ThemeConfig {
  /** Primary color */
  primaryColor?: string;

  /** Secondary color */
  secondaryColor?: string;

  /** Background color */
  backgroundColor?: string;

  /** Font family */
  fontFamily?: string;

  /** Border radius */
  borderRadius?: 'none' | 'sm' | 'md' | 'lg';

  /** Custom CSS */
  customCss?: string;
}

/**
 * Application-level settings
 */
export interface AppSettings {
  /** Enable authentication */
  requireAuth?: boolean;

  /** Allowed roles (if auth enabled) */
  allowedRoles?: string[];

  /** Enable audit logging */
  auditLogging?: boolean;

  /** Cache TTL in seconds */
  cacheTtl?: number;

  /** Maximum rows to fetch */
  maxRowsFetch?: number;
}

// ============================================================================
// Widget Registry Types
// ============================================================================

/**
 * Widget definition for the registry
 */
export interface WidgetDefinition<T extends BaseWidgetConfig = BaseWidgetConfig> {
  /** Widget type identifier */
  type: WidgetType;

  /** Display name */
  displayName: string;

  /** Description */
  description: string;

  /** Icon name */
  icon: string;

  /** Category for widget panel */
  category: WidgetCategory;

  /** Default configuration */
  defaultConfig: T;

  /** Default layout */
  defaultLayout: Partial<WidgetLayout>;

  /** Available binding slots */
  bindingSlots: BindingSlot[];

  /** Available event handlers */
  eventHandlers: EventHandlerDefinition[];

  /** Configuration schema (for ConfigPanel) */
  configSchema: ConfigSchema;
}

export type WidgetCategory = 'data' | 'input' | 'visualization' | 'layout' | 'action';

/**
 * Slot for data binding
 */
export interface BindingSlot {
  /** Slot name */
  name: string;

  /** Display label */
  label: string;

  /** Description */
  description?: string;

  /** Whether binding is required */
  required: boolean;

  /** Accepted binding types */
  acceptedTypes: DataBinding['sourceType'][];
}

/**
 * Event handler definition
 */
export interface EventHandlerDefinition {
  /** Event name */
  name: string;

  /** Display label */
  label: string;

  /** Description */
  description?: string;

  /** Event payload type */
  payloadType?: string;
}

/**
 * Configuration schema for widget config panel
 */
export interface ConfigSchema {
  /** Schema properties */
  properties: Record<string, ConfigProperty>;

  /** Required properties */
  required?: string[];
}

export interface ConfigProperty {
  /** Property type */
  type: 'string' | 'number' | 'boolean' | 'array' | 'object' | 'enum';

  /** Display label */
  label: string;

  /** Description */
  description?: string;

  /** Default value */
  default?: unknown;

  /** Enum values (for type: 'enum') */
  enum?: unknown[];

  /** Enum labels (for type: 'enum') */
  enumLabels?: string[];

  /** Nested properties (for type: 'object') */
  properties?: Record<string, ConfigProperty>;

  /** Array item schema (for type: 'array') */
  items?: ConfigProperty;
}

// ============================================================================
// Runtime Types
// ============================================================================

/**
 * Runtime state for a published application
 */
export interface RuntimeState {
  /** Current page ID */
  currentPageId: StudioId;

  /** Page parameters */
  pageParams: Record<string, unknown>;

  /** Global state values */
  globalState: Record<string, unknown>;

  /** Page state values */
  pageState: Record<string, unknown>;

  /** Widget states */
  widgetStates: Record<StudioId, WidgetRuntimeState>;

  /** Loading states for data bindings */
  loadingStates: Record<StudioId, boolean>;

  /** Error states for data bindings */
  errorStates: Record<StudioId, Error | null>;

  /** Cached data for bindings */
  dataCache: Record<StudioId, unknown>;
}

/**
 * Runtime state for individual widgets
 */
export interface WidgetRuntimeState {
  /** Selected items (for tables, etc.) */
  selectedItems?: unknown[];

  /** Current filter values (for filter bar) */
  filterValues?: Record<string, unknown>;

  /** Form values */
  formValues?: Record<string, unknown>;

  /** Form validation errors */
  formErrors?: Record<string, string>;

  /** Custom widget state */
  custom?: Record<string, unknown>;
}

// ============================================================================
// Editor Types
// ============================================================================

/**
 * Editor state for design-time
 */
export interface EditorState {
  /** Currently edited app */
  app: StudioApp;

  /** Currently selected page */
  selectedPageId: StudioId | null;

  /** Currently selected widget */
  selectedWidgetId: StudioId | null;

  /** Currently active panel */
  activePanel: 'widgets' | 'config' | 'data' | 'actions' | 'code';

  /** Undo history */
  history: StudioApp[];

  /** Current position in history */
  historyIndex: number;

  /** Unsaved changes flag */
  isDirty: boolean;

  /** Preview mode */
  isPreviewMode: boolean;

  /** Zoom level */
  zoom: number;

  /** Canvas offset */
  canvasOffset: { x: number; y: number };
}

// ============================================================================
// API Types
// ============================================================================

/**
 * Request to create a new studio app
 */
export interface CreateAppRequest {
  name: string;
  description?: string;
  icon?: string;
}

/**
 * Request to update a studio app
 */
export interface UpdateAppRequest {
  id: StudioId;
  app: Partial<StudioApp>;
}

/**
 * Response for app list
 */
export interface AppListResponse {
  apps: StudioApp[];
  total: number;
  page: number;
  pageSize: number;
}

/**
 * Request to publish an app
 */
export interface PublishAppRequest {
  appId: StudioId;
  version?: string;
  releaseNotes?: string;
}

/**
 * Published app version
 */
export interface PublishedAppVersion {
  id: StudioId;
  appId: StudioId;
  version: string;
  app: StudioApp;
  publishedAt: string;
  publishedBy: string;
  releaseNotes?: string;
}
