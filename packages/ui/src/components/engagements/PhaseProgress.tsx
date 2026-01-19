'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';
import type { EngagementStatus } from '@/lib/api';

interface Phase {
  id: string;
  name: string;
  description?: string;
}

const DEFAULT_PHASES: Phase[] = [
  { id: 'draft', name: 'Draft', description: 'Initial configuration' },
  { id: 'approval', name: 'Approval', description: 'Awaiting review' },
  { id: 'data_ingestion', name: 'Data Ingestion', description: 'Loading data sources' },
  { id: 'ontology', name: 'Ontology', description: 'Schema generation' },
  { id: 'analysis', name: 'Analysis', description: 'AI processing' },
  { id: 'review', name: 'Review', description: 'Final review' },
  { id: 'complete', name: 'Complete', description: 'Engagement finished' },
];

// Map engagement status to phase index
const statusToPhase: Record<EngagementStatus, number> = {
  draft: 0,
  pending_approval: 1,
  approved: 2,
  in_progress: 3, // Could be data_ingestion, ontology, or analysis
  paused: -1, // Show current phase as paused
  completed: 6,
  cancelled: -2,
  failed: -3,
};

interface PhaseProgressProps {
  status: EngagementStatus;
  currentPhase?: number;
  phases?: Phase[];
  orientation?: 'horizontal' | 'vertical';
  className?: string;
  showDescriptions?: boolean;
}

export function PhaseProgress({
  status,
  currentPhase,
  phases = DEFAULT_PHASES,
  orientation = 'horizontal',
  className,
  showDescriptions = false,
}: PhaseProgressProps) {
  const activePhase = currentPhase ?? statusToPhase[status] ?? 0;
  const isFailed = status === 'failed';
  const isCancelled = status === 'cancelled';
  const isPaused = status === 'paused';

  const getPhaseState = (index: number) => {
    if (isFailed || isCancelled) {
      return index < Math.max(0, activePhase) ? 'completed' : 'inactive';
    }
    if (index < activePhase) return 'completed';
    if (index === activePhase) return isPaused ? 'paused' : 'active';
    return 'upcoming';
  };

  if (orientation === 'vertical') {
    return (
      <div className={cn('flex flex-col space-y-2', className)}>
        {phases.map((phase, index) => {
          const state = getPhaseState(index);
          return (
            <div key={phase.id} className="flex items-start gap-3">
              <div className="flex flex-col items-center">
                <PhaseIcon state={state} />
                {index < phases.length - 1 && (
                  <div
                    className={cn(
                      'w-0.5 h-6 mt-1',
                      state === 'completed'
                        ? 'bg-green-500'
                        : 'bg-muted'
                    )}
                  />
                )}
              </div>
              <div className="pt-0.5">
                <p
                  className={cn(
                    'text-sm font-medium',
                    state === 'completed' && 'text-green-600 dark:text-green-400',
                    state === 'active' && 'text-primary',
                    state === 'paused' && 'text-orange-600 dark:text-orange-400',
                    state === 'upcoming' && 'text-muted-foreground'
                  )}
                >
                  {phase.name}
                </p>
                {showDescriptions && phase.description && (
                  <p className="text-xs text-muted-foreground">{phase.description}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center justify-between">
        {phases.map((phase, index) => {
          const state = getPhaseState(index);
          const isLast = index === phases.length - 1;

          return (
            <React.Fragment key={phase.id}>
              <div className="flex flex-col items-center">
                <PhaseIcon state={state} />
                <span
                  className={cn(
                    'mt-2 text-xs font-medium text-center hidden sm:block',
                    state === 'completed' && 'text-green-600 dark:text-green-400',
                    state === 'active' && 'text-primary',
                    state === 'paused' && 'text-orange-600 dark:text-orange-400',
                    state === 'upcoming' && 'text-muted-foreground'
                  )}
                >
                  {phase.name}
                </span>
              </div>
              {!isLast && (
                <div
                  className={cn(
                    'flex-1 h-0.5 mx-2',
                    getPhaseState(index + 1) === 'completed' || state === 'completed'
                      ? 'bg-green-500'
                      : state === 'active'
                      ? 'bg-gradient-to-r from-green-500 to-muted'
                      : 'bg-muted'
                  )}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

interface PhaseIconProps {
  state: 'completed' | 'active' | 'paused' | 'upcoming' | 'inactive';
}

function PhaseIcon({ state }: PhaseIconProps) {
  switch (state) {
    case 'completed':
      return (
        <CheckCircle2 className="h-6 w-6 text-green-500" />
      );
    case 'active':
      return (
        <div className="relative">
          <Loader2 className="h-6 w-6 text-primary animate-spin" />
        </div>
      );
    case 'paused':
      return (
        <div className="h-6 w-6 rounded-full border-2 border-orange-500 flex items-center justify-center">
          <div className="w-2 h-2 bg-orange-500 rounded-sm" />
        </div>
      );
    case 'inactive':
    case 'upcoming':
    default:
      return (
        <Circle className="h-6 w-6 text-muted-foreground" />
      );
  }
}
