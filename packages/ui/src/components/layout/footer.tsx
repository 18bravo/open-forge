import * as React from 'react';
import Link from 'next/link';

import { cn } from '@/lib/utils';
import { Separator } from '@/components/ui/separator';

interface FooterProps {
  className?: string;
}

export function Footer({ className }: FooterProps) {
  return (
    <footer className={cn('border-t bg-background', className)}>
      <div className="container py-8">
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Open Forge</h3>
            <p className="text-sm text-muted-foreground">
              The open-source data platform for building and managing data-driven
              applications.
            </p>
          </div>

          <div className="space-y-4">
            <h4 className="text-sm font-semibold">Product</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  href="/features"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Features
                </Link>
              </li>
              <li>
                <Link
                  href="/pricing"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Pricing
                </Link>
              </li>
              <li>
                <Link
                  href="/docs"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Documentation
                </Link>
              </li>
              <li>
                <Link
                  href="/changelog"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Changelog
                </Link>
              </li>
            </ul>
          </div>

          <div className="space-y-4">
            <h4 className="text-sm font-semibold">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  href="/blog"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Blog
                </Link>
              </li>
              <li>
                <Link
                  href="/community"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Community
                </Link>
              </li>
              <li>
                <Link
                  href="/support"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Support
                </Link>
              </li>
              <li>
                <a
                  href="https://github.com/open-forge"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  GitHub
                </a>
              </li>
            </ul>
          </div>

          <div className="space-y-4">
            <h4 className="text-sm font-semibold">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  href="/privacy"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link
                  href="/terms"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link
                  href="/security"
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  Security
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <Separator className="my-8" />

        <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} Open Forge. All rights reserved.
          </p>
          <p className="text-sm text-muted-foreground">
            Built with Next.js, TypeScript, and Tailwind CSS.
          </p>
        </div>
      </div>
    </footer>
  );
}
