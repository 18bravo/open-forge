'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

/**
 * Props for the LangSmithEmbed component
 */
interface LangSmithEmbedProps {
  /** Engagement ID to filter traces by */
  engagementId?: string;
  /** Specific run ID to display */
  runId?: string;
  /** LangSmith base URL (for self-hosted instances) */
  baseUrl?: string;
  /** LangSmith project name */
  projectName?: string;
  /** Height of the embed iframe */
  height?: number | string;
  /** Additional CSS classes */
  className?: string;
  /** Whether to show in a card wrapper */
  showCard?: boolean;
  /** Card title (only used if showCard is true) */
  cardTitle?: string;
  /** Callback when the iframe loads */
  onLoad?: () => void;
  /** Callback when there's an error loading */
  onError?: (error: Error) => void;
}

/**
 * Loading skeleton for the LangSmith embed
 */
function LangSmithEmbedSkeleton({ height }: { height: number | string }) {
  return (
    <div className="space-y-4 p-4" style={{ height }}>
      <div className="flex items-center gap-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-8 w-32" />
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
      <div className="grid grid-cols-3 gap-4 mt-6">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <Skeleton className="h-40 mt-4" />
    </div>
  );
}

/**
 * Error state component for the LangSmith embed
 */
function LangSmithEmbedError({
  error,
  onRetry,
}: {
  error: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="rounded-full bg-destructive/10 p-3 mb-4">
        <svg
          className="h-6 w-6 text-destructive"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-semibold mb-2">Failed to load LangSmith</h3>
      <p className="text-sm text-muted-foreground mb-4">{error}</p>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  );
}

/**
 * LangSmithEmbed component for embedding LangSmith dashboard views.
 *
 * Supports both hosted LangSmith (smith.langchain.com) and self-hosted instances.
 * Can filter by engagement ID or show a specific run.
 *
 * @example
 * // Show traces for an engagement
 * <LangSmithEmbed engagementId="eng-123" showCard />
 *
 * @example
 * // Show a specific run
 * <LangSmithEmbed runId="run-456" />
 *
 * @example
 * // Self-hosted LangSmith
 * <LangSmithEmbed
 *   engagementId="eng-123"
 *   baseUrl="http://langsmith.internal:3001"
 *   projectName="my-project"
 * />
 */
export function LangSmithEmbed({
  engagementId,
  runId,
  baseUrl = process.env.NEXT_PUBLIC_LANGSMITH_URL || 'https://smith.langchain.com',
  projectName = process.env.NEXT_PUBLIC_LANGSMITH_PROJECT || 'open-forge',
  height = 600,
  className,
  showCard = false,
  cardTitle = 'LangSmith Traces',
  onLoad,
  onError,
}: LangSmithEmbedProps) {
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const iframeRef = React.useRef<HTMLIFrameElement>(null);

  // Construct the LangSmith URL based on provided props
  const langsmithUrl = React.useMemo(() => {
    const base = baseUrl.replace(/\/$/, ''); // Remove trailing slash

    if (runId) {
      // Direct link to a specific run
      return `${base}/public/${projectName}/runs/${runId}`;
    }

    // Project view with optional engagement filter
    let url = `${base}/public/${projectName}/traces`;

    // Add filter for engagement if provided
    if (engagementId) {
      const filter = encodeURIComponent(`engagement:${engagementId}`);
      url += `?filter=${filter}`;
    }

    return url;
  }, [baseUrl, projectName, runId, engagementId]);

  // Handle iframe load
  const handleLoad = React.useCallback(() => {
    setIsLoading(false);
    setError(null);
    onLoad?.();
  }, [onLoad]);

  // Handle iframe error
  const handleError = React.useCallback(() => {
    const err = new Error('Failed to load LangSmith dashboard');
    setIsLoading(false);
    setError(err.message);
    onError?.(err);
  }, [onError]);

  // Retry loading
  const handleRetry = React.useCallback(() => {
    setIsLoading(true);
    setError(null);
    if (iframeRef.current) {
      iframeRef.current.src = langsmithUrl;
    }
  }, [langsmithUrl]);

  // Open in new tab
  const handleOpenInNewTab = React.useCallback(() => {
    window.open(langsmithUrl, '_blank', 'noopener,noreferrer');
  }, [langsmithUrl]);

  const content = (
    <div className={cn('relative', className)}>
      {/* Loading state */}
      {isLoading && !error && (
        <div className="absolute inset-0 z-10 bg-background">
          <LangSmithEmbedSkeleton height={height} />
        </div>
      )}

      {/* Error state */}
      {error && (
        <div style={{ height }}>
          <LangSmithEmbedError error={error} onRetry={handleRetry} />
        </div>
      )}

      {/* Iframe */}
      {!error && (
        <iframe
          ref={iframeRef}
          src={langsmithUrl}
          title={`LangSmith ${runId ? 'Run' : 'Traces'}${engagementId ? ` - ${engagementId}` : ''}`}
          className={cn(
            'w-full border-0 rounded-md',
            isLoading && 'invisible'
          )}
          style={{ height }}
          onLoad={handleLoad}
          onError={handleError}
          allow="clipboard-write"
          sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
        />
      )}

      {/* Open in new tab button */}
      <div className="absolute top-2 right-2 z-20">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleOpenInNewTab}
          className="opacity-0 hover:opacity-100 focus:opacity-100 transition-opacity bg-background/80"
          title="Open in new tab"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </Button>
      </div>
    </div>
  );

  if (showCard) {
    return (
      <Card className={className}>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-lg font-semibold">{cardTitle}</CardTitle>
          <Button variant="ghost" size="sm" onClick={handleOpenInNewTab}>
            Open in LangSmith
          </Button>
        </CardHeader>
        <CardContent className="p-0">{content}</CardContent>
      </Card>
    );
  }

  return content;
}

/**
 * Compact trace summary component for inline use
 */
interface TracesSummaryProps {
  engagementId: string;
  className?: string;
}

export function LangSmithTracesSummary({
  engagementId,
  className,
}: TracesSummaryProps) {
  const [stats, setStats] = React.useState<{
    total: number;
    success: number;
    error: number;
    avgLatency: number;
  } | null>(null);

  // In a real implementation, this would fetch from the API
  React.useEffect(() => {
    // Simulate fetching stats
    const timer = setTimeout(() => {
      setStats({
        total: Math.floor(Math.random() * 100) + 10,
        success: Math.floor(Math.random() * 80) + 10,
        error: Math.floor(Math.random() * 10),
        avgLatency: Math.floor(Math.random() * 500) + 100,
      });
    }, 500);

    return () => clearTimeout(timer);
  }, [engagementId]);

  if (!stats) {
    return (
      <div className={cn('flex items-center gap-4', className)}>
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-20" />
      </div>
    );
  }

  return (
    <div className={cn('flex items-center gap-4 text-sm', className)}>
      <div className="flex items-center gap-1">
        <span className="text-muted-foreground">Traces:</span>
        <span className="font-medium">{stats.total}</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="h-2 w-2 rounded-full bg-green-500" />
        <span className="font-medium">{stats.success}</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="h-2 w-2 rounded-full bg-red-500" />
        <span className="font-medium">{stats.error}</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-muted-foreground">Avg:</span>
        <span className="font-medium">{stats.avgLatency}ms</span>
      </div>
    </div>
  );
}

export default LangSmithEmbed;
