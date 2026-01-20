'use client';

import * as React from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/engagements';
import { cn, formatRelativeTime, formatDateTime } from '@/lib/utils';
import { useAgentTasks, useAgentTask, useApproveToolCall } from '@/lib/hooks/use-agent';
import type { AgentTask, AgentTaskStatus, AgentMessage, ToolCall } from '@/lib/api';
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Loader2,
  MessageSquare,
  Play,
  RefreshCw,
  Terminal,
  User,
  Wrench,
  XCircle,
} from 'lucide-react';

const taskStatusIcons: Record<AgentTaskStatus, React.ReactNode> = {
  pending: <Clock className="h-4 w-4" />,
  queued: <Clock className="h-4 w-4" />,
  running: <Loader2 className="h-4 w-4 animate-spin" />,
  waiting_approval: <AlertCircle className="h-4 w-4" />,
  completed: <CheckCircle2 className="h-4 w-4" />,
  failed: <XCircle className="h-4 w-4" />,
  cancelled: <XCircle className="h-4 w-4" />,
};

interface AgentsPageProps {
  params: Promise<{ id: string }>;
}

export default function AgentsPage({ params }: AgentsPageProps) {
  const { id } = React.use(params);
  const { data: tasksData, isLoading, error } = useAgentTasks(id);
  const [selectedTaskId, setSelectedTaskId] = React.useState<string | null>(null);

  const tasks = tasksData?.items ?? [];

  // Auto-select first task when data loads
  React.useEffect(() => {
    if (tasks.length > 0 && !selectedTaskId) {
      setSelectedTaskId(tasks[0].id);
    }
  }, [tasks, selectedTaskId]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="flex flex-col items-center justify-center py-12 text-center">
        <h3 className="text-lg font-medium">Error loading tasks</h3>
        <p className="text-sm text-muted-foreground">
          {error.message || 'Failed to load agent tasks'}
        </p>
      </Card>
    );
  }

  const runningTasks = tasks.filter((t) => t.status === 'running');
  const pendingApprovalTasks = tasks.filter((t) => t.status === 'waiting_approval');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Agent Tasks</h2>
          <p className="text-sm text-muted-foreground">
            {runningTasks.length} running, {pendingApprovalTasks.length} awaiting approval
          </p>
        </div>
        <Button>
          <Play className="mr-2 h-4 w-4" />
          Run New Task
        </Button>
      </div>

      {/* Pending Approvals Alert */}
      {pendingApprovalTasks.length > 0 && (
        <Card className="border-amber-500/50 bg-amber-50 dark:bg-amber-950/20">
          <CardContent className="flex items-center gap-4 py-4">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            <div className="flex-1">
              <p className="font-medium text-amber-800 dark:text-amber-200">
                {pendingApprovalTasks.length} task{pendingApprovalTasks.length > 1 ? 's' : ''} awaiting approval
              </p>
              <p className="text-sm text-amber-700 dark:text-amber-300">
                Review and approve tool calls to continue agent execution.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedTaskId(pendingApprovalTasks[0].id)}
            >
              Review
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {tasks.length === 0 && (
        <Card className="flex flex-col items-center justify-center py-12 text-center">
          <Bot className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium">No agent tasks</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Start a new agent task to begin processing.
          </p>
          <Button>
            <Play className="mr-2 h-4 w-4" />
            Run New Task
          </Button>
        </Card>
      )}

      {tasks.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Task List */}
          <Card className="lg:col-span-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Tasks</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y">
                {tasks.map((task) => {
                  const isSelected = selectedTaskId === task.id;

                  return (
                    <button
                      key={task.id}
                      onClick={() => setSelectedTaskId(task.id)}
                      className={cn(
                        'flex items-start gap-3 w-full px-4 py-3 text-left hover:bg-muted/50 transition-colors',
                        isSelected && 'bg-primary/5 border-l-2 border-primary'
                      )}
                    >
                      <div className="mt-0.5">
                        {taskStatusIcons[task.status]}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">
                          {task.task_type.replace(/_/g, ' ')}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <StatusBadge status={task.status} size="sm" />
                          <span className="text-xs text-muted-foreground">
                            {task.current_iteration}
                          </span>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Task Detail */}
          <TaskDetail taskId={selectedTaskId} />
        </div>
      )}
    </div>
  );
}

function TaskDetail({ taskId }: { taskId: string | null }) {
  const { data: task, isLoading, error } = useAgentTask(taskId ?? undefined);
  const approveToolCallMutation = useApproveToolCall();

  if (!taskId) {
    return (
      <Card className="lg:col-span-2">
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <Bot className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium">Select a task</h3>
          <p className="text-sm text-muted-foreground">
            Choose a task from the list to view details
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className="lg:col-span-2">
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error || !task) {
    return (
      <Card className="lg:col-span-2">
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <h3 className="text-lg font-medium">Error loading task</h3>
          <p className="text-sm text-muted-foreground">
            {error?.message || 'Task not found'}
          </p>
        </CardContent>
      </Card>
    );
  }

  const handleApprove = async (toolCallId: string) => {
    await approveToolCallMutation.mutateAsync({
      taskId: task.id,
      toolCallId,
      approved: true,
    });
  };

  const handleReject = async (toolCallId: string, reason?: string) => {
    await approveToolCallMutation.mutateAsync({
      taskId: task.id,
      toolCallId,
      approved: false,
      reason,
    });
  };

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              {task.task_type.replace(/_/g, ' ')}
            </CardTitle>
            <CardDescription className="mt-1">
              {task.description}
            </CardDescription>
          </div>
          <StatusBadge status={task.status} />
        </div>
        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mt-2">
          <span>
            Iteration {task.current_iteration}/{task.max_iterations}
          </span>
          {task.started_at && (
            <span>Started {formatRelativeTime(task.started_at)}</span>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Pending Approvals */}
        {task.pending_tool_approvals.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium">Pending Approvals</h4>
            {task.pending_tool_approvals.map((tool) => (
              <ToolApprovalCard
                key={tool.id}
                toolCall={tool}
                onApprove={() => handleApprove(tool.id)}
                onReject={(reason) => handleReject(tool.id, reason)}
                isProcessing={approveToolCallMutation.isPending}
              />
            ))}
          </div>
        )}

        {/* Tools */}
        <div>
          <h4 className="text-sm font-medium mb-2">Available Tools</h4>
          <div className="flex flex-wrap gap-2">
            {task.tools.map((tool) => (
              <span
                key={tool}
                className="inline-flex items-center gap-1 px-2 py-1 rounded bg-muted text-sm"
              >
                <Wrench className="h-3 w-3" />
                {tool}
              </span>
            ))}
          </div>
        </div>

        {/* Message History */}
        <div>
          <h4 className="text-sm font-medium mb-3">Conversation</h4>
          <div className="space-y-4 max-h-[400px] overflow-y-auto">
            {task.messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {task.messages.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">
                No messages yet
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface ToolApprovalCardProps {
  toolCall: ToolCall;
  onApprove: () => void;
  onReject: (reason?: string) => void;
  isProcessing: boolean;
}

function ToolApprovalCard({ toolCall, onApprove, onReject, isProcessing }: ToolApprovalCardProps) {
  return (
    <Card className="border-amber-500/50">
      <CardContent className="py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Terminal className="h-4 w-4 text-amber-600" />
              <span className="font-medium">{toolCall.name}</span>
            </div>
            <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
              {JSON.stringify(toolCall.arguments, null, 2)}
            </pre>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onReject()}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Reject'
              )}
            </Button>
            <Button
              size="sm"
              onClick={onApprove}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Approve'
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function MessageBubble({ message }: { message: AgentMessage }) {
  const isAssistant = message.role === 'assistant';
  const isSystem = message.role === 'system';
  const isTool = message.role === 'tool';

  return (
    <div className={cn('flex gap-3', isAssistant && 'flex-row-reverse')}>
      <div
        className={cn(
          'flex h-8 w-8 items-center justify-center rounded-full',
          isAssistant && 'bg-primary text-primary-foreground',
          isSystem && 'bg-muted',
          isTool && 'bg-purple-100 text-purple-600 dark:bg-purple-900 dark:text-purple-400',
          !isAssistant && !isSystem && !isTool && 'bg-secondary'
        )}
      >
        {isAssistant && <Bot className="h-4 w-4" />}
        {isSystem && <Terminal className="h-4 w-4" />}
        {isTool && <Wrench className="h-4 w-4" />}
        {!isAssistant && !isSystem && !isTool && <User className="h-4 w-4" />}
      </div>
      <div className={cn('flex-1 max-w-[80%]', isAssistant && 'text-right')}>
        <div
          className={cn(
            'inline-block px-4 py-2 rounded-lg text-sm',
            isAssistant && 'bg-primary text-primary-foreground',
            isSystem && 'bg-muted',
            isTool && 'bg-purple-100 dark:bg-purple-900',
            !isAssistant && !isSystem && !isTool && 'bg-secondary'
          )}
        >
          {message.content}
        </div>

        {/* Tool Calls */}
        {message.tool_calls && message.tool_calls.length > 0 && (
          <div className="mt-2 space-y-2">
            {message.tool_calls.map((tc) => (
              <div
                key={tc.id}
                className="p-2 rounded bg-muted text-xs"
              >
                <div className="flex items-center gap-2 mb-1">
                  <Wrench className="h-3 w-3" />
                  <span className="font-medium">{tc.name}</span>
                  {tc.duration_ms && (
                    <span className="text-muted-foreground">
                      {tc.duration_ms}ms
                    </span>
                  )}
                </div>
                {tc.result && (
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(tc.result, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}

        <p className="text-xs text-muted-foreground mt-1">
          {formatRelativeTime(message.timestamp)}
        </p>
      </div>
    </div>
  );
}
