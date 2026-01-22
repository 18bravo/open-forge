/**
 * Formatters
 *
 * Utility functions for formatting values in analytics components.
 */

// ============================================================================
// Number Formatting
// ============================================================================

export interface NumberFormatOptions {
  /** Number of decimal places */
  decimals?: number;

  /** Use thousands separator */
  thousandsSeparator?: boolean;

  /** Prefix string */
  prefix?: string;

  /** Suffix string */
  suffix?: string;

  /** Locale for formatting */
  locale?: string;
}

/**
 * Format a number with configurable options
 */
export function formatNumber(
  value: number | null | undefined,
  options: NumberFormatOptions = {}
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '-';
  }

  const {
    decimals = 0,
    thousandsSeparator = true,
    prefix = '',
    suffix = '',
    locale = 'en-US',
  } = options;

  const formatted = new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
    useGrouping: thousandsSeparator,
  }).format(value);

  return `${prefix}${formatted}${suffix}`;
}

// ============================================================================
// Currency Formatting
// ============================================================================

export interface CurrencyFormatOptions {
  /** Currency code (ISO 4217) */
  currency?: string;

  /** Number of decimal places */
  decimals?: number;

  /** Display style */
  display?: 'symbol' | 'code' | 'name' | 'narrowSymbol';

  /** Locale for formatting */
  locale?: string;
}

/**
 * Format a number as currency
 */
export function formatCurrency(
  value: number | null | undefined,
  options: CurrencyFormatOptions = {}
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '-';
  }

  const {
    currency = 'USD',
    decimals = 2,
    display = 'symbol',
    locale = 'en-US',
  } = options;

  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    currencyDisplay: display,
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

// ============================================================================
// Percentage Formatting
// ============================================================================

export interface PercentageFormatOptions {
  /** Number of decimal places */
  decimals?: number;

  /** Whether value is already a percentage (vs. decimal) */
  isPercentage?: boolean;

  /** Include sign for positive values */
  showSign?: boolean;

  /** Locale for formatting */
  locale?: string;
}

/**
 * Format a number as percentage
 */
export function formatPercentage(
  value: number | null | undefined,
  options: PercentageFormatOptions = {}
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '-';
  }

  const {
    decimals = 1,
    isPercentage = false,
    showSign = false,
    locale = 'en-US',
  } = options;

  // If value is already a percentage (e.g., 50 for 50%), convert to decimal
  const decimalValue = isPercentage ? value / 100 : value;

  const formatted = new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
    signDisplay: showSign ? 'exceptZero' : 'auto',
  }).format(decimalValue);

  return formatted;
}

// ============================================================================
// Date Formatting
// ============================================================================

export interface DateFormatOptions {
  /** Format style or custom format */
  format?: 'short' | 'medium' | 'long' | 'full' | string;

  /** Whether to include time */
  includeTime?: boolean;

  /** Locale for formatting */
  locale?: string;

  /** Timezone */
  timeZone?: string;
}

/**
 * Format a date string or Date object
 */
export function formatDate(
  value: string | Date | null | undefined,
  options: DateFormatOptions = {}
): string {
  if (!value) {
    return '-';
  }

  const date = typeof value === 'string' ? new Date(value) : value;

  if (isNaN(date.getTime())) {
    return '-';
  }

  const {
    format = 'medium',
    includeTime = false,
    locale = 'en-US',
    timeZone,
  } = options;

  const dateStyle = ['short', 'medium', 'long', 'full'].includes(format)
    ? (format as 'short' | 'medium' | 'long' | 'full')
    : 'medium';

  const formatOptions: Intl.DateTimeFormatOptions = {
    dateStyle,
    timeZone,
  };

  if (includeTime) {
    formatOptions.timeStyle = 'short';
  }

  return new Intl.DateTimeFormat(locale, formatOptions).format(date);
}

/**
 * Format a date as relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(
  value: string | Date | null | undefined,
  options: { locale?: string } = {}
): string {
  if (!value) {
    return '-';
  }

  const date = typeof value === 'string' ? new Date(value) : value;

  if (isNaN(date.getTime())) {
    return '-';
  }

  const { locale = 'en-US' } = options;

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffWeeks = Math.floor(diffDays / 7);
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffDays / 365);

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

  if (diffYears > 0) {
    return rtf.format(-diffYears, 'year');
  } else if (diffMonths > 0) {
    return rtf.format(-diffMonths, 'month');
  } else if (diffWeeks > 0) {
    return rtf.format(-diffWeeks, 'week');
  } else if (diffDays > 0) {
    return rtf.format(-diffDays, 'day');
  } else if (diffHours > 0) {
    return rtf.format(-diffHours, 'hour');
  } else if (diffMinutes > 0) {
    return rtf.format(-diffMinutes, 'minute');
  } else {
    return rtf.format(-diffSeconds, 'second');
  }
}

// ============================================================================
// Boolean Formatting
// ============================================================================

export interface BooleanFormatOptions {
  /** True label */
  trueLabel?: string;

  /** False label */
  falseLabel?: string;

  /** Null/undefined label */
  nullLabel?: string;
}

/**
 * Format a boolean value
 */
export function formatBoolean(
  value: boolean | null | undefined,
  options: BooleanFormatOptions = {}
): string {
  const {
    trueLabel = 'Yes',
    falseLabel = 'No',
    nullLabel = '-',
  } = options;

  if (value === null || value === undefined) {
    return nullLabel;
  }

  return value ? trueLabel : falseLabel;
}

// ============================================================================
// Compact Number Formatting
// ============================================================================

/**
 * Format a number in compact notation (e.g., 1.2K, 3.4M)
 */
export function formatCompactNumber(
  value: number | null | undefined,
  options: { locale?: string; decimals?: number } = {}
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '-';
  }

  const { locale = 'en-US', decimals = 1 } = options;

  return new Intl.NumberFormat(locale, {
    notation: 'compact',
    compactDisplay: 'short',
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(value);
}

// ============================================================================
// File Size Formatting
// ============================================================================

/**
 * Format a number of bytes as human-readable file size
 */
export function formatFileSize(
  bytes: number | null | undefined,
  options: { decimals?: number } = {}
): string {
  if (bytes === null || bytes === undefined || isNaN(bytes)) {
    return '-';
  }

  const { decimals = 1 } = options;

  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  let unitIndex = 0;
  let size = bytes;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(decimals)} ${units[unitIndex]}`;
}

// ============================================================================
// Text Truncation
// ============================================================================

/**
 * Truncate text to a maximum length with ellipsis
 */
export function truncateText(
  text: string | null | undefined,
  maxLength: number,
  options: { ellipsis?: string; wordBoundary?: boolean } = {}
): string {
  if (!text) {
    return '';
  }

  if (text.length <= maxLength) {
    return text;
  }

  const { ellipsis = '...', wordBoundary = true } = options;

  let truncated = text.slice(0, maxLength - ellipsis.length);

  if (wordBoundary) {
    const lastSpace = truncated.lastIndexOf(' ');
    if (lastSpace > maxLength * 0.5) {
      truncated = truncated.slice(0, lastSpace);
    }
  }

  return truncated + ellipsis;
}
