/**
 * Sorting
 *
 * Utility functions for working with sort configurations.
 */

import type { SortConfig, PropertyRef } from '../../types';

// ============================================================================
// Sort Building
// ============================================================================

/**
 * Create a sort configuration
 */
export function createSort(property: PropertyRef, direction: 'asc' | 'desc' = 'asc'): SortConfig {
  return { property, direction };
}

/**
 * Create an ascending sort
 */
export function asc(property: PropertyRef): SortConfig {
  return createSort(property, 'asc');
}

/**
 * Create a descending sort
 */
export function desc(property: PropertyRef): SortConfig {
  return createSort(property, 'desc');
}

// ============================================================================
// Sort Manipulation
// ============================================================================

/**
 * Toggle sort direction for a property
 * If property is not sorted, add ascending sort
 * If ascending, change to descending
 * If descending, remove sort
 */
export function toggleSort(
  sorts: SortConfig[],
  property: PropertyRef,
  options: { multiSort?: boolean } = {}
): SortConfig[] {
  const { multiSort = false } = options;

  const existingIndex = sorts.findIndex(s => s.property === property);

  if (existingIndex === -1) {
    // Not currently sorted - add ascending
    const newSort = asc(property);
    return multiSort ? [...sorts, newSort] : [newSort];
  }

  const existing = sorts[existingIndex]!;

  if (existing.direction === 'asc') {
    // Currently ascending - change to descending
    const updated = [...sorts];
    updated[existingIndex] = desc(property);
    return updated;
  }

  // Currently descending - remove sort
  if (multiSort) {
    return sorts.filter((_, i) => i !== existingIndex);
  }
  return [];
}

/**
 * Set sort for a property (replaces existing sorts unless multiSort)
 */
export function setSort(
  sorts: SortConfig[],
  property: PropertyRef,
  direction: 'asc' | 'desc',
  options: { multiSort?: boolean } = {}
): SortConfig[] {
  const { multiSort = false } = options;

  const newSort = createSort(property, direction);

  if (!multiSort) {
    return [newSort];
  }

  const existingIndex = sorts.findIndex(s => s.property === property);
  if (existingIndex >= 0) {
    const updated = [...sorts];
    updated[existingIndex] = newSort;
    return updated;
  }

  return [...sorts, newSort];
}

/**
 * Remove sort for a property
 */
export function removeSort(sorts: SortConfig[], property: PropertyRef): SortConfig[] {
  return sorts.filter(s => s.property !== property);
}

/**
 * Clear all sorts
 */
export function clearSorts(): SortConfig[] {
  return [];
}

/**
 * Check if a property is sorted
 */
export function isSorted(sorts: SortConfig[], property: PropertyRef): boolean {
  return sorts.some(s => s.property === property);
}

/**
 * Get sort direction for a property
 */
export function getSortDirection(
  sorts: SortConfig[],
  property: PropertyRef
): 'asc' | 'desc' | undefined {
  const sort = sorts.find(s => s.property === property);
  return sort?.direction;
}

/**
 * Get sort index for a property (for multi-sort)
 */
export function getSortIndex(sorts: SortConfig[], property: PropertyRef): number {
  return sorts.findIndex(s => s.property === property);
}

// ============================================================================
// Sort Reordering
// ============================================================================

/**
 * Move a sort to a new position in the multi-sort order
 */
export function reorderSort(
  sorts: SortConfig[],
  fromIndex: number,
  toIndex: number
): SortConfig[] {
  if (fromIndex === toIndex) {
    return sorts;
  }

  if (fromIndex < 0 || fromIndex >= sorts.length) {
    return sorts;
  }

  if (toIndex < 0 || toIndex >= sorts.length) {
    return sorts;
  }

  const result = [...sorts];
  const [removed] = result.splice(fromIndex, 1);
  result.splice(toIndex, 0, removed!);
  return result;
}

// ============================================================================
// Sort Serialization
// ============================================================================

/**
 * Serialize sorts to URL query string
 */
export function serializeSorts(sorts: SortConfig[]): string {
  if (sorts.length === 0) {
    return '';
  }

  return sorts
    .map(s => `${s.direction === 'desc' ? '-' : ''}${s.property}`)
    .join(',');
}

/**
 * Deserialize sorts from URL query string
 */
export function deserializeSorts(queryString: string): SortConfig[] {
  if (!queryString) {
    return [];
  }

  return queryString.split(',').map(part => {
    const trimmed = part.trim();
    if (trimmed.startsWith('-')) {
      return desc(trimmed.slice(1));
    }
    return asc(trimmed);
  });
}

// ============================================================================
// Local Sorting (for client-side sorting)
// ============================================================================

/**
 * Compare two values for sorting
 */
export function compareValues(
  a: unknown,
  b: unknown,
  direction: 'asc' | 'desc' = 'asc'
): number {
  const multiplier = direction === 'desc' ? -1 : 1;

  // Handle null/undefined
  if (a === null || a === undefined) {
    return b === null || b === undefined ? 0 : 1 * multiplier;
  }
  if (b === null || b === undefined) {
    return -1 * multiplier;
  }

  // Numbers
  if (typeof a === 'number' && typeof b === 'number') {
    return (a - b) * multiplier;
  }

  // Dates (as strings)
  if (
    typeof a === 'string' &&
    typeof b === 'string' &&
    !isNaN(Date.parse(a)) &&
    !isNaN(Date.parse(b))
  ) {
    return (new Date(a).getTime() - new Date(b).getTime()) * multiplier;
  }

  // Booleans
  if (typeof a === 'boolean' && typeof b === 'boolean') {
    return (Number(a) - Number(b)) * multiplier;
  }

  // Strings (default)
  const strA = String(a).toLowerCase();
  const strB = String(b).toLowerCase();
  return strA.localeCompare(strB) * multiplier;
}

/**
 * Sort an array of objects by multiple sort configurations
 */
export function sortObjects<T extends Record<string, unknown>>(
  objects: T[],
  sorts: SortConfig[]
): T[] {
  if (sorts.length === 0) {
    return objects;
  }

  return [...objects].sort((a, b) => {
    for (const sort of sorts) {
      const result = compareValues(a[sort.property], b[sort.property], sort.direction);
      if (result !== 0) {
        return result;
      }
    }
    return 0;
  });
}
