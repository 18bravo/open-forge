/**
 * Lens Module
 *
 * Object-driven analysis components for exploring individual objects,
 * their relationships, and history.
 */

// ============================================================================
// Components
// ============================================================================

export {
  ObjectView,
  ObjectViewFieldRenderer,
  ObjectViewSection,
  RelatedObjectsList,
  type ObjectViewProps,
  type ObjectViewFieldRendererProps,
  type ObjectViewSectionProps,
  type RelatedObjectsListProps,
} from './ObjectView';

export {
  RelationshipGraph,
  GraphNodeComponent,
  GraphEdgeComponent,
  GraphControls,
  GraphLegend,
  GraphTooltip,
  type RelationshipGraphProps,
  type GraphNodeComponentProps,
  type GraphEdgeComponentProps,
  type GraphControlsProps,
  type GraphLegendProps,
  type GraphTooltipProps,
  type LayoutAlgorithm,
  type LayoutOptions,
} from './RelationshipGraph';

export {
  TimelineView,
  TimelineEventCard,
  TimelineGroup,
  TimelineDateFilter,
  TimelineEventTypeFilter,
  PropertyChangeDisplay,
  defaultEventTypeConfigs,
  type TimelineViewProps,
  type TimelineEventCardProps,
  type TimelineGroupProps,
  type TimelineDateFilterProps,
  type TimelineEventTypeFilterProps,
  type PropertyChangeDisplayProps,
  type TimelineEventTypeConfig,
} from './TimelineView';
