/**
 * Filters
 *
 * Utility functions for working with filter conditions.
 */

import type {
  FilterCondition,
  FilterOperator,
  ActiveFilter,
} from '../../types';

// ============================================================================
// Filter Building
// ============================================================================

/**
 * Create a filter condition
 */
export function createFilter(
  property: string,
  operator: FilterOperator,
  value: unknown
): FilterCondition {
  return { property, operator, value };
}

/**
 * Create an equals filter
 */
export function equals(property: string, value: unknown): FilterCondition {
  return createFilter(property, 'equals', value);
}

/**
 * Create a not equals filter
 */
export function notEquals(property: string, value: unknown): FilterCondition {
  return createFilter(property, 'notEquals', value);
}

/**
 * Create a contains filter (for strings)
 */
export function contains(property: string, value: string): FilterCondition {
  return createFilter(property, 'contains', value);
}

/**
 * Create a starts with filter
 */
export function startsWith(property: string, value: string): FilterCondition {
  return createFilter(property, 'startsWith', value);
}

/**
 * Create an ends with filter
 */
export function endsWith(property: string, value: string): FilterCondition {
  return createFilter(property, 'endsWith', value);
}

/**
 * Create a greater than filter
 */
export function greaterThan(property: string, value: number | string): FilterCondition {
  return createFilter(property, 'greaterThan', value);
}

/**
 * Create a less than filter
 */
export function lessThan(property: string, value: number | string): FilterCondition {
  return createFilter(property, 'lessThan', value);
}

/**
 * Create a between filter
 */
export function between(property: string, min: number | string, max: number | string): FilterCondition {
  return createFilter(property, 'between', [min, max]);
}

/**
 * Create an in filter (value is in list)
 */
export function isIn(property: string, values: unknown[]): FilterCondition {
  return createFilter(property, 'in', values);
}

/**
 * Create a not in filter
 */
export function notIn(property: string, values: unknown[]): FilterCondition {
  return createFilter(property, 'notIn', values);
}

/**
 * Create an is null filter
 */
export function isNull(property: string): FilterCondition {
  return createFilter(property, 'isNull', null);
}

/**
 * Create an is not null filter
 */
export function isNotNull(property: string): FilterCondition {
  return createFilter(property, 'isNotNull', null);
}

// ============================================================================
// Filter Manipulation
// ============================================================================

/**
 * Add or update a filter in a list
 */
export function setFilter(
  filters: FilterCondition[],
  filter: FilterCondition
): FilterCondition[] {
  const index = filters.findIndex(f => f.property === filter.property);
  if (index >= 0) {
    const updated = [...filters];
    updated[index] = filter;
    return updated;
  }
  return [...filters, filter];
}

/**
 * Remove a filter by property
 */
export function removeFilter(
  filters: FilterCondition[],
  property: string
): FilterCondition[] {
  return filters.filter(f => f.property !== property);
}

/**
 * Remove filters by properties
 */
export function removeFilters(
  filters: FilterCondition[],
  properties: string[]
): FilterCondition[] {
  const propSet = new Set(properties);
  return filters.filter(f => !propSet.has(f.property));
}

/**
 * Clear all filters
 */
export function clearFilters(): FilterCondition[] {
  return [];
}

/**
 * Check if a filter exists for a property
 */
export function hasFilter(filters: FilterCondition[], property: string): boolean {
  return filters.some(f => f.property === property);
}

/**
 * Get filter by property
 */
export function getFilter(
  filters: FilterCondition[],
  property: string
): FilterCondition | undefined {
  return filters.find(f => f.property === property);
}

// ============================================================================
// Filter Validation
// ============================================================================

/**
 * Check if a filter has a valid value
 */
export function isValidFilter(filter: FilterCondition): boolean {
  const { operator, value } = filter;

  // Null checks don't need values
  if (operator === 'isNull' || operator === 'isNotNull') {
    return true;
  }

  // Empty values are invalid
  if (value === null || value === undefined) {
    return false;
  }

  // Empty strings are invalid (except for equals which might intentionally match empty)
  if (typeof value === 'string' && value.trim() === '' && operator !== 'equals') {
    return false;
  }

  // Arrays should have at least one element
  if (Array.isArray(value) && value.length === 0) {
    return false;
  }

  // Between should have exactly 2 values
  if (operator === 'between') {
    return Array.isArray(value) && value.length === 2;
  }

  return true;
}

/**
 * Filter out invalid filters
 */
export function removeInvalidFilters(filters: FilterCondition[]): FilterCondition[] {
  return filters.filter(isValidFilter);
}

// ============================================================================
// Active Filter Conversion
// ============================================================================

/**
 * Convert ActiveFilter to FilterCondition
 */
export function activeFilterToCondition(activeFilter: ActiveFilter): FilterCondition {
  return {
    property: activeFilter.property,
    operator: activeFilter.operator,
    value: activeFilter.value,
  };
}

/**
 * Convert FilterCondition to ActiveFilter
 */
export function conditionToActiveFilter(
  filterId: string,
  condition: FilterCondition
): ActiveFilter {
  return {
    filterId,
    property: condition.property,
    operator: condition.operator,
    value: condition.value,
  };
}

/**
 * Convert active filters to filter conditions
 */
export function activeFiltersToConditions(activeFilters: ActiveFilter[]): FilterCondition[] {
  return activeFilters.map(activeFilterToCondition);
}

// ============================================================================
// Filter Serialization
// ============================================================================

/**
 * Serialize filters to URL query string
 */
export function serializeFilters(filters: FilterCondition[]): string {
  const validFilters = removeInvalidFilters(filters);
  if (validFilters.length === 0) {
    return '';
  }

  return encodeURIComponent(JSON.stringify(validFilters));
}

/**
 * Deserialize filters from URL query string
 */
export function deserializeFilters(queryString: string): FilterCondition[] {
  if (!queryString) {
    return [];
  }

  try {
    const decoded = decodeURIComponent(queryString);
    const parsed = JSON.parse(decoded);

    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter(
      (f): f is FilterCondition =>
        typeof f === 'object' &&
        typeof f.property === 'string' &&
        typeof f.operator === 'string'
    );
  } catch {
    return [];
  }
}
