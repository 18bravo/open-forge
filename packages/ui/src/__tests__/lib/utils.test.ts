/**
 * Tests for utility functions
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  cn,
  formatDate,
  formatDateTime,
  formatRelativeTime,
  truncate,
  getInitials,
  capitalize,
  formatCompactNumber,
  formatCurrency,
  generateId,
  debounce,
  throttle,
  isClient,
  isServer,
  sleep,
  toKebabCase,
  toCamelCase,
} from '@/lib/utils'

describe('cn', () => {
  it('combines class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('handles conditional classes', () => {
    expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz')
  })

  it('merges tailwind classes correctly', () => {
    expect(cn('px-2', 'px-4')).toBe('px-4')
  })

  it('handles arrays of classes', () => {
    expect(cn(['foo', 'bar'])).toBe('foo bar')
  })

  it('handles objects of classes', () => {
    expect(cn({ foo: true, bar: false })).toBe('foo')
  })

  it('handles undefined and null', () => {
    expect(cn('foo', undefined, null, 'bar')).toBe('foo bar')
  })
})

describe('formatDate', () => {
  it('formats Date object', () => {
    const date = new Date('2026-01-15T10:00:00Z')
    const result = formatDate(date)
    expect(result).toMatch(/Jan 15, 2026/)
  })

  it('formats date string', () => {
    const result = formatDate('2026-01-15T10:00:00Z')
    expect(result).toMatch(/Jan 15, 2026/)
  })
})

describe('formatDateTime', () => {
  it('formats Date object with time', () => {
    const date = new Date('2026-01-15T10:30:00Z')
    const result = formatDateTime(date)
    expect(result).toMatch(/Jan 15, 2026/)
    expect(result).toMatch(/\d{1,2}:\d{2}/)
  })

  it('formats date string with time', () => {
    const result = formatDateTime('2026-01-15T10:30:00Z')
    expect(result).toMatch(/Jan 15, 2026/)
  })
})

describe('formatRelativeTime', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-19T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns "just now" for recent times', () => {
    const date = new Date('2026-01-19T11:59:45Z')
    expect(formatRelativeTime(date)).toBe('just now')
  })

  it('returns minutes ago', () => {
    const date = new Date('2026-01-19T11:30:00Z')
    expect(formatRelativeTime(date)).toBe('30m ago')
  })

  it('returns hours ago', () => {
    const date = new Date('2026-01-19T09:00:00Z')
    expect(formatRelativeTime(date)).toBe('3h ago')
  })

  it('returns days ago', () => {
    const date = new Date('2026-01-17T12:00:00Z')
    expect(formatRelativeTime(date)).toBe('2d ago')
  })

  it('returns formatted date for older times', () => {
    const date = new Date('2026-01-01T12:00:00Z')
    const result = formatRelativeTime(date)
    expect(result).toMatch(/Jan 1, 2026/)
  })
})

describe('truncate', () => {
  it('does not truncate short strings', () => {
    expect(truncate('hello', 10)).toBe('hello')
  })

  it('truncates long strings with ellipsis', () => {
    expect(truncate('hello world', 8)).toBe('hello...')
  })

  it('handles exact length', () => {
    expect(truncate('hello', 5)).toBe('hello')
  })

  it('handles empty string', () => {
    expect(truncate('', 10)).toBe('')
  })
})

describe('getInitials', () => {
  it('returns initials from full name', () => {
    expect(getInitials('John Doe')).toBe('JD')
  })

  it('returns single initial for single name', () => {
    expect(getInitials('John')).toBe('J')
  })

  it('returns first two initials for long names', () => {
    expect(getInitials('John Michael Doe')).toBe('JM')
  })

  it('returns uppercase initials', () => {
    expect(getInitials('john doe')).toBe('JD')
  })
})

describe('capitalize', () => {
  it('capitalizes first letter', () => {
    expect(capitalize('hello')).toBe('Hello')
  })

  it('lowercases rest of string', () => {
    expect(capitalize('hELLO')).toBe('Hello')
  })

  it('handles single character', () => {
    expect(capitalize('h')).toBe('H')
  })

  it('handles empty string', () => {
    expect(capitalize('')).toBe('')
  })
})

describe('formatCompactNumber', () => {
  it('formats thousands', () => {
    expect(formatCompactNumber(1500)).toMatch(/1\.?5?K/)
  })

  it('formats millions', () => {
    expect(formatCompactNumber(1500000)).toMatch(/1\.?5?M/)
  })

  it('formats small numbers normally', () => {
    expect(formatCompactNumber(999)).toBe('999')
  })

  it('formats billions', () => {
    expect(formatCompactNumber(1500000000)).toMatch(/1\.?5?B/)
  })
})

describe('formatCurrency', () => {
  it('formats USD by default', () => {
    const result = formatCurrency(1234.56)
    expect(result).toMatch(/\$1,234\.56/)
  })

  it('formats with specified currency', () => {
    const result = formatCurrency(1234.56, 'EUR')
    expect(result).toContain('1,234.56')
  })

  it('handles whole numbers', () => {
    const result = formatCurrency(1000)
    expect(result).toMatch(/\$1,000\.00/)
  })

  it('handles zero', () => {
    const result = formatCurrency(0)
    expect(result).toMatch(/\$0\.00/)
  })
})

describe('generateId', () => {
  it('generates string of specified length', () => {
    const id = generateId(8)
    expect(id.length).toBe(8)
  })

  it('generates unique ids', () => {
    const ids = new Set()
    for (let i = 0; i < 100; i++) {
      ids.add(generateId())
    }
    expect(ids.size).toBe(100)
  })

  it('uses default length when not specified', () => {
    const id = generateId()
    expect(id.length).toBe(8)
  })
})

describe('debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('delays function execution', () => {
    const fn = vi.fn()
    const debouncedFn = debounce(fn, 100)

    debouncedFn()
    expect(fn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(100)
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('cancels previous calls', () => {
    const fn = vi.fn()
    const debouncedFn = debounce(fn, 100)

    debouncedFn()
    vi.advanceTimersByTime(50)
    debouncedFn()
    vi.advanceTimersByTime(50)
    debouncedFn()
    vi.advanceTimersByTime(100)

    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('passes arguments to the function', () => {
    const fn = vi.fn()
    const debouncedFn = debounce(fn, 100)

    debouncedFn('arg1', 'arg2')
    vi.advanceTimersByTime(100)

    expect(fn).toHaveBeenCalledWith('arg1', 'arg2')
  })
})

describe('throttle', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('executes immediately on first call', () => {
    const fn = vi.fn()
    const throttledFn = throttle(fn, 100)

    throttledFn()
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('limits execution rate', () => {
    const fn = vi.fn()
    const throttledFn = throttle(fn, 100)

    throttledFn()
    throttledFn()
    throttledFn()

    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('allows execution after throttle period', () => {
    const fn = vi.fn()
    const throttledFn = throttle(fn, 100)

    throttledFn()
    vi.advanceTimersByTime(100)
    throttledFn()

    expect(fn).toHaveBeenCalledTimes(2)
  })
})

describe('isClient', () => {
  it('returns true in browser environment', () => {
    // jsdom provides window object
    expect(isClient()).toBe(true)
  })
})

describe('isServer', () => {
  it('returns false in browser environment', () => {
    // jsdom provides window object
    expect(isServer()).toBe(false)
  })
})

describe('sleep', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('resolves after specified time', async () => {
    const promise = sleep(100)
    vi.advanceTimersByTime(100)
    await expect(promise).resolves.toBeUndefined()
  })
})

describe('toKebabCase', () => {
  it('converts camelCase to kebab-case', () => {
    expect(toKebabCase('camelCase')).toBe('camel-case')
  })

  it('converts PascalCase to kebab-case', () => {
    expect(toKebabCase('PascalCase')).toBe('pascal-case')
  })

  it('converts spaces to hyphens', () => {
    expect(toKebabCase('hello world')).toBe('hello-world')
  })

  it('converts underscores to hyphens', () => {
    expect(toKebabCase('hello_world')).toBe('hello-world')
  })

  it('handles already kebab-case', () => {
    expect(toKebabCase('already-kebab')).toBe('already-kebab')
  })
})

describe('toCamelCase', () => {
  it('converts kebab-case to camelCase', () => {
    expect(toCamelCase('kebab-case')).toBe('kebabCase')
  })

  it('converts snake_case to camelCase', () => {
    expect(toCamelCase('snake_case')).toBe('snakeCase')
  })

  it('converts spaces to camelCase', () => {
    expect(toCamelCase('hello world')).toBe('helloWorld')
  })

  it('handles already camelCase', () => {
    expect(toCamelCase('alreadyCamel')).toBe('alreadyCamel')
  })

  it('lowercases first character', () => {
    expect(toCamelCase('PascalCase')).toBe('pascalCase')
  })
})
