/**
 * Forge Studio Widgets
 *
 * All available widget components and their definitions.
 */

// Widget Registry
export {
  widgetRegistry,
  widgetCategories,
  defineWidget,
  createWidgetInstance,
  validateWidgetInstance,
} from './registry';
export type {
  WidgetComponentProps,
  WidgetComponent,
  WidgetRegistryEntry,
} from './registry';

// Individual Widgets
export { ObjectTable, objectTableDefinition } from './ObjectTable';
export type { ObjectTableProps } from './ObjectTable';

export { ObjectDetail, objectDetailDefinition } from './ObjectDetail';
export type { ObjectDetailProps } from './ObjectDetail';

export { Form, formDefinition } from './Form';
export type { FormProps } from './Form';

export { Chart, chartDefinition } from './Chart';
export type { ChartProps } from './Chart';

export { MetricCard, metricCardDefinition } from './MetricCard';
export type { MetricCardProps } from './MetricCard';

export { Text, textDefinition } from './Text';
export type { TextProps } from './Text';

export { FilterBar, filterBarDefinition } from './FilterBar';
export type { FilterBarProps } from './FilterBar';

export { ActionButton, actionButtonDefinition } from './ActionButton';
export type { ActionButtonProps } from './ActionButton';

// ============================================================================
// Widget Registration
// ============================================================================

import { widgetRegistry } from './registry';
import { ObjectTable, objectTableDefinition } from './ObjectTable';
import { ObjectDetail, objectDetailDefinition } from './ObjectDetail';
import { Form, formDefinition } from './Form';
import { Chart, chartDefinition } from './Chart';
import { MetricCard, metricCardDefinition } from './MetricCard';
import { Text, textDefinition } from './Text';
import { FilterBar, filterBarDefinition } from './FilterBar';
import { ActionButton, actionButtonDefinition } from './ActionButton';

/**
 * Register all built-in widgets with the registry
 */
export function registerBuiltInWidgets(): void {
  widgetRegistry.register({
    definition: objectTableDefinition,
    component: ObjectTable,
  });

  widgetRegistry.register({
    definition: objectDetailDefinition,
    component: ObjectDetail,
  });

  widgetRegistry.register({
    definition: formDefinition,
    component: Form,
  });

  widgetRegistry.register({
    definition: chartDefinition,
    component: Chart,
  });

  widgetRegistry.register({
    definition: metricCardDefinition,
    component: MetricCard,
  });

  widgetRegistry.register({
    definition: textDefinition,
    component: Text,
  });

  widgetRegistry.register({
    definition: filterBarDefinition,
    component: FilterBar,
  });

  widgetRegistry.register({
    definition: actionButtonDefinition,
    component: ActionButton,
  });
}

// Auto-register widgets on import
registerBuiltInWidgets();
