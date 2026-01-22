/**
 * Forge Analytics
 *
 * Unified analytics tools for object and tabular analysis.
 *
 * Modules:
 * - **Lens**: Object-driven analysis (ObjectView, RelationshipGraph, TimelineView)
 * - **Prism**: Large-scale tabular analysis (DataGrid, Pivot, Aggregations)
 * - **Browser**: Object explorer (Search, ObjectList, Filters)
 * - **Shared**: Common hooks and utilities
 *
 * @packageDocumentation
 */

// ============================================================================
// Types
// ============================================================================

export * from './types';

// ============================================================================
// Lens Module (Object-Driven Analysis)
// ============================================================================

export * from './lens';

// ============================================================================
// Prism Module (Tabular Analysis)
// ============================================================================

export * from './prism';

// ============================================================================
// Browser Module (Object Explorer)
// ============================================================================

export * from './browser';

// ============================================================================
// Shared Module (Hooks & Utilities)
// ============================================================================

export * from './shared';

// ============================================================================
// Version
// ============================================================================

export const VERSION = '0.1.0';
