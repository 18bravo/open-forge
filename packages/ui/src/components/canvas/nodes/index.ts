/**
 * Custom node components for the Pipeline Canvas.
 *
 * Each node type represents a different stage in a data pipeline:
 * - SourceNode: Data extraction from various sources (PostgreSQL, S3, REST APIs, CSV)
 * - TransformNode: Data transformation operations (filter, join, aggregate, map)
 * - DestinationNode: Data sinks/destinations (Knowledge Graph, databases, storage)
 * - AssetNode: Generic Dagster asset representation
 */

export { SourceNode } from './SourceNode';
export type { SourceNodeData } from './SourceNode';

export { TransformNode } from './TransformNode';
export type { TransformNodeData } from './TransformNode';

export { DestinationNode } from './DestinationNode';
export type { DestinationNodeData } from './DestinationNode';

export { AssetNode } from './AssetNode';
export type { AssetNodeData } from './AssetNode';

// Re-export node types map for ReactFlow registration
import { NodeTypes } from 'reactflow';
import { SourceNode } from './SourceNode';
import { TransformNode } from './TransformNode';
import { DestinationNode } from './DestinationNode';
import { AssetNode } from './AssetNode';

export const pipelineNodeTypes: NodeTypes = {
  source: SourceNode,
  transform: TransformNode,
  destination: DestinationNode,
  asset: AssetNode,
};
