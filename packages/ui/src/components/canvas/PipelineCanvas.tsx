'use client';

import * as React from 'react';
import { useCallback, useEffect, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  NodeTypes,
  EdgeTypes,
  BackgroundVariant,
  Panel,
  ReactFlowProvider,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { SourceNode } from './nodes/SourceNode';
import { TransformNode } from './nodes/TransformNode';
import { DestinationNode } from './nodes/DestinationNode';
import { AssetNode } from './nodes/AssetNode';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  Database,
  GitBranch,
  Play,
  Save,
  Undo2,
  Redo2,
  ZoomIn,
  ZoomOut,
  Maximize2,
} from 'lucide-react';

// Register custom node types
const nodeTypes: NodeTypes = {
  source: SourceNode,
  transform: TransformNode,
  destination: DestinationNode,
  asset: AssetNode,
};

// Default edge styling
const defaultEdgeOptions = {
  style: { strokeWidth: 2, stroke: '#52525b' },
  type: 'smoothstep',
  animated: false,
};

export interface PipelineNode extends Node {
  data: {
    label: string;
    connectorType?: string;
    config?: Record<string, unknown>;
    status?: 'idle' | 'running' | 'success' | 'error';
    objectType?: string;
    transform?: {
      type: string;
      schema?: Record<string, unknown>;
    };
    destinationType?: string;
    assetKey?: string;
    description?: string;
  };
}

export interface PipelineEdge extends Edge {
  data?: {
    label?: string;
  };
}

export interface PipelineCanvasProps {
  engagementId: string;
  pipelineId?: string;
  initialNodes?: PipelineNode[];
  initialEdges?: PipelineEdge[];
  onPipelineChange?: (nodes: PipelineNode[], edges: PipelineEdge[]) => void;
  onSave?: (nodes: PipelineNode[], edges: PipelineEdge[]) => void;
  onCompile?: () => void;
  onExecute?: () => void;
  readOnly?: boolean;
  className?: string;
}

function PipelineCanvasInner({
  engagementId,
  pipelineId,
  initialNodes = [],
  initialEdges = [],
  onPipelineChange,
  onSave,
  onCompile,
  onExecute,
  readOnly = false,
  className,
}: PipelineCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const reactFlowInstance = useReactFlow();

  // Handle connection between nodes
  const onConnect = useCallback(
    (params: Connection) => {
      if (readOnly) return;
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            style: { strokeWidth: 2, stroke: '#52525b' },
            type: 'smoothstep',
            animated: false,
          },
          eds
        )
      );
    },
    [setEdges, readOnly]
  );

  // Notify parent of changes
  useEffect(() => {
    onPipelineChange?.(nodes as PipelineNode[], edges as PipelineEdge[]);
  }, [nodes, edges, onPipelineChange]);

  // Handle drag over for drag-and-drop
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop for drag-and-drop node creation
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      if (readOnly) return;

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode: PipelineNode = {
        id: `${type}_${Date.now()}`,
        type,
        position,
        data: {
          label: `New ${type.charAt(0).toUpperCase() + type.slice(1)}`,
          status: 'idle',
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes, readOnly]
  );

  // Get node color for minimap
  const getNodeColor = useCallback((node: Node) => {
    switch (node.type) {
      case 'source':
        return '#22c55e'; // green-500
      case 'transform':
        return '#8b5cf6'; // violet-500
      case 'destination':
        return '#3b82f6'; // blue-500
      case 'asset':
        return '#f59e0b'; // amber-500
      default:
        return '#6b7280'; // gray-500
    }
  }, []);

  // Handle save
  const handleSave = useCallback(() => {
    onSave?.(nodes as PipelineNode[], edges as PipelineEdge[]);
  }, [nodes, edges, onSave]);

  // Fit view to contents
  const handleFitView = useCallback(() => {
    reactFlowInstance.fitView({ padding: 0.2 });
  }, [reactFlowInstance]);

  return (
    <div className={cn('h-full w-full', className)}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={readOnly ? undefined : onNodesChange}
        onEdgesChange={readOnly ? undefined : onEdgesChange}
        onConnect={onConnect}
        onDragOver={onDragOver}
        onDrop={onDrop}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        className="bg-zinc-950"
        proOptions={{ hideAttribution: true }}
        deleteKeyCode={readOnly ? null : ['Backspace', 'Delete']}
        selectionKeyCode={readOnly ? null : 'Shift'}
        multiSelectionKeyCode={readOnly ? null : ['Meta', 'Control']}
      >
        {/* Controls Panel */}
        <Panel position="top-left" className="flex gap-2">
          <div className="flex items-center gap-1 rounded-lg bg-zinc-900/90 border border-zinc-800 p-1 backdrop-blur-sm">
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
              onClick={() => reactFlowInstance.zoomIn()}
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
              onClick={() => reactFlowInstance.zoomOut()}
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
              onClick={handleFitView}
            >
              <Maximize2 className="h-4 w-4" />
            </Button>
          </div>
        </Panel>

        {/* Actions Panel */}
        {!readOnly && (
          <Panel position="top-right" className="flex gap-2">
            <div className="flex items-center gap-2 rounded-lg bg-zinc-900/90 border border-zinc-800 p-2 backdrop-blur-sm">
              {onSave && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 gap-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
                  onClick={handleSave}
                >
                  <Save className="h-4 w-4" />
                  <span className="text-xs">Save</span>
                </Button>
              )}
              {onCompile && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 gap-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
                  onClick={onCompile}
                >
                  <GitBranch className="h-4 w-4" />
                  <span className="text-xs">Compile</span>
                </Button>
              )}
              {onExecute && (
                <Button
                  variant="default"
                  size="sm"
                  className="h-8 gap-2 bg-green-600 hover:bg-green-700"
                  onClick={onExecute}
                >
                  <Play className="h-4 w-4" />
                  <span className="text-xs">Execute</span>
                </Button>
              )}
            </div>
          </Panel>
        )}

        {/* Info Panel */}
        <Panel position="bottom-left">
          <div className="rounded-lg bg-zinc-900/90 border border-zinc-800 px-3 py-2 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-xs text-zinc-500">
              <Database className="h-3 w-3" />
              <span>
                {pipelineId ? `Pipeline: ${pipelineId}` : 'New Pipeline'}
              </span>
              <span className="text-zinc-700">|</span>
              <span>{nodes.length} nodes</span>
              <span className="text-zinc-700">|</span>
              <span>{edges.length} connections</span>
            </div>
          </div>
        </Panel>

        {/* Controls */}
        <Controls
          className="bg-zinc-900 border-zinc-800 [&>button]:bg-zinc-800 [&>button]:border-zinc-700 [&>button]:text-zinc-400 [&>button:hover]:bg-zinc-700"
          showZoom={false}
          showFitView={false}
        />

        {/* MiniMap */}
        <MiniMap
          className="bg-zinc-900 border-zinc-800"
          nodeColor={getNodeColor}
          maskColor="rgba(0, 0, 0, 0.7)"
          style={{
            backgroundColor: '#18181b',
          }}
        />

        {/* Background */}
        <Background
          color="#27272a"
          gap={20}
          size={1}
          variant={BackgroundVariant.Dots}
        />
      </ReactFlow>
    </div>
  );
}

export function PipelineCanvas(props: PipelineCanvasProps) {
  return (
    <ReactFlowProvider>
      <PipelineCanvasInner {...props} />
    </ReactFlowProvider>
  );
}

// Node palette for drag-and-drop
export interface NodePaletteItem {
  type: string;
  label: string;
  icon: React.ReactNode;
  description: string;
}

export function NodePalette({ className }: { className?: string }) {
  const onDragStart = useCallback(
    (event: React.DragEvent, nodeType: string) => {
      event.dataTransfer.setData('application/reactflow', nodeType);
      event.dataTransfer.effectAllowed = 'move';
    },
    []
  );

  const paletteItems: NodePaletteItem[] = [
    {
      type: 'source',
      label: 'Source',
      icon: <Database className="h-4 w-4 text-green-500" />,
      description: 'Data source extraction',
    },
    {
      type: 'transform',
      label: 'Transform',
      icon: <GitBranch className="h-4 w-4 text-violet-500" />,
      description: 'Data transformation',
    },
    {
      type: 'destination',
      label: 'Destination',
      icon: <Database className="h-4 w-4 text-blue-500" />,
      description: 'Data destination/sink',
    },
    {
      type: 'asset',
      label: 'Asset',
      icon: <Database className="h-4 w-4 text-amber-500" />,
      description: 'Generic Dagster asset',
    },
  ];

  return (
    <div
      className={cn(
        'flex flex-col gap-2 rounded-lg bg-zinc-900 border border-zinc-800 p-3',
        className
      )}
    >
      <h3 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
        Node Types
      </h3>
      <div className="flex flex-col gap-1">
        {paletteItems.map((item) => (
          <div
            key={item.type}
            draggable
            onDragStart={(e) => onDragStart(e, item.type)}
            className="flex items-center gap-2 rounded-md bg-zinc-800/50 px-3 py-2 cursor-grab hover:bg-zinc-800 transition-colors"
          >
            {item.icon}
            <div className="flex flex-col">
              <span className="text-sm font-medium text-zinc-200">
                {item.label}
              </span>
              <span className="text-xs text-zinc-500">{item.description}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
