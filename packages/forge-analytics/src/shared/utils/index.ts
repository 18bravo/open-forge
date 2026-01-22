/**
 * Shared Utilities
 *
 * Utility functions for formatting, filtering, and sorting.
 */

export {
  formatNumber,
  formatCurrency,
  formatPercentage,
  formatDate,
  formatRelativeTime,
  formatBoolean,
  formatCompactNumber,
  formatFileSize,
  truncateText,
  type NumberFormatOptions,
  type CurrencyFormatOptions,
  type PercentageFormatOptions,
  type DateFormatOptions,
  type BooleanFormatOptions,
} from './formatters';

export {
  // Filter builders
  createFilter,
  equals,
  notEquals,
  contains,
  startsWith,
  endsWith,
  greaterThan,
  lessThan,
  between,
  isIn,
  notIn,
  isNull,
  isNotNull,
  // Filter manipulation
  setFilter,
  removeFilter,
  removeFilters,
  clearFilters,
  hasFilter,
  getFilter,
  // Filter validation
  isValidFilter,
  removeInvalidFilters,
  // Active filter conversion
  activeFilterToCondition,
  conditionToActiveFilter,
  activeFiltersToConditions,
  // Filter serialization
  serializeFilters,
  deserializeFilters,
} from './filters';

export {
  // Sort builders
  createSort,
  asc,
  desc,
  // Sort manipulation
  toggleSort,
  setSort,
  removeSort,
  clearSorts,
  isSorted,
  getSortDirection,
  getSortIndex,
  reorderSort,
  // Sort serialization
  serializeSorts,
  deserializeSorts,
  // Local sorting
  compareValues,
  sortObjects,
} from './sorting';
