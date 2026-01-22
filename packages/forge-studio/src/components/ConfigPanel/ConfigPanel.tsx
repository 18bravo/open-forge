/**
 * ConfigPanel Component
 *
 * Configuration panel for editing widget properties, data bindings, and actions.
 * Dynamically renders form fields based on widget configuration schema.
 */

import React from 'react';
import type {
  WidgetInstance,
  WidgetDefinition,
  ConfigSchema,
  ConfigProperty,
  DataBinding,
  StudioAction,
} from '../../types';

// ============================================================================
// Props Interfaces
// ============================================================================

export interface ConfigPanelProps {
  /** Currently selected widget */
  widget?: WidgetInstance | null;

  /** Widget definition for the selected widget */
  widgetDefinition?: WidgetDefinition | null;

  /** Callback when widget config changes */
  onConfigChange?: (config: Record<string, unknown>) => void;

  /** Callback when bindings change */
  onBindingsChange?: (bindings: Record<string, DataBinding>) => void;

  /** Callback when actions change */
  onActionsChange?: (actions: Record<string, StudioAction[]>) => void;

  /** Available object types for binding */
  availableObjectTypes?: Array<{ id: string; name: string }>;

  /** Custom class name */
  className?: string;

  /** Active tab */
  activeTab?: ConfigPanelTab;

  /** Callback when active tab changes */
  onActiveTabChange?: (tab: ConfigPanelTab) => void;
}

export type ConfigPanelTab = 'properties' | 'data' | 'actions' | 'style';

export interface PropertyEditorProps {
  /** Property schema */
  schema: ConfigProperty;

  /** Property name/key */
  name: string;

  /** Current value */
  value: unknown;

  /** Callback when value changes */
  onChange: (value: unknown) => void;

  /** Path for nested properties */
  path?: string[];
}

export interface BindingEditorProps {
  /** Binding slot name */
  slotName: string;

  /** Binding slot label */
  slotLabel: string;

  /** Current binding */
  binding?: DataBinding;

  /** Callback when binding changes */
  onChange: (binding: DataBinding | undefined) => void;

  /** Available object types */
  availableObjectTypes?: Array<{ id: string; name: string }>;

  /** Required flag */
  required?: boolean;
}

export interface ActionEditorProps {
  /** Event name */
  eventName: string;

  /** Event label */
  eventLabel: string;

  /** Current actions */
  actions: StudioAction[];

  /** Callback when actions change */
  onChange: (actions: StudioAction[]) => void;
}

// ============================================================================
// Sub-components
// ============================================================================

/**
 * Renders a property editor based on schema type
 */
export const PropertyEditor: React.FC<PropertyEditorProps> = ({
  schema: _schema,
  name: _name,
  value: _value,
  onChange: _onChange,
  path: _path = [],
}) => {
  // TODO: Implement type-specific editors:
  // - string: text input
  // - number: number input with min/max
  // - boolean: checkbox/switch
  // - enum: select dropdown
  // - array: list editor
  // - object: nested form

  return (
    <div data-testid="property-editor">
      {/* TODO: Implement property editor */}
    </div>
  );
};

/**
 * Renders a data binding editor
 */
export const BindingEditor: React.FC<BindingEditorProps> = ({
  slotName: _slotName,
  slotLabel: _slotLabel,
  binding: _binding,
  onChange: _onChange,
  availableObjectTypes: _availableObjectTypes,
  required: _required = false,
}) => {
  // TODO: Implement binding editor:
  // - Source type selector
  // - Object type selector
  // - Property selector
  // - Filter builder
  // - Expression editor

  return (
    <div data-testid="binding-editor">
      {/* TODO: Implement binding editor */}
    </div>
  );
};

/**
 * Renders an action editor
 */
export const ActionEditor: React.FC<ActionEditorProps> = ({
  eventName: _eventName,
  eventLabel: _eventLabel,
  actions: _actions,
  onChange: _onChange,
}) => {
  // TODO: Implement action editor:
  // - Action list
  // - Add action button
  // - Action type selector
  // - Action config editor
  // - Condition builder

  return (
    <div data-testid="action-editor">
      {/* TODO: Implement action editor */}
    </div>
  );
};

/**
 * Schema-driven form generator
 */
export const SchemaForm: React.FC<{
  schema: ConfigSchema;
  values: Record<string, unknown>;
  onChange: (values: Record<string, unknown>) => void;
}> = ({ schema: _schema, values: _values, onChange: _onChange }) => {
  // TODO: Implement schema-driven form rendering

  return (
    <div data-testid="schema-form">
      {/* TODO: Implement schema form */}
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

/**
 * Configuration panel for editing widget settings
 *
 * @example
 * ```tsx
 * <ConfigPanel
 *   widget={selectedWidget}
 *   widgetDefinition={getWidgetDefinition(selectedWidget.type)}
 *   onConfigChange={handleConfigChange}
 *   onBindingsChange={handleBindingsChange}
 *   onActionsChange={handleActionsChange}
 * />
 * ```
 */
export const ConfigPanel: React.FC<ConfigPanelProps> = ({
  widget: _widget,
  widgetDefinition: _widgetDefinition,
  onConfigChange: _onConfigChange,
  onBindingsChange: _onBindingsChange,
  onActionsChange: _onActionsChange,
  availableObjectTypes: _availableObjectTypes,
  className: _className,
  activeTab: _activeTab = 'properties',
  onActiveTabChange: _onActiveTabChange,
}) => {
  // TODO: Implement tab navigation
  // TODO: Implement properties tab (schema form)
  // TODO: Implement data tab (binding editors)
  // TODO: Implement actions tab (action editors)
  // TODO: Implement style tab (CSS overrides)

  return (
    <div data-testid="forge-studio-config-panel">
      {/* TODO: Implement panel layout */}
      {/* - Tab navigation */}
      {/* - Properties tab */}
      {/* - Data tab */}
      {/* - Actions tab */}
      {/* - Style tab */}
    </div>
  );
};

ConfigPanel.displayName = 'ConfigPanel';

export default ConfigPanel;
