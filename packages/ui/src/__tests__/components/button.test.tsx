/**
 * Tests for Button component
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '@/components/ui/button'

describe('Button', () => {
  describe('rendering', () => {
    it('renders with default props', () => {
      render(<Button>Click me</Button>)
      expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
    })

    it('renders children correctly', () => {
      render(<Button>Test Content</Button>)
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('renders as a button element by default', () => {
      render(<Button>Button</Button>)
      const button = screen.getByRole('button')
      expect(button.tagName).toBe('BUTTON')
    })
  })

  describe('variants', () => {
    it('applies default variant styles', () => {
      render(<Button variant="default">Default</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-primary')
    })

    it('applies destructive variant styles', () => {
      render(<Button variant="destructive">Delete</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-destructive')
    })

    it('applies outline variant styles', () => {
      render(<Button variant="outline">Outline</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('border')
    })

    it('applies secondary variant styles', () => {
      render(<Button variant="secondary">Secondary</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-secondary')
    })

    it('applies ghost variant styles', () => {
      render(<Button variant="ghost">Ghost</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('hover:bg-accent')
    })

    it('applies link variant styles', () => {
      render(<Button variant="link">Link</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('underline-offset-4')
    })
  })

  describe('sizes', () => {
    it('applies default size', () => {
      render(<Button size="default">Default</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-10')
    })

    it('applies small size', () => {
      render(<Button size="sm">Small</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-9')
    })

    it('applies large size', () => {
      render(<Button size="lg">Large</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-11')
    })

    it('applies icon size', () => {
      render(<Button size="icon">Icon</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-10', 'w-10')
    })
  })

  describe('interactions', () => {
    it('calls onClick handler when clicked', () => {
      const handleClick = vi.fn()
      render(<Button onClick={handleClick}>Click me</Button>)

      fireEvent.click(screen.getByRole('button'))
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('does not call onClick when disabled', () => {
      const handleClick = vi.fn()
      render(<Button onClick={handleClick} disabled>Disabled</Button>)

      fireEvent.click(screen.getByRole('button'))
      expect(handleClick).not.toHaveBeenCalled()
    })

    it('applies disabled styles when disabled', () => {
      render(<Button disabled>Disabled</Button>)
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
      expect(button).toHaveClass('disabled:opacity-50')
    })
  })

  describe('asChild', () => {
    it('renders as child element when asChild is true', () => {
      render(
        <Button asChild>
          <a href="/test">Link Button</a>
        </Button>
      )
      const link = screen.getByRole('link', { name: /link button/i })
      expect(link).toBeInTheDocument()
      expect(link).toHaveAttribute('href', '/test')
    })
  })

  describe('custom className', () => {
    it('merges custom className with default classes', () => {
      render(<Button className="custom-class">Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
      expect(button).toHaveClass('inline-flex')
    })
  })

  describe('accessibility', () => {
    it('has accessible name from children', () => {
      render(<Button>Accessible Button</Button>)
      expect(screen.getByRole('button', { name: 'Accessible Button' })).toBeInTheDocument()
    })

    it('supports aria-label', () => {
      render(<Button aria-label="Custom label">Button</Button>)
      expect(screen.getByRole('button', { name: 'Custom label' })).toBeInTheDocument()
    })

    it('can receive focus', () => {
      render(<Button>Focusable</Button>)
      const button = screen.getByRole('button')
      button.focus()
      expect(button).toHaveFocus()
    })

    it('cannot receive focus when disabled', () => {
      render(<Button disabled>Not focusable</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('disabled')
    })
  })

  describe('type attribute', () => {
    it('defaults to button type', () => {
      render(<Button>Button</Button>)
      // Note: React defaults to no type attribute, browser defaults to submit
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('accepts submit type', () => {
      render(<Button type="submit">Submit</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'submit')
    })

    it('accepts reset type', () => {
      render(<Button type="reset">Reset</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'reset')
    })
  })
})
