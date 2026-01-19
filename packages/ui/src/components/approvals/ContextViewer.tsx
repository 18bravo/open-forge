'use client';

import * as React from 'react';
import {
  ChevronRight,
  ChevronDown,
  Copy,
  Check,
  Maximize2,
  Minimize2,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ContextViewerProps {
  data: Record<string, unknown> | unknown[] | unknown;
  title?: string;
  maxHeight?: string;
  expandable?: boolean;
  className?: string;
}

export function ContextViewer({
  data,
  title = 'Context',
  maxHeight = '400px',
  expandable = true,
  className,
}: ContextViewerProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const content = (
    <div className="font-mono text-sm">
      <JsonNode data={data} depth={0} />
    </div>
  );

  return (
    <div
      className={cn(
        'rounded-lg border bg-muted/30',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-2">
        <span className="text-sm font-medium text-muted-foreground">{title}</span>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="h-7 w-7 p-0"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
            <span className="sr-only">Copy JSON</span>
          </Button>

          {expandable && (
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                  <Maximize2 className="h-3.5 w-3.5" />
                  <span className="sr-only">Expand</span>
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-3xl max-h-[80vh]">
                <DialogHeader>
                  <DialogTitle>{title}</DialogTitle>
                </DialogHeader>
                <ScrollArea className="h-[60vh]">
                  <div className="p-4 font-mono text-sm">
                    <JsonNode data={data} depth={0} defaultExpanded />
                  </div>
                </ScrollArea>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="p-4" style={{ maxHeight }}>
        {content}
      </ScrollArea>
    </div>
  );
}

interface JsonNodeProps {
  data: unknown;
  depth: number;
  keyName?: string;
  defaultExpanded?: boolean;
}

function JsonNode({ data, depth, keyName, defaultExpanded = false }: JsonNodeProps) {
  const [isExpanded, setIsExpanded] = React.useState(
    defaultExpanded || depth < 2
  );

  const indent = depth * 16;

  // Null
  if (data === null) {
    return (
      <div style={{ paddingLeft: indent }}>
        {keyName && <span className="text-purple-600 dark:text-purple-400">"{keyName}"</span>}
        {keyName && <span className="text-muted-foreground">: </span>}
        <span className="text-orange-600 dark:text-orange-400">null</span>
      </div>
    );
  }

  // Undefined
  if (data === undefined) {
    return (
      <div style={{ paddingLeft: indent }}>
        {keyName && <span className="text-purple-600 dark:text-purple-400">"{keyName}"</span>}
        {keyName && <span className="text-muted-foreground">: </span>}
        <span className="text-muted-foreground">undefined</span>
      </div>
    );
  }

  // Boolean
  if (typeof data === 'boolean') {
    return (
      <div style={{ paddingLeft: indent }}>
        {keyName && <span className="text-purple-600 dark:text-purple-400">"{keyName}"</span>}
        {keyName && <span className="text-muted-foreground">: </span>}
        <span className="text-blue-600 dark:text-blue-400">{data.toString()}</span>
      </div>
    );
  }

  // Number
  if (typeof data === 'number') {
    return (
      <div style={{ paddingLeft: indent }}>
        {keyName && <span className="text-purple-600 dark:text-purple-400">"{keyName}"</span>}
        {keyName && <span className="text-muted-foreground">: </span>}
        <span className="text-green-600 dark:text-green-400">{data}</span>
      </div>
    );
  }

  // String
  if (typeof data === 'string') {
    // Check if it's a URL
    const isUrl = data.startsWith('http://') || data.startsWith('https://');
    // Check if it's a long string
    const isLong = data.length > 100;

    return (
      <div style={{ paddingLeft: indent }}>
        {keyName && <span className="text-purple-600 dark:text-purple-400">"{keyName}"</span>}
        {keyName && <span className="text-muted-foreground">: </span>}
        {isUrl ? (
          <a
            href={data}
            target="_blank"
            rel="noopener noreferrer"
            className="text-yellow-600 dark:text-yellow-400 hover:underline"
          >
            "{data}"
          </a>
        ) : (
          <span
            className={cn(
              'text-yellow-600 dark:text-yellow-400',
              isLong && 'break-all'
            )}
          >
            "{isLong ? data.slice(0, 100) + '...' : data}"
          </span>
        )}
      </div>
    );
  }

  // Array
  if (Array.isArray(data)) {
    if (data.length === 0) {
      return (
        <div style={{ paddingLeft: indent }}>
          {keyName && <span className="text-purple-600 dark:text-purple-400">"{keyName}"</span>}
          {keyName && <span className="text-muted-foreground">: </span>}
          <span className="text-muted-foreground">[]</span>
        </div>
      );
    }

    return (
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <div style={{ paddingLeft: indent }}>
          <CollapsibleTrigger className="flex items-center gap-1 hover:text-foreground">
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
            {keyName && <span className="text-purple-600 dark:text-purple-400">"{keyName}"</span>}
            {keyName && <span className="text-muted-foreground">: </span>}
            <span className="text-muted-foreground">[</span>
            {!isExpanded && (
              <span className="text-muted-foreground text-xs ml-1">
                {data.length} items
              </span>
            )}
          </CollapsibleTrigger>
          <CollapsibleContent>
            {data.map((item, index) => (
              <JsonNode
                key={index}
                data={item}
                depth={depth + 1}
                defaultExpanded={defaultExpanded}
              />
            ))}
            <div style={{ paddingLeft: indent }}>
              <span className="text-muted-foreground">]</span>
            </div>
          </CollapsibleContent>
        </div>
      </Collapsible>
    );
  }

  // Object
  if (typeof data === 'object') {
    const keys = Object.keys(data as Record<string, unknown>);

    if (keys.length === 0) {
      return (
        <div style={{ paddingLeft: indent }}>
          {keyName && <span className="text-purple-600 dark:text-purple-400">"{keyName}"</span>}
          {keyName && <span className="text-muted-foreground">: </span>}
          <span className="text-muted-foreground">{'{}'}</span>
        </div>
      );
    }

    return (
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <div style={{ paddingLeft: indent }}>
          <CollapsibleTrigger className="flex items-center gap-1 hover:text-foreground">
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
            {keyName && <span className="text-purple-600 dark:text-purple-400">"{keyName}"</span>}
            {keyName && <span className="text-muted-foreground">: </span>}
            <span className="text-muted-foreground">{'{'}</span>
            {!isExpanded && (
              <span className="text-muted-foreground text-xs ml-1">
                {keys.length} keys
              </span>
            )}
          </CollapsibleTrigger>
          <CollapsibleContent>
            {keys.map((key) => (
              <JsonNode
                key={key}
                data={(data as Record<string, unknown>)[key]}
                depth={depth + 1}
                keyName={key}
                defaultExpanded={defaultExpanded}
              />
            ))}
            <div style={{ paddingLeft: indent }}>
              <span className="text-muted-foreground">{'}'}</span>
            </div>
          </CollapsibleContent>
        </div>
      </Collapsible>
    );
  }

  // Fallback
  return (
    <div style={{ paddingLeft: indent }}>
      {keyName && <span className="text-purple-600 dark:text-purple-400">"{keyName}"</span>}
      {keyName && <span className="text-muted-foreground">: </span>}
      <span className="text-muted-foreground">{String(data)}</span>
    </div>
  );
}

// Simpler table-like view for flat objects
export function ContextTable({
  data,
  className,
}: {
  data: Record<string, unknown>;
  className?: string;
}) {
  const entries = Object.entries(data);

  if (entries.length === 0) {
    return (
      <div className={cn('text-sm text-muted-foreground', className)}>
        No data
      </div>
    );
  }

  return (
    <div className={cn('rounded-lg border', className)}>
      <table className="w-full text-sm">
        <tbody>
          {entries.map(([key, value], index) => (
            <tr
              key={key}
              className={cn(
                index !== entries.length - 1 && 'border-b'
              )}
            >
              <td className="px-4 py-2 font-medium text-muted-foreground whitespace-nowrap">
                {key}
              </td>
              <td className="px-4 py-2 font-mono break-all">
                {formatValue(value)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatValue(value: unknown): React.ReactNode {
  if (value === null) return <span className="text-muted-foreground">null</span>;
  if (value === undefined) return <span className="text-muted-foreground">undefined</span>;
  if (typeof value === 'boolean') return value.toString();
  if (typeof value === 'number') return value.toString();
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return `[${value.length} items]`;
  if (typeof value === 'object') return `{${Object.keys(value).length} keys}`;
  return String(value);
}
