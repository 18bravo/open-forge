'use client';

import Link from 'next/link';
import { ArrowRight, Sparkles } from 'lucide-react';

/**
 * Banner displayed at the top of demo pages to indicate sample data
 */
export function DemoBanner() {
  return (
    <div className="flex items-center justify-center gap-2 bg-violet-600 px-4 py-2 text-sm text-white">
      <Sparkles className="h-4 w-4" />
      <span>You&apos;re viewing a demo with sample data.</span>
      <Link
        href="/docs/quickstart"
        className="inline-flex items-center gap-1 font-medium underline underline-offset-2 hover:no-underline"
      >
        Start with your own data
        <ArrowRight className="h-3 w-3" />
      </Link>
    </div>
  );
}
