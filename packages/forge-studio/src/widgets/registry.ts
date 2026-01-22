/**
 * Widget Registry
 *
 * Central registry for all widget types in Forge Studio.
 * Provides widget definitions, components, and metadata.
 */

import React from 'react';
import type {
  WidgetType,
  WidgetDefinition,
  WidgetInstance,
  BaseWidgetConfig,
  WidgetCategory,
} from '../types';

// ============================================================================
// Registry Types
// ============================================================================

/**
 * Widget component props (runtime)
 */
export interface WidgetComponentProps<T extends BaseWidgetConfig = BaseWidgetConfig> {
  /** Widget instance */
  widget: WidgetInstance<T>;

  /** Resolved data from bindings */
  data: Record<string, unknown>;

  /** Callback to update widget state */
  onStateChange?: (state: Record<string, unknown>) => void;

  /** Callback to trigger an action */
  onAction?: (eventName: string, payload?: unknown) => void;

  /** Loading state */
  isLoading?: boolean;

  /** Error state */
  error?: Error | null;

  /** Preview mode (design-time) */
  isPreview?: boolean;
}

/**
 * Widget component type
 */
export type WidgetComponent<T extends BaseWidgetConfig = BaseWidgetConfig> = React.FC<
  WidgetComponentProps<T>
>;

/**
 * Registry entry for a widget type
 */
export interface WidgetRegistryEntry<T extends BaseWidgetConfig = BaseWidgetConfig> {
  /** Widget definition (metadata) */
  definition: WidgetDefinition<T>;

  /** Widget component */
  component: WidgetComponent<T>;

  /** Preview component (for widget panel) */
  previewComponent?: React.FC;

  /** Icon component */
  iconComponent?: React.FC<{ size?: number; className?: string }>;
}

// ============================================================================
// Registry Implementation
// ============================================================================

/**
 * Widget registry class
 */
class WidgetRegistryImpl {
  private entries: Map<WidgetType, WidgetRegistryEntry> = new Map();

  /**
   * Register a widget type
   */
  register<T extends BaseWidgetConfig>(entry: WidgetRegistryEntry<T>): void {
    this.entries.set(entry.definition.type, entry as WidgetRegistryEntry);
  }

  /**
   * Unregister a widget type
   */
  unregister(type: WidgetType): void {
    this.entries.delete(type);
  }

  /**
   * Get a widget entry by type
   */
  get<T extends BaseWidgetConfig>(type: WidgetType): WidgetRegistryEntry<T> | undefined {
    return this.entries.get(type) as WidgetRegistryEntry<T> | undefined;
  }

  /**
   * Get widget definition by type
   */
  getDefinition<T extends BaseWidgetConfig>(type: WidgetType): WidgetDefinition<T> | undefined {
    return this.entries.get(type)?.definition as WidgetDefinition<T> | undefined;
  }

  /**
   * Get widget component by type
   */
  getComponent<T extends BaseWidgetConfig>(type: WidgetType): WidgetComponent<T> | undefined {
    return this.entries.get(type)?.component as WidgetComponent<T> | undefined;
  }

  /**
   * Get all registered widget types
   */
  getTypes(): WidgetType[] {
    return Array.from(this.entries.keys());
  }

  /**
   * Get all widget definitions
   */
  getDefinitions(): WidgetDefinition[] {
    return Array.from(this.entries.values()).map((entry) => entry.definition);
  }

  /**
   * Get widget definitions by category
   */
  getDefinitionsByCategory(category: WidgetCategory): WidgetDefinition[] {
    return this.getDefinitions().filter((def) => def.category === category);
  }

  /**
   * Check if a widget type is registered
   */
  has(type: WidgetType): boolean {
    return this.entries.has(type);
  }

  /**
   * Clear all registrations
   */
  clear(): void {
    this.entries.clear();
  }
}

/**
 * Singleton widget registry instance
 */
export const widgetRegistry = new WidgetRegistryImpl();

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Create a widget definition
 */
export function defineWidget<T extends BaseWidgetConfig>(
  definition: WidgetDefinition<T>
): WidgetDefinition<T> {
  return definition;
}

/**
 * Create a widget instance with defaults
 */
export function createWidgetInstance<T extends BaseWidgetConfig>(
  type: WidgetType,
  overrides?: Partial<WidgetInstance<T>>
): WidgetInstance<T> {
  const definition = widgetRegistry.getDefinition<T>(type);

  if (!definition) {
    throw new Error(`Unknown widget type: ${type}`);
  }

  return {
    id: crypto.randomUUID(),
    type,
    config: { ...definition.defaultConfig },
    bindings: {},
    actions: {},
    layout: {
      x: 0,
      y: 0,
      width: definition.defaultLayout.width ?? 4,
      height: definition.defaultLayout.height ?? 2,
      ...definition.defaultLayout,
    },
    ...overrides,
  } as WidgetInstance<T>;
}

/**
 * Validate a widget instance against its definition
 */
export function validateWidgetInstance(widget: WidgetInstance): string[] {
  const errors: string[] = [];
  const definition = widgetRegistry.getDefinition(widget.type);

  if (!definition) {
    errors.push(`Unknown widget type: ${widget.type}`);
    return errors;
  }

  // Check required bindings
  for (const slot of definition.bindingSlots) {
    if (slot.required && !widget.bindings[slot.name]) {
      errors.push(`Missing required binding: ${slot.label}`);
    }
  }

  // Check required config properties
  if (definition.configSchema.required) {
    for (const prop of definition.configSchema.required) {
      if (widget.config[prop as keyof typeof widget.config] === undefined) {
        errors.push(`Missing required config: ${prop}`);
      }
    }
  }

  return errors;
}

// ============================================================================
// Category Metadata
// ============================================================================

export const widgetCategories: Record<WidgetCategory, { label: string; icon: string }> = {
  data: {
    label: 'Data Display',
    icon: 'table',
  },
  input: {
    label: 'Input & Forms',
    icon: 'text-cursor-input',
  },
  visualization: {
    label: 'Visualization',
    icon: 'chart-bar',
  },
  layout: {
    label: 'Layout',
    icon: 'layout',
  },
  action: {
    label: 'Actions',
    icon: 'play',
  },
};

export default widgetRegistry;
