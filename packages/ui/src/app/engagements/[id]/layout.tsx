'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/engagements';
import { cn } from '@/lib/utils';
import { useEngagement, useUpdateEngagementStatus } from '@/lib/hooks';
import { Skeleton } from '@/components/ui/skeleton';
import {
  ArrowLeft,
  Bot,
  CheckSquare,
  Database,
  FileCode,
  LayoutDashboard,
  MoreVertical,
  Play,
  Pause,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface Tab {
  name: string;
  href: string;
  icon: React.ElementType;
}

interface EngagementLayoutProps {
  children: React.ReactNode;
  params: { id: string };
}

export default function EngagementLayout({ children, params }: EngagementLayoutProps) {
  const pathname = usePathname();
  const basePath = `/engagements/${params.id}`;

  // Fetch engagement data from API
  const { data: engagement, isLoading, error } = useEngagement(params.id);
  const updateStatus = useUpdateEngagementStatus();

  const tabs: Tab[] = [
    { name: 'Overview', href: `${basePath}/overview`, icon: LayoutDashboard },
    { name: 'Data Sources', href: `${basePath}/data-sources`, icon: Database },
    { name: 'Ontology', href: `${basePath}/ontology`, icon: FileCode },
    { name: 'Agents', href: `${basePath}/agents`, icon: Bot },
    { name: 'Approvals', href: `${basePath}/approvals`, icon: CheckSquare },
  ];

  // Determine active tab
  const activeTab = tabs.find((tab) => pathname === tab.href) || tabs[0];

  // If we're at the base path, redirect to overview
  const isBasePath = pathname === basePath;

  const handleStatusChange = (newStatus: 'paused' | 'in_progress' | 'cancelled') => {
    if (engagement) {
      updateStatus.mutate({ id: engagement.id, status: newStatus });
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen">
        <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
          <div className="container py-4">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div className="flex items-start gap-4">
                <Button variant="ghost" size="icon" asChild className="mt-1">
                  <Link href="/engagements">
                    <ArrowLeft className="h-4 w-4" />
                  </Link>
                </Button>
                <div className="space-y-2">
                  <Skeleton className="h-8 w-64" />
                  <Skeleton className="h-4 w-96" />
                </div>
              </div>
            </div>
            <div className="flex gap-1">
              {tabs.map((tab) => (
                <Skeleton key={tab.name} className="h-10 w-24" />
              ))}
            </div>
          </div>
        </div>
        <div className="container py-6">
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  // Show error state
  if (error || !engagement) {
    return (
      <div className="min-h-screen">
        <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
          <div className="container py-4">
            <div className="flex items-start gap-4">
              <Button variant="ghost" size="icon" asChild className="mt-1">
                <Link href="/engagements">
                  <ArrowLeft className="h-4 w-4" />
                </Link>
              </Button>
              <h1 className="text-2xl font-bold tracking-tight">Engagement</h1>
            </div>
          </div>
        </div>
        <div className="container py-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error loading engagement</AlertTitle>
            <AlertDescription>
              {error?.message || 'Engagement not found. Please try again.'}
            </AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
        <div className="container py-4">
          {/* Back button and title */}
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex items-start gap-4">
              <Button variant="ghost" size="icon" asChild className="mt-1">
                <Link href="/engagements">
                  <ArrowLeft className="h-4 w-4" />
                </Link>
              </Button>
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold tracking-tight">
                    {engagement.name}
                  </h1>
                  <StatusBadge status={engagement.status} />
                </div>
                {engagement.description && (
                  <p className="text-muted-foreground mt-1 max-w-2xl">
                    {engagement.description}
                  </p>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {engagement.status === 'in_progress' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleStatusChange('paused')}
                  disabled={updateStatus.isPending}
                >
                  <Pause className="mr-2 h-4 w-4" />
                  Pause
                </Button>
              )}
              {engagement.status === 'paused' && (
                <Button
                  size="sm"
                  onClick={() => handleStatusChange('in_progress')}
                  disabled={updateStatus.isPending}
                >
                  <Play className="mr-2 h-4 w-4" />
                  Resume
                </Button>
              )}
              {engagement.status === 'approved' && (
                <Button
                  size="sm"
                  onClick={() => handleStatusChange('in_progress')}
                  disabled={updateStatus.isPending}
                >
                  <Play className="mr-2 h-4 w-4" />
                  Start
                </Button>
              )}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="icon">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem>Edit Configuration</DropdownMenuItem>
                  <DropdownMenuItem>View Logs</DropdownMenuItem>
                  <DropdownMenuItem>Export Results</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    className="text-destructive"
                    onClick={() => handleStatusChange('cancelled')}
                  >
                    <XCircle className="mr-2 h-4 w-4" />
                    Cancel Engagement
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = isBasePath
                ? tab.href.endsWith('/overview')
                : pathname === tab.href;

              return (
                <Link
                  key={tab.name}
                  href={tab.href}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors whitespace-nowrap',
                    isActive
                      ? 'border-primary text-primary bg-primary/5'
                      : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {tab.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="container py-6">{children}</div>
    </div>
  );
}
