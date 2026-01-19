# LangChain Ecosystem Integration Plan

**Date:** 2026-01-19
**Status:** Proposed
**Target Gate:** Gate 8 (Post-Testing & Hardening)
**Estimated Duration:** 4-6 weeks

---

## Executive Summary

This plan integrates the complete LangChain ecosystem into Open Forge, replacing custom implementations with battle-tested components and adding visual canvas interfaces for AI-agent orchestration and pipeline design. The approach follows an "AI-generates, user-refines" paradigm where autonomous agents create workflows that users can visually adjust.

### Key Integration Points

| Component | Current State | Target State |
|-----------|---------------|--------------|
| Agent Canvas | None | Langflow integration |
| Pipeline Canvas | None | Custom React Flow + Dagster |
| Memory (Short-term) | Custom PostgreSQL | LangGraph PostgresSaver |
| Memory (Long-term) | Custom implementation | PostgresStore + pgvector |
| Observability | Jaeger tracing | LangSmith (self-hosted option) |
| Tool Extensibility | Custom tool framework | MCP Adapters |
| Agent Patterns | Custom agents | create_supervisor + create_react_agent |

---

## Architectural Changes

### Current Architecture (Gate 6)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: PRESENTATION                                                        │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                 │
│ │ Customer Portal │ │ Admin Dashboard │ │ Approval UI     │                 │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ LAYER 2: API GATEWAY                                                         │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ FastAPI Gateway (REST + GraphQL + SSE)                                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ LAYER 3: ORCHESTRATION                                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ LangGraph Orchestrator + Custom State Manager + Custom Memory           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ LAYER 4: AGENT CLUSTERS                                                      │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐      │
│ │ Discovery │ │ Data      │ │ App       │ │ Enablemt  │ │ Operations│      │
│ │ (Custom)  │ │ Architect │ │ Builder   │ │ (Custom)  │ │ (Custom)  │      │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Target Architecture (Post-Gate 8)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: PRESENTATION                                                        │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│ │ Customer    │ │ Admin       │ │ Approval    │ │ Visual Canvases         │ │
│ │ Portal      │ │ Dashboard   │ │ UI          │ │ ┌─────────┐ ┌─────────┐ │ │
│ │             │ │             │ │             │ │ │ Agent   │ │Pipeline │ │ │
│ │             │ │             │ │             │ │ │ Canvas  │ │Canvas   │ │ │
│ │             │ │             │ │             │ │ │(Langflw)│ │(RFlow)  │ │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ │ └─────────┘ └─────────┘ │ │
│                                                 └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ LAYER 2: API GATEWAY                                                         │
│ ┌───────────────────────────────────────┐ ┌───────────────────────────────┐ │
│ │ FastAPI Gateway (REST + GraphQL + SSE)│ │ LangSmith Observability       │ │
│ └───────────────────────────────────────┘ └───────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ LAYER 3: ORCHESTRATION                                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ LangGraph Orchestrator (create_supervisor pattern)                      │ │
│ │ ┌──────────────────────────────┐ ┌──────────────────────────────┐       │ │
│ │ │ PostgresSaver (Short-term)   │ │ PostgresStore (Long-term)    │       │ │
│ │ │ Thread checkpoints           │ │ Cross-thread memory + RAG    │       │ │
│ │ └──────────────────────────────┘ └──────────────────────────────┘       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ LAYER 4: AGENT CLUSTERS                                                      │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐      │
│ │ Discovery │ │ Data      │ │ App       │ │ Enablemt  │ │ Operations│      │
│ │(ReAct)    │ │ Architect │ │ Builder   │ │ (ReAct)   │ │ (ReAct)   │      │
│ │           │ │ (ReAct)   │ │ (ReAct)   │ │           │ │           │      │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘      │
├─────────────────────────────────────────────────────────────────────────────┤
│ LAYER 5: TOOL LAYER                                                          │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ MCP Adapters (langchain-mcp-adapters)                                   │ │
│ │ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │ │
│ │ │ File Tools │ │ DB Tools   │ │ API Tools  │ │ Custom MCP │            │ │
│ │ └────────────┘ └────────────┘ └────────────┘ └────────────┘            │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Work Packages

### WP1: Visual Agent Canvas (Langflow Integration)

**Duration:** 2 weeks
**Dependencies:** None (can start immediately)
**Owner:** UI/Frontend Team

#### Objective

Integrate Langflow as an embedded visual canvas for designing and refining AI agent workflows. Agents generate initial workflows; users can visually adjust nodes, connections, and parameters.

#### Rationale: Why Langflow (Not Custom React Flow)

| Consideration | Langflow | Custom React Flow |
|---------------|----------|-------------------|
| LangGraph native | Yes - built-in support | Requires custom integration |
| Agent components | Pre-built library | Must build from scratch |
| Time to value | Days | Weeks-months |
| Maintenance | Community maintained | Full internal ownership |
| Export format | Native LangGraph JSON | Custom format needed |

#### Implementation Tasks

**1.1 Langflow Deployment**
```yaml
# infrastructure/docker/docker-compose.langflow.yml
services:
  langflow:
    image: langflowai/langflow:latest
    environment:
      - LANGFLOW_DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/langflow
      - LANGFLOW_CONFIG_DIR=/app/config
      - LANGFLOW_AUTO_LOGIN=false
      - LANGFLOW_SUPERUSER=${LANGFLOW_SUPERUSER}
      - LANGFLOW_SUPERUSER_PASSWORD=${LANGFLOW_SUPERUSER_PASSWORD}
    ports:
      - "7860:7860"
    volumes:
      - langflow_data:/app/data
      - ./langflow-config:/app/config
    depends_on:
      - postgres
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**1.2 Open Forge Custom Components**

Create custom Langflow components for Open Forge-specific functionality:

```
packages/langflow-components/
├── __init__.py
├── agents/
│   ├── discovery_agent.py      # Wrap Discovery cluster agents
│   ├── data_architect_agent.py # Wrap Data Architect agents
│   ├── app_builder_agent.py    # Wrap App Builder agents
│   └── operations_agent.py     # Wrap Operations agents
├── tools/
│   ├── ontology_tool.py        # Query/modify ontology
│   ├── pipeline_tool.py        # Trigger/monitor pipelines
│   └── connector_tool.py       # Data source operations
└── memory/
    └── postgres_memory.py      # PostgresStore component
```

Example custom component:

```python
# packages/langflow-components/agents/discovery_agent.py
from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Message

class DiscoveryAgentComponent(Component):
    """Open Forge Discovery Agent for Langflow."""

    display_name = "Discovery Agent"
    description = "Stakeholder discovery and requirements gathering agent"
    icon = "search"

    inputs = [
        MessageTextInput(
            name="input_text",
            display_name="Input",
            info="The stakeholder context or question to analyze",
        ),
        StrInput(
            name="engagement_id",
            display_name="Engagement ID",
            info="The Open Forge engagement context",
        ),
    ]

    outputs = [
        Output(display_name="Discovery Results", name="output", method="run_agent"),
    ]

    async def run_agent(self) -> Message:
        from packages.agents.src.agents.discovery import DiscoveryCluster

        cluster = DiscoveryCluster(engagement_id=self.engagement_id)
        result = await cluster.execute(self.input_text)

        return Message(text=result.model_dump_json())
```

**1.3 Embedding in Open Forge UI**

```typescript
// packages/ui/src/components/canvas/AgentCanvas.tsx
import { useEffect, useRef } from 'react';

interface AgentCanvasProps {
  engagementId: string;
  initialFlow?: object;
  onFlowChange?: (flow: object) => void;
  readOnly?: boolean;
}

export function AgentCanvas({
  engagementId,
  initialFlow,
  onFlowChange,
  readOnly = false
}: AgentCanvasProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    // Establish postMessage communication with Langflow
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'LANGFLOW_FLOW_UPDATED') {
        onFlowChange?.(event.data.flow);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onFlowChange]);

  const langflowUrl = `/langflow/flow/${engagementId}?embed=true&readonly=${readOnly}`;

  return (
    <div className="h-full w-full rounded-lg border border-zinc-800 overflow-hidden">
      <iframe
        ref={iframeRef}
        src={langflowUrl}
        className="h-full w-full"
        title="Agent Workflow Canvas"
      />
    </div>
  );
}
```

**1.4 API Bridge**

```python
# packages/api/src/api/routers/canvas.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/canvas", tags=["canvas"])

class FlowExportRequest(BaseModel):
    engagement_id: str
    flow_id: str

class FlowImportRequest(BaseModel):
    engagement_id: str
    flow_data: dict

@router.post("/agent/export")
async def export_agent_flow(request: FlowExportRequest):
    """Export Langflow flow to LangGraph-compatible format."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://langflow:7860/api/v1/flows/{request.flow_id}"
        )

    flow_data = response.json()

    # Convert to Open Forge internal format
    langgraph_config = convert_langflow_to_langgraph(flow_data)

    return {"langgraph_config": langgraph_config}

@router.post("/agent/import")
async def import_agent_flow(request: FlowImportRequest):
    """Import AI-generated flow into Langflow for user refinement."""
    # Convert from internal format to Langflow
    langflow_data = convert_langgraph_to_langflow(request.flow_data)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://langflow:7860/api/v1/flows/",
            json=langflow_data
        )

    return {"flow_id": response.json()["id"]}
```

#### Acceptance Criteria

- [ ] Langflow running as Docker service
- [ ] Custom Open Forge components registered
- [ ] Canvas embedded in UI with iframe communication
- [ ] AI-generated flows importable into canvas
- [ ] User-modified flows exportable to LangGraph format
- [ ] Authentication SSO between Open Forge and Langflow

---

### WP2: Visual Pipeline Canvas (React Flow + Dagster)

**Duration:** 2-3 weeks
**Dependencies:** None (can start in parallel with WP1)
**Owner:** UI/Frontend Team + Pipeline Team

#### Objective

Build a custom visual canvas for designing data pipelines using React Flow, with Dagster as the execution backend. This cannot use Langflow because Langflow doesn't understand Dagster's asset-based paradigm.

#### Implementation Tasks

**2.1 React Flow Canvas Component**

```typescript
// packages/ui/src/components/canvas/PipelineCanvas.tsx
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
} from 'reactflow';
import 'reactflow/dist/style.css';

import { SourceNode } from './nodes/SourceNode';
import { TransformNode } from './nodes/TransformNode';
import { DestinationNode } from './nodes/DestinationNode';
import { AssetNode } from './nodes/AssetNode';

const nodeTypes: NodeTypes = {
  source: SourceNode,
  transform: TransformNode,
  destination: DestinationNode,
  asset: AssetNode,
};

interface PipelineCanvasProps {
  engagementId: string;
  pipelineId?: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onPipelineChange?: (nodes: Node[], edges: Edge[]) => void;
  readOnly?: boolean;
}

export function PipelineCanvas({
  engagementId,
  pipelineId,
  initialNodes = [],
  initialEdges = [],
  onPipelineChange,
  readOnly = false,
}: PipelineCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge(params, eds));
    },
    [setEdges]
  );

  useEffect(() => {
    onPipelineChange?.(nodes, edges);
  }, [nodes, edges, onPipelineChange]);

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={readOnly ? undefined : onNodesChange}
        onEdgesChange={readOnly ? undefined : onEdgesChange}
        onConnect={readOnly ? undefined : onConnect}
        nodeTypes={nodeTypes}
        fitView
        className="bg-zinc-950"
      >
        <Controls className="bg-zinc-800 border-zinc-700" />
        <MiniMap
          className="bg-zinc-900"
          nodeColor={(node) => {
            switch (node.type) {
              case 'source': return '#22c55e';
              case 'transform': return '#8b5cf6';
              case 'destination': return '#3b82f6';
              default: return '#6b7280';
            }
          }}
        />
        <Background color="#27272a" gap={16} />
      </ReactFlow>
    </div>
  );
}
```

**2.2 Custom Node Types**

```typescript
// packages/ui/src/components/canvas/nodes/SourceNode.tsx
import { Handle, Position, NodeProps } from 'reactflow';
import { Database, Cloud, FileSpreadsheet } from 'lucide-react';

interface SourceNodeData {
  label: string;
  connectorType: 'postgresql' | 's3' | 'rest' | 'csv';
  config: Record<string, any>;
  status?: 'idle' | 'running' | 'success' | 'error';
}

export function SourceNode({ data, selected }: NodeProps<SourceNodeData>) {
  const icons = {
    postgresql: Database,
    s3: Cloud,
    rest: Cloud,
    csv: FileSpreadsheet,
  };

  const Icon = icons[data.connectorType] || Database;

  return (
    <div className={`
      px-4 py-3 rounded-lg border-2 min-w-[180px]
      bg-zinc-900
      ${selected ? 'border-green-500' : 'border-green-500/50'}
      ${data.status === 'running' ? 'animate-pulse' : ''}
    `}>
      <div className="flex items-center gap-2">
        <Icon className="w-5 h-5 text-green-500" />
        <span className="font-medium text-zinc-100">{data.label}</span>
      </div>
      <div className="text-xs text-zinc-500 mt-1">
        {data.connectorType.toUpperCase()}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-green-500 border-2 border-zinc-900"
      />
    </div>
  );
}
```

**2.3 Pipeline-to-Dagster Compiler**

```python
# packages/pipelines/src/canvas/compiler.py
from typing import List, Dict, Any
from dataclasses import dataclass
from dagster import (
    asset,
    AssetIn,
    AssetKey,
    Definitions,
    define_asset_job,
)

@dataclass
class CanvasNode:
    id: str
    type: str  # source, transform, destination, asset
    data: Dict[str, Any]
    position: Dict[str, float]

@dataclass
class CanvasEdge:
    id: str
    source: str
    target: str
    source_handle: str
    target_handle: str

class PipelineCanvasCompiler:
    """Compile React Flow canvas to Dagster assets."""

    def compile(
        self,
        nodes: List[CanvasNode],
        edges: List[CanvasEdge],
        engagement_id: str
    ) -> Definitions:
        """Convert canvas representation to Dagster Definitions."""

        # Build dependency graph
        dependencies = self._build_dependencies(nodes, edges)

        # Generate assets
        assets = []
        for node in nodes:
            if node.type == 'source':
                assets.append(self._create_source_asset(node, engagement_id))
            elif node.type == 'transform':
                deps = dependencies.get(node.id, [])
                assets.append(
                    self._create_transform_asset(node, deps, engagement_id)
                )
            elif node.type == 'destination':
                deps = dependencies.get(node.id, [])
                assets.append(
                    self._create_destination_asset(node, deps, engagement_id)
                )

        # Create job
        job = define_asset_job(
            name=f"canvas_pipeline_{engagement_id}",
            selection=assets,
        )

        return Definitions(
            assets=assets,
            jobs=[job],
        )

    def _create_source_asset(self, node: CanvasNode, engagement_id: str):
        """Create a Dagster source asset from canvas node."""

        connector_type = node.data.get('connectorType')
        config = node.data.get('config', {})

        @asset(
            name=f"{engagement_id}_{node.id}",
            group_name=engagement_id,
            metadata={
                "canvas_node_id": node.id,
                "connector_type": connector_type,
            }
        )
        def source_asset():
            from packages.connectors import get_connector

            connector = get_connector(connector_type)
            connector.connect(config)
            return connector.extract()

        return source_asset

    def _create_transform_asset(
        self,
        node: CanvasNode,
        dependencies: List[str],
        engagement_id: str
    ):
        """Create a Dagster transform asset."""

        ins = {
            dep: AssetIn(key=AssetKey([f"{engagement_id}_{dep}"]))
            for dep in dependencies
        }

        transform_config = node.data.get('transform', {})

        @asset(
            name=f"{engagement_id}_{node.id}",
            ins=ins,
            group_name=engagement_id,
            metadata={
                "canvas_node_id": node.id,
                "transform_type": transform_config.get('type'),
            }
        )
        def transform_asset(**inputs):
            import polars as pl

            # Combine inputs
            dfs = list(inputs.values())
            if len(dfs) == 1:
                df = dfs[0]
            else:
                df = pl.concat(dfs)

            # Apply transformation
            return apply_transform(df, transform_config)

        return transform_asset
```

**2.4 AI-to-Canvas Generator**

```python
# packages/pipelines/src/canvas/generator.py
from typing import List, Dict, Any
from packages.ontology.models import OntologyDefinition

class PipelineCanvasGenerator:
    """Generate visual canvas layout from AI agent output."""

    def generate_from_ontology(
        self,
        ontology: OntologyDefinition,
        source_mappings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate React Flow nodes/edges from ontology and source mappings."""

        nodes = []
        edges = []

        # Calculate layout positions
        y_offset = 0
        source_x = 100
        transform_x = 400
        destination_x = 700

        # Create source nodes
        for i, mapping in enumerate(source_mappings):
            node_id = f"source_{i}"
            nodes.append({
                "id": node_id,
                "type": "source",
                "position": {"x": source_x, "y": y_offset + (i * 150)},
                "data": {
                    "label": mapping["source_name"],
                    "connectorType": mapping["connector_type"],
                    "config": mapping["config"],
                }
            })

        # Create transform nodes for each object type
        for i, obj_type in enumerate(ontology.object_types):
            node_id = f"transform_{obj_type.name}"
            nodes.append({
                "id": node_id,
                "type": "transform",
                "position": {"x": transform_x, "y": y_offset + (i * 150)},
                "data": {
                    "label": f"Transform: {obj_type.name}",
                    "objectType": obj_type.name,
                    "transform": {
                        "type": "ontology_mapping",
                        "schema": obj_type.model_dump(),
                    }
                }
            })

            # Connect sources to transforms based on mappings
            for j, mapping in enumerate(source_mappings):
                if mapping.get("target_type") == obj_type.name:
                    edges.append({
                        "id": f"edge_source_{j}_to_{node_id}",
                        "source": f"source_{j}",
                        "target": node_id,
                    })

        # Create destination node (graph sync)
        nodes.append({
            "id": "destination_graph",
            "type": "destination",
            "position": {"x": destination_x, "y": y_offset + 75},
            "data": {
                "label": "Knowledge Graph",
                "destinationType": "graph",
            }
        })

        # Connect all transforms to destination
        for obj_type in ontology.object_types:
            edges.append({
                "id": f"edge_transform_{obj_type.name}_to_graph",
                "source": f"transform_{obj_type.name}",
                "target": "destination_graph",
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }
```

#### Acceptance Criteria

- [ ] React Flow canvas renders with custom node types
- [ ] Nodes can be dragged, connected, and configured
- [ ] Canvas state compiles to valid Dagster definitions
- [ ] AI-generated pipelines render in canvas
- [ ] User modifications persist and execute correctly
- [ ] Pipeline execution status reflects in node visual state

---

### WP3: LangGraph Memory Migration

**Duration:** 1-2 weeks
**Dependencies:** None
**Owner:** Backend/Orchestration Team

#### Objective

Replace custom memory implementation with LangGraph's native memory system:
- **PostgresSaver** for short-term, within-thread checkpointing
- **PostgresStore** + pgvector for long-term, cross-thread memory with semantic search

#### Current State Analysis

The existing `orchestrator.py` already uses `PostgresSaver`:

```python
# Current (in orchestration/orchestrator.py)
from langgraph.checkpoint.postgres import PostgresSaver
self.checkpointer = PostgresSaver.from_conn_string(db_connection_string)
```

**What's Missing:**
1. Long-term memory store (PostgresStore)
2. Semantic search capability (pgvector integration)
3. Memory namespacing per engagement
4. Cross-thread memory sharing

#### Implementation Tasks

**3.1 PostgresStore Setup**

```python
# packages/agent-framework/src/memory/long_term.py
from langgraph.store.postgres import PostgresStore
from typing import Optional, Dict, Any, List
import uuid

class EngagementMemoryStore:
    """Long-term memory store for engagement context."""

    def __init__(self, connection_string: str):
        self.store = PostgresStore.from_conn_string(
            connection_string,
            index={
                "dims": 1536,  # OpenAI embedding dimensions
                "embed": self._get_embeddings,
            }
        )

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for semantic search."""
        from langchain_openai import OpenAIEmbeddings
        embeddings = OpenAIEmbeddings()
        return embeddings.embed_documents(texts)

    async def store_memory(
        self,
        engagement_id: str,
        memory_type: str,  # 'stakeholder', 'requirement', 'decision', etc.
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a memory item with semantic indexing."""

        namespace = ("engagements", engagement_id, memory_type)
        key = str(uuid.uuid4())

        # Create searchable text from content
        search_text = self._content_to_text(content)

        await self.store.aput(
            namespace=namespace,
            key=key,
            value={
                "content": content,
                "metadata": metadata or {},
                "search_text": search_text,
            }
        )

        return key

    async def search_memories(
        self,
        engagement_id: str,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Semantic search across engagement memories."""

        if memory_types:
            # Search specific types
            results = []
            for mtype in memory_types:
                namespace = ("engagements", engagement_id, mtype)
                items = await self.store.asearch(
                    namespace=namespace,
                    query=query,
                    limit=limit,
                )
                results.extend(items)
            return sorted(results, key=lambda x: x.score, reverse=True)[:limit]
        else:
            # Search all engagement memories
            namespace = ("engagements", engagement_id)
            return await self.store.asearch(
                namespace=namespace,
                query=query,
                limit=limit,
            )

    async def get_memories_by_type(
        self,
        engagement_id: str,
        memory_type: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all memories of a specific type."""

        namespace = ("engagements", engagement_id, memory_type)
        items = await self.store.alist(namespace=namespace, limit=limit)
        return [item.value for item in items]

    def _content_to_text(self, content: Dict[str, Any]) -> str:
        """Convert structured content to searchable text."""
        parts = []
        for key, value in content.items():
            if isinstance(value, str):
                parts.append(f"{key}: {value}")
            elif isinstance(value, list):
                parts.append(f"{key}: {', '.join(str(v) for v in value)}")
        return " | ".join(parts)
```

**3.2 Memory-Aware Agent Base Class**

```python
# packages/agent-framework/src/agents/base_memory_agent.py
from langgraph.prebuilt import create_react_agent
from langgraph.store.postgres import PostgresStore
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.tools import tool
from typing import List, Dict, Any

class MemoryAwareAgent:
    """Base class for agents with memory capabilities."""

    def __init__(
        self,
        llm,
        checkpointer: PostgresSaver,
        store: PostgresStore,
        engagement_id: str,
        agent_id: str,
    ):
        self.llm = llm
        self.checkpointer = checkpointer
        self.store = store
        self.engagement_id = engagement_id
        self.agent_id = agent_id

        # Create memory tools
        self.memory_tools = self._create_memory_tools()

        # Build agent with memory
        self.agent = create_react_agent(
            model=llm,
            tools=self.get_tools() + self.memory_tools,
            checkpointer=checkpointer,
            store=store,
        )

    def _create_memory_tools(self) -> List:
        """Create tools for memory operations."""

        store = self.store
        engagement_id = self.engagement_id

        @tool
        async def remember(
            content: str,
            memory_type: str = "general"
        ) -> str:
            """Store important information for future reference.

            Args:
                content: The information to remember
                memory_type: Category of memory (stakeholder, requirement, decision, etc.)
            """
            namespace = ("engagements", engagement_id, memory_type)
            key = str(uuid.uuid4())
            await store.aput(namespace, key, {"content": content})
            return f"Stored memory: {key}"

        @tool
        async def recall(
            query: str,
            memory_type: str = None,
            limit: int = 5
        ) -> str:
            """Search past memories for relevant information.

            Args:
                query: What to search for
                memory_type: Optional category to search within
                limit: Maximum results to return
            """
            if memory_type:
                namespace = ("engagements", engagement_id, memory_type)
            else:
                namespace = ("engagements", engagement_id)

            results = await store.asearch(namespace, query=query, limit=limit)

            if not results:
                return "No relevant memories found."

            return "\n".join([
                f"- {r.value.get('content', str(r.value))}"
                for r in results
            ])

        return [remember, recall]

    def get_tools(self) -> List:
        """Override in subclasses to provide agent-specific tools."""
        return []

    async def run(self, input_message: str, thread_id: str) -> Dict[str, Any]:
        """Execute the agent with memory context."""

        config = {
            "configurable": {
                "thread_id": thread_id,
                "engagement_id": self.engagement_id,
            }
        }

        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": input_message}]},
            config=config,
        )

        return result
```

**3.3 Migration Script**

```python
# scripts/migrate_memory.py
"""Migrate existing custom memory to LangGraph PostgresStore."""
import asyncio
from packages.core.database import get_session
from packages.agent_framework.memory.long_term import EngagementMemoryStore

async def migrate_memories():
    """Migrate old memory format to new PostgresStore format."""

    # Connect to old system
    async with get_session() as session:
        # Fetch all engagements
        result = await session.execute(
            "SELECT id, state FROM engagements.engagements"
        )
        engagements = result.fetchall()

    # Initialize new store
    store = EngagementMemoryStore(connection_string)

    for engagement_id, state in engagements:
        # Migrate stakeholders
        for stakeholder in state.get('stakeholders', []):
            await store.store_memory(
                engagement_id=engagement_id,
                memory_type='stakeholder',
                content=stakeholder,
            )

        # Migrate decisions
        for decision in state.get('agent_decisions', []):
            await store.store_memory(
                engagement_id=engagement_id,
                memory_type='decision',
                content=decision,
            )

        # Migrate requirements
        for req in state.get('use_cases', []):
            await store.store_memory(
                engagement_id=engagement_id,
                memory_type='requirement',
                content=req,
            )

        print(f"Migrated engagement {engagement_id}")

if __name__ == "__main__":
    asyncio.run(migrate_memories())
```

#### Acceptance Criteria

- [ ] PostgresStore initialized with pgvector indexing
- [ ] Memory tools available to all agents
- [ ] Semantic search returns relevant results
- [ ] Cross-thread memory sharing works
- [ ] Migration script runs without data loss
- [ ] Memory-aware agents can remember and recall

---

### WP4: Agent Pattern Refactoring

**Duration:** 2 weeks
**Dependencies:** WP3 (Memory Migration)
**Owner:** Backend/Agent Team

#### Objective

Refactor existing agents to use LangGraph prebuilt patterns:
- **Orchestrator**: Use `create_supervisor` pattern
- **Specialist Agents**: Use `create_react_agent` pattern

#### Implementation Tasks

**4.1 Supervisor-Based Orchestrator**

```python
# packages/orchestration/src/supervisor_orchestrator.py
from langgraph.prebuilt import create_supervisor
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langchain_anthropic import ChatAnthropic

from packages.agents.discovery import DiscoveryAgent
from packages.agents.data_architect import DataArchitectAgent
from packages.agents.app_builder import AppBuilderAgent
from packages.agents.operations import OperationsAgent
from packages.agents.enablement import EnablementAgent

class SupervisorOrchestrator:
    """
    Multi-agent orchestrator using LangGraph supervisor pattern.

    The supervisor routes tasks to specialist agents and coordinates
    the overall engagement workflow.
    """

    def __init__(
        self,
        connection_string: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.llm = ChatAnthropic(model=model, temperature=0)

        # Initialize persistence
        self.checkpointer = PostgresSaver.from_conn_string(connection_string)
        self.store = PostgresStore.from_conn_string(connection_string)

        # Initialize specialist agents
        self.agents = {
            "discovery": DiscoveryAgent(self.llm, self.checkpointer, self.store),
            "data_architect": DataArchitectAgent(self.llm, self.checkpointer, self.store),
            "app_builder": AppBuilderAgent(self.llm, self.checkpointer, self.store),
            "operations": OperationsAgent(self.llm, self.checkpointer, self.store),
            "enablement": EnablementAgent(self.llm, self.checkpointer, self.store),
        }

        # Build supervisor graph
        self.graph = self._build_supervisor()

    def _build_supervisor(self):
        """Build the supervisor graph."""

        supervisor = create_supervisor(
            agents=list(self.agents.values()),
            model=self.llm,
            prompt=self._get_supervisor_prompt(),
            checkpointer=self.checkpointer,
            output_mode="last_message",
        )

        return supervisor.compile()

    def _get_supervisor_prompt(self) -> str:
        return """You are the orchestrator for an FDE (Forward Deployed Engineering) engagement.

Your job is to coordinate specialist agents to complete the engagement:

1. **Discovery Agent**: Gathers requirements, interviews stakeholders, identifies data sources
2. **Data Architect Agent**: Designs ontology, schemas, and data transformations
3. **App Builder Agent**: Generates applications, UIs, and APIs
4. **Operations Agent**: Sets up monitoring, scaling, and maintenance
5. **Enablement Agent**: Creates documentation, training, and support materials

Current engagement phase: {current_phase}
Engagement status: {status}

Route tasks to the appropriate agent based on the current phase and needs.
Ensure human approvals are obtained at phase transitions.
"""

    async def run_engagement(
        self,
        engagement_id: str,
        input_message: str
    ) -> dict:
        """Run the supervisor with engagement context."""

        config = {
            "configurable": {
                "thread_id": engagement_id,
            }
        }

        result = await self.graph.ainvoke(
            {"messages": [{"role": "user", "content": input_message}]},
            config=config,
        )

        return result
```

**4.2 ReAct Agent Implementation**

```python
# packages/agents/src/agents/discovery/react_agent.py
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from typing import List, Dict, Any

class DiscoveryReActAgent:
    """Discovery agent using ReAct pattern."""

    def __init__(self, llm, checkpointer, store):
        self.llm = llm
        self.checkpointer = checkpointer
        self.store = store

        self.agent = create_react_agent(
            model=llm,
            tools=self._get_tools(),
            checkpointer=checkpointer,
            store=store,
            state_modifier=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        return """You are a Discovery Agent specializing in stakeholder analysis and requirements gathering.

Your capabilities:
1. Interview stakeholders to understand their needs
2. Analyze existing data sources and systems
3. Document business processes and workflows
4. Identify success criteria and KPIs

Always:
- Ask clarifying questions when requirements are ambiguous
- Document all stakeholder interactions
- Prioritize requirements based on business impact
- Flag any risks or blockers

Use the provided tools to:
- Store stakeholder information (remember tool)
- Search past conversations (recall tool)
- Query connected data sources (query_source tool)
"""

    def _get_tools(self) -> List:
        """Define discovery-specific tools."""

        @tool
        async def interview_stakeholder(
            stakeholder_name: str,
            questions: List[str]
        ) -> str:
            """Conduct a structured interview with a stakeholder.

            Args:
                stakeholder_name: Name/role of the stakeholder
                questions: List of questions to ask
            """
            # In production, this would send questions via the UI
            # and wait for responses
            return f"Interview scheduled with {stakeholder_name}"

        @tool
        async def analyze_data_source(
            source_name: str,
            connection_config: Dict[str, Any]
        ) -> str:
            """Analyze a data source to understand its schema and content.

            Args:
                source_name: Name identifier for the source
                connection_config: Connection parameters
            """
            from packages.connectors import get_connector

            connector = get_connector(connection_config['type'])
            await connector.connect(connection_config)

            schema = await connector.get_schema()
            profile = await connector.profile(connection_config.get('table'))

            return f"Schema: {schema}\n\nProfile: {profile}"

        @tool
        async def document_requirement(
            requirement_type: str,
            description: str,
            priority: str,
            stakeholder: str
        ) -> str:
            """Document a discovered requirement.

            Args:
                requirement_type: Type (functional, non-functional, constraint)
                description: Detailed description
                priority: Priority level (high, medium, low)
                stakeholder: Who requested this
            """
            # Store in memory for future reference
            return f"Requirement documented: {description[:50]}..."

        return [interview_stakeholder, analyze_data_source, document_requirement]
```

**4.3 Agent Registry Update**

```python
# packages/orchestration/src/registry/agent_registry.py
from typing import Dict, Type, Any
from packages.agents.base import MemoryAwareAgent

class AgentRegistry:
    """Registry for discovering and instantiating agents."""

    _agents: Dict[str, Type[MemoryAwareAgent]] = {}

    @classmethod
    def register(cls, agent_id: str):
        """Decorator to register an agent class."""
        def decorator(agent_class: Type[MemoryAwareAgent]):
            cls._agents[agent_id] = agent_class
            return agent_class
        return decorator

    @classmethod
    def get_agent(
        cls,
        agent_id: str,
        llm,
        checkpointer,
        store,
        **kwargs
    ) -> MemoryAwareAgent:
        """Instantiate a registered agent."""
        if agent_id not in cls._agents:
            raise ValueError(f"Agent {agent_id} not registered")

        return cls._agents[agent_id](
            llm=llm,
            checkpointer=checkpointer,
            store=store,
            **kwargs
        )

    @classmethod
    def list_agents(cls) -> Dict[str, Dict[str, Any]]:
        """List all registered agents with metadata."""
        return {
            agent_id: {
                "name": agent_class.__name__,
                "description": agent_class.__doc__,
            }
            for agent_id, agent_class in cls._agents.items()
        }

# Usage:
@AgentRegistry.register("discovery")
class DiscoveryAgent(MemoryAwareAgent):
    """Agent for stakeholder discovery and requirements gathering."""
    pass
```

#### Acceptance Criteria

- [ ] Supervisor orchestrator routes to correct agents
- [ ] ReAct agents complete tasks autonomously
- [ ] Agent handoffs preserve context
- [ ] Human-in-the-loop interrupts work correctly
- [ ] Agent registry discovers all agents
- [ ] Existing tests pass with new patterns

---

### WP5: LangSmith Integration

**Duration:** 1 week
**Dependencies:** WP4 (Agent Patterns)
**Owner:** DevOps/Observability Team

#### Objective

Integrate LangSmith for comprehensive observability, tracing, and evaluation of agent workflows.

#### Implementation Tasks

**5.1 LangSmith Configuration**

```python
# packages/core/src/observability/langsmith.py
import os
from functools import wraps
from langsmith import Client
from langsmith.run_trees import RunTree

# Environment configuration
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "open-forge"

# For self-hosted LangSmith
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv(
    "LANGSMITH_ENDPOINT",
    "https://api.smith.langchain.com"
)

class LangSmithObservability:
    """LangSmith integration for Open Forge."""

    def __init__(self):
        self.client = Client()

    def trace_engagement(self, engagement_id: str):
        """Decorator to trace an entire engagement workflow."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                with RunTree(
                    name=f"engagement_{engagement_id}",
                    run_type="chain",
                    project_name="open-forge",
                    tags=[f"engagement:{engagement_id}"],
                ) as rt:
                    result = await func(*args, **kwargs)
                    rt.end(outputs={"result": str(result)})
                    return result
            return wrapper
        return decorator

    def trace_agent(self, agent_id: str):
        """Decorator to trace agent execution."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                with RunTree(
                    name=f"agent_{agent_id}",
                    run_type="agent",
                    tags=[f"agent:{agent_id}"],
                ) as rt:
                    result = await func(*args, **kwargs)
                    rt.end(outputs={"result": str(result)})
                    return result
            return wrapper
        return decorator

    async def log_feedback(
        self,
        run_id: str,
        score: float,
        comment: str = None
    ):
        """Log human feedback for a run."""
        self.client.create_feedback(
            run_id=run_id,
            key="human_feedback",
            score=score,
            comment=comment,
        )

    async def get_engagement_traces(
        self,
        engagement_id: str,
        limit: int = 100
    ):
        """Get all traces for an engagement."""
        runs = self.client.list_runs(
            project_name="open-forge",
            filter=f'has(tags, "engagement:{engagement_id}")',
            limit=limit,
        )
        return list(runs)
```

**5.2 Self-Hosted LangSmith (Optional)**

```yaml
# infrastructure/docker/docker-compose.langsmith.yml
services:
  langsmith-backend:
    image: langchain/langsmith-backend:latest
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/langsmith
      - REDIS_URL=redis://redis:6379
      - LANGSMITH_LICENSE_KEY=${LANGSMITH_LICENSE_KEY}
    ports:
      - "1984:1984"
    depends_on:
      - postgres
      - redis

  langsmith-frontend:
    image: langchain/langsmith-frontend:latest
    environment:
      - BACKEND_URL=http://langsmith-backend:1984
    ports:
      - "3001:80"
    depends_on:
      - langsmith-backend

  langsmith-queue:
    image: langchain/langsmith-queue:latest
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/langsmith
      - REDIS_URL=redis://redis:6379
    depends_on:
      - langsmith-backend
```

**5.3 Dashboard Integration**

```typescript
// packages/ui/src/components/observability/LangSmithEmbed.tsx
interface LangSmithEmbedProps {
  engagementId: string;
  runId?: string;
}

export function LangSmithEmbed({ engagementId, runId }: LangSmithEmbedProps) {
  const langsmithUrl = process.env.NEXT_PUBLIC_LANGSMITH_URL || 'https://smith.langchain.com';

  const embedUrl = runId
    ? `${langsmithUrl}/runs/${runId}?embed=true`
    : `${langsmithUrl}/projects/open-forge?filter=engagement:${engagementId}&embed=true`;

  return (
    <div className="h-full w-full rounded-lg border border-zinc-800 overflow-hidden">
      <iframe
        src={embedUrl}
        className="h-full w-full"
        title="LangSmith Traces"
      />
    </div>
  );
}
```

#### Acceptance Criteria

- [ ] All agent runs traced in LangSmith
- [ ] Engagement-level trace grouping works
- [ ] Human feedback logged correctly
- [ ] Dashboard shows embedded traces
- [ ] Self-hosted option documented and tested

---

### WP6: MCP Adapters Integration

**Duration:** 1 week
**Dependencies:** WP4 (Agent Patterns)
**Owner:** Backend/Tools Team

#### Objective

Integrate Model Context Protocol (MCP) adapters for extensible tool capabilities, allowing Open Forge to use any MCP-compatible tool server.

#### Implementation Tasks

**6.1 MCP Client Setup**

```python
# packages/agent-framework/src/tools/mcp_adapter.py
from langchain_mcp_adapters import MCPToolkit
from langchain_core.tools import BaseTool
from typing import List, Optional
import asyncio

class MCPToolProvider:
    """Provides tools from MCP servers to Open Forge agents."""

    def __init__(self):
        self._toolkits: dict[str, MCPToolkit] = {}

    async def connect_server(
        self,
        server_name: str,
        command: List[str],
        args: Optional[List[str]] = None,
        env: Optional[dict] = None
    ) -> List[BaseTool]:
        """Connect to an MCP server and get its tools."""

        toolkit = MCPToolkit(
            command=command,
            args=args or [],
            env=env or {},
        )

        await toolkit.initialize()
        self._toolkits[server_name] = toolkit

        return toolkit.get_tools()

    async def connect_filesystem(self, allowed_paths: List[str]) -> List[BaseTool]:
        """Connect to the filesystem MCP server."""
        return await self.connect_server(
            server_name="filesystem",
            command=["npx", "-y", "@modelcontextprotocol/server-filesystem"],
            args=allowed_paths,
        )

    async def connect_postgres(
        self,
        connection_string: str
    ) -> List[BaseTool]:
        """Connect to the PostgreSQL MCP server."""
        return await self.connect_server(
            server_name="postgres",
            command=["npx", "-y", "@modelcontextprotocol/server-postgres"],
            env={"DATABASE_URL": connection_string},
        )

    async def connect_github(self, token: str) -> List[BaseTool]:
        """Connect to the GitHub MCP server."""
        return await self.connect_server(
            server_name="github",
            command=["npx", "-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": token},
        )

    def get_all_tools(self) -> List[BaseTool]:
        """Get all tools from all connected servers."""
        tools = []
        for toolkit in self._toolkits.values():
            tools.extend(toolkit.get_tools())
        return tools

    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        for toolkit in self._toolkits.values():
            await toolkit.close()
        self._toolkits.clear()
```

**6.2 Custom MCP Server for Open Forge**

```python
# packages/mcp-server/src/open_forge_mcp.py
"""Custom MCP server exposing Open Forge capabilities."""
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

server = Server("open-forge")

@server.tool()
async def query_ontology(
    engagement_id: str,
    object_type: str,
    filters: dict = None
) -> str:
    """Query the ontology graph for an engagement.

    Args:
        engagement_id: The engagement to query
        object_type: The type of objects to retrieve
        filters: Optional filters to apply
    """
    from packages.ontology import OntologyEngine

    engine = OntologyEngine()
    results = await engine.query(engagement_id, object_type, filters)

    return json.dumps(results, indent=2)

@server.tool()
async def trigger_pipeline(
    engagement_id: str,
    pipeline_id: str,
    config_overrides: dict = None
) -> str:
    """Trigger a data pipeline execution.

    Args:
        engagement_id: The engagement context
        pipeline_id: The pipeline to execute
        config_overrides: Optional configuration overrides
    """
    from packages.pipelines import PipelineEngine

    engine = PipelineEngine()
    run = await engine.run_pipeline(pipeline_id, config_overrides)

    return f"Pipeline run started: {run.run_id}"

@server.tool()
async def generate_code(
    engagement_id: str,
    generator_type: str,
    target_entities: list = None
) -> str:
    """Generate code from the ontology.

    Args:
        engagement_id: The engagement context
        generator_type: Type of code to generate (fastapi, orm, hooks, tests)
        target_entities: Optional list of entities to generate for
    """
    from packages.codegen import CodegenEngine

    engine = CodegenEngine()
    result = await engine.generate(
        engagement_id=engagement_id,
        generator_type=generator_type,
        entities=target_entities,
    )

    return json.dumps({"files": result.files, "status": "success"})

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run())
```

**6.3 MCP Registry**

```python
# packages/agent-framework/src/tools/mcp_registry.py
from typing import Dict, Any, List
from pydantic import BaseModel

class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    name: str
    command: List[str]
    args: List[str] = []
    env: Dict[str, str] = {}
    description: str
    enabled: bool = True

class MCPRegistry:
    """Registry of available MCP servers."""

    DEFAULT_SERVERS = [
        MCPServerConfig(
            name="filesystem",
            command=["npx", "-y", "@modelcontextprotocol/server-filesystem"],
            description="File system access for reading/writing files",
        ),
        MCPServerConfig(
            name="postgres",
            command=["npx", "-y", "@modelcontextprotocol/server-postgres"],
            description="PostgreSQL database access",
        ),
        MCPServerConfig(
            name="github",
            command=["npx", "-y", "@modelcontextprotocol/server-github"],
            description="GitHub repository access",
        ),
        MCPServerConfig(
            name="open-forge",
            command=["python", "-m", "packages.mcp_server"],
            description="Open Forge internal capabilities",
        ),
    ]

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {
            s.name: s for s in self.DEFAULT_SERVERS
        }

    def register(self, config: MCPServerConfig):
        """Register a new MCP server."""
        self._servers[config.name] = config

    def get(self, name: str) -> MCPServerConfig:
        """Get server configuration by name."""
        return self._servers.get(name)

    def list_enabled(self) -> List[MCPServerConfig]:
        """List all enabled servers."""
        return [s for s in self._servers.values() if s.enabled]
```

#### Acceptance Criteria

- [ ] MCP client connects to standard servers
- [ ] Custom Open Forge MCP server works
- [ ] Tools accessible to agents
- [ ] Server registry allows dynamic registration
- [ ] Connection failures handled gracefully

---

## Integration Schedule

### Phase 1: Foundation (Week 1-2)
- WP1: Langflow deployment and basic integration
- WP2: React Flow pipeline canvas MVP
- WP3: PostgresStore setup and migration script

### Phase 2: Core Migration (Week 3-4)
- WP3: Complete memory migration
- WP4: Supervisor orchestrator implementation
- WP4: ReAct agent refactoring

### Phase 3: Observability & Tools (Week 5-6)
- WP5: LangSmith integration
- WP6: MCP adapters integration
- Integration testing across all components

### Timeline Visualization

```
Week:  1     2     3     4     5     6
       │     │     │     │     │     │
WP1:   ████████████░░░░░░░░░░░░░░░░░░  Langflow Canvas
WP2:   ████████████████░░░░░░░░░░░░░░  Pipeline Canvas
WP3:   ░░░░████████████░░░░░░░░░░░░░░  Memory Migration
WP4:   ░░░░░░░░████████████░░░░░░░░░░  Agent Patterns
WP5:   ░░░░░░░░░░░░░░░░████████░░░░░░  LangSmith
WP6:   ░░░░░░░░░░░░░░░░████████░░░░░░  MCP Adapters
INT:   ░░░░░░░░░░░░░░░░░░░░████████░░  Integration Test
       │     │     │     │     │     │
       G7────────────────────G8──────  Gates
```

---

## Updated pyproject.toml Dependencies

```toml
[project.dependencies]
# ... existing dependencies ...

# LangChain Ecosystem (updated)
langchain = ">=0.3"
langchain-anthropic = ">=0.3"
langgraph = ">=0.2"
langgraph-checkpoint-postgres = ">=0.1"
langgraph-store-postgres = ">=0.1"
langsmith = ">=0.1"
langchain-mcp-adapters = ">=0.1"

# Visual Canvas
reactflow = ">=11.0"  # React dependency

# Langflow (for development/testing)
langflow = ">=1.0"
```

---

## Testing Strategy

### Unit Tests
- Memory store operations
- Agent tool functionality
- Canvas compilation
- MCP adapter connections

### Integration Tests
- Supervisor → Agent routing
- Memory persistence across threads
- Langflow ↔ Open Forge sync
- Pipeline canvas → Dagster execution

### End-to-End Tests
- Full engagement with visual canvas refinement
- AI-generates → User-refines → Execute workflow
- Cross-engagement memory search

---

## Rollback Plan

If issues arise during migration:

1. **Memory**: Keep old custom memory system as fallback
2. **Agents**: Old agent implementations preserved in `_legacy/`
3. **Canvases**: Feature flag to disable visual interfaces
4. **LangSmith**: Falls back to Jaeger tracing

```python
# Feature flags
FEATURES = {
    "use_langflow_canvas": True,
    "use_pipeline_canvas": True,
    "use_langgraph_memory": True,
    "use_langsmith": True,
    "use_mcp_adapters": True,
}
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Agent task completion rate | 85% | 95% |
| Memory recall relevance | N/A | >90% |
| User workflow modification rate | N/A | >50% |
| Trace visibility | Partial | Complete |
| Tool extensibility | Custom only | MCP + Custom |

---

## Next Steps After Completion

1. **Gate 9: Production Deployment**
   - Kubernetes manifests for new services
   - Helm chart updates
   - Production LangSmith setup

2. **Documentation Updates**
   - Visual canvas user guides
   - MCP server development docs
   - Memory architecture docs

3. **Community Features**
   - Public MCP server registry
   - Langflow component marketplace
   - Shared workflow templates
