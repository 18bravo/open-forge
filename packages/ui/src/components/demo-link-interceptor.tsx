'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useEffect, type ReactNode } from 'react';

/**
 * Intercepts link clicks in demo mode and redirects to /demo/* equivalents
 * This allows reusing existing page components without modifying their links
 */
export function DemoLinkInterceptor({ children }: { children: ReactNode }) {
  const router = useRouter();

  const handleClick = useCallback(
    (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest('a');

      if (!link) return;

      const href = link.getAttribute('href');
      if (!href) return;

      // Skip external links, hash links, already-demo links, and root path (exit demo)
      if (
        href.startsWith('http') ||
        href.startsWith('#') ||
        href.startsWith('/demo') ||
        href.startsWith('mailto:') ||
        href === '/'
      ) {
        return;
      }

      // Skip links that open in new tab
      if (link.target === '_blank') return;

      // Intercept internal links and redirect to demo version
      if (href.startsWith('/')) {
        e.preventDefault();
        e.stopPropagation();
        router.push(`/demo${href}`);
      }
    },
    [router]
  );

  useEffect(() => {
    // Use capture phase to intercept before React's event handlers
    document.addEventListener('click', handleClick, true);
    return () => {
      document.removeEventListener('click', handleClick, true);
    };
  }, [handleClick]);

  return <>{children}</>;
}
