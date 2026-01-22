# Open Forge Platform Architecture: Enterprise Data Platform

**Date:** 2026-01-20
**Status:** Superseded (See 2026-01-21-consolidated-architecture.md)
**Goal:** Comprehensive enterprise data platform with AI capabilities

---

## Executive Summary

This document defines the complete architecture for Open Forge as an enterprise-grade data platform. The original design encompasses 64 packages across 8 development tracks, enabling parallel development by specialized subagents.

**Note:** This architecture has been superseded by the consolidated 20-package architecture in `2026-01-21-consolidated-architecture.md`.

### Key Decisions

1. **Progressive Disclosure UI** - Single app builder (Forge Studio) that scales from low-code to full-code
2. **Ontology-First** - All apps built around LinkML ontology objects
3. **Separate Packages** - Clean separation for parallel development
4. **Hybrid Patterns** - Block + Grid layouts, Direct + Query data binding
5. **Unique Branding** - All products named with "Forge" prefix

---

## Product Suite

| Product | Description |
|---------|-------------|
| **Forge** | Core platform |
| **Forge Studio** | Low-code app builder |
| **Forge Canvas** | Full-code app builder |
| **Forge Lens** | Object-driven analysis |
| **Forge Prism** | Large-scale tabular analysis |
| **Forge Atlas** | Geospatial visualization |
| **Forge Scribe** | Rich text reporting |
| **Forge Hub** | Workspace management |
| **Forge Navigator** | Data catalog & discovery |
| **Forge Browser** | Object search & exploration |
| **Forge Orbit** | Continuous delivery platform |
| **Forge Exchange** | Pre-built solutions |
| **Forge AI** | AI platform umbrella |
| **Forge Logic** | No-code LLM functions |
| **Forge Copilot** | AI assistant |
| **Forge Agent Builder** | Visual agent creation |
| **Forge Evaluate** | LLM testing framework |
| **Forge Automate** | Workflow automation |

---

## Product Suite Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OPEN FORGE PLATFORM                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      FORGE AI                                    │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │    │
│  │  │  Logic   │ │  Agent   │ │ Evaluate │ │ Copilot  │           │    │
│  │  │(no-code) │ │ Builder  │ │(testing) │ │(assist)  │           │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌───────────────────────┐  ┌───────────────────────────────────────┐   │
│  │    BUILD APPS         │  │           ANALYZE DATA                │   │
│  │  ┌────────┐ ┌───────┐ │  │  ┌──────┐ ┌───────┐ ┌───────┐       │   │
│  │  │ Studio │ │Canvas │ │  │  │ Lens │ │ Prism │ │ Atlas │       │   │
│  │  │(lo-co) │ │(code) │ │  │  │(obj) │ │(table)│ │ (geo) │       │   │
│  │  └────────┘ └───────┘ │  │  └──────┘ └───────┘ └───────┘       │   │
│  └───────────────────────┘  └───────────────────────────────────────┘   │
│                                                                          │
│  ┌───────────────────────┐  ┌───────────────────────────────────────┐   │
│  │    COLLABORATE        │  │           MANAGE DATA                 │   │
│  │  ┌────────┐ ┌───────┐ │  │  ┌─────────┐ ┌────────┐ ┌─────────┐  │   │
│  │  │ Scribe │ │  Hub  │ │  │  │Navigator│ │Quality │ │Branches │  │   │
│  │  │(report)│ │(work) │ │  │  │(catalog)│ │(health)│ │(version)│  │   │
│  │  └────────┘ └───────┘ │  │  └─────────┘ └────────┘ └─────────┘  │   │
│  └───────────────────────┘  └───────────────────────────────────────┘   │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    CONNECT & PROCESS                               │  │
│  │  ┌─────────────────┐  ┌────────────┐  ┌──────────────────────┐   │  │
│  │  │  Forge Connect  │  │ Transforms │  │    Forge Media       │   │  │
│  │  │  (200+ sources) │  │(Spark/Flink)│ │(Docs/Vision/Voice)  │   │  │
│  │  └─────────────────┘  └────────────┘  └──────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                         DEPLOY                                     │  │
│  │  ┌────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐              │  │
│  │  │ Orbit  │  │ Exchange │  │  Edge  │  │ Consumer │              │  │
│  │  │  (CD)  │  │(market)  │  │(airgap)│  │(public)  │              │  │
│  │  └────────┘  └──────────┘  └────────┘  └──────────┘              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    FOUNDATION                                      │  │
│  │  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌─────────────────┐  │  │
│  │  │ Ontology │  │ Pipelines │  │  Agents  │  │ Forge API       │  │  │
│  │  │ (LinkML) │  │ (Dagster) │  │(LangGraph)│ │ (FastAPI+GQL)   │  │  │
│  │  └──────────┘  └───────────┘  └──────────┘  └─────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Monorepo Structure

```
open-forge/
├── packages/
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── CORE PLATFORM (Existing + Enhanced)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── api/                     # Forge API
│   ├── ontology/                # Forge Ontology Engine
│   ├── agents/                  # Forge Agents (existing)
│   ├── pipelines/               # Forge Pipelines
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── CONNECTORS (Track A)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── connectors-core/         # Forge Connect (framework)
│   ├── connectors-sql/          # PostgreSQL, MySQL, SQL Server, Oracle
│   ├── connectors-warehouse/    # Snowflake, BigQuery, Redshift, Databricks
│   ├── connectors-nosql/        # MongoDB, Cassandra, DynamoDB, CosmosDB
│   ├── connectors-streaming/    # Kafka, Kinesis, Pub/Sub, EventHub
│   ├── connectors-erp/          # SAP, Oracle EBS, NetSuite, Dynamics
│   ├── connectors-crm/          # Salesforce, HubSpot, Dynamics 365
│   ├── connectors-cloud/        # S3, Azure Blob, GCS, MinIO
│   ├── connectors-files/        # HDFS, SFTP, local, Parquet, CSV
│   ├── connectors-api/          # REST, GraphQL, SOAP, OData, webhooks
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── DATA PLATFORM (Track B)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── transforms-core/         # Forge Transforms
│   ├── transforms-spark/        # Apache Spark transforms
│   ├── transforms-flink/        # Apache Flink streaming
│   ├── transforms-datafusion/   # Rust-based fast transforms
│   ├── forge-quality/           # Forge Quality (health checks)
│   ├── forge-lineage/           # Forge Lineage (data lineage)
│   ├── forge-branches/          # Forge Branches (data versioning)
│   ├── forge-navigator/         # Forge Navigator (data catalog)
│   ├── forge-federation/        # Forge Federation (virtual tables)
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── FORGE AI (Track C)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── forge-ai-core/           # Forge AI Core (multi-LLM)
│   ├── forge-logic/             # Forge Logic (no-code LLM functions)
│   ├── forge-agent-builder/     # Forge Agent Builder
│   ├── forge-evaluate/          # Forge Evaluate (LLM testing)
│   ├── forge-copilot/           # Forge Copilot (AI assistant)
│   ├── forge-automate/          # Forge Automate (automation)
│   ├── forge-vectors/           # Forge Vectors (embeddings, RAG)
│   ├── forge-ml/                # Forge ML (model ops)
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── ANALYTICS & APPS (Track D)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── ui/                      # Forge Portal (main UI)
│   ├── ui-components/           # Forge Design System
│   ├── forge-studio/            # Forge Studio (low-code builder)
│   ├── forge-studio-runtime/    # Forge Studio Runtime
│   ├── forge-studio-widgets/    # Forge Studio Widgets
│   ├── forge-canvas/            # Forge Canvas (full-code builder)
│   ├── forge-lens/              # Forge Lens (object analysis)
│   ├── forge-prism/             # Forge Prism (tabular analysis)
│   ├── forge-scribe/            # Forge Scribe (reporting)
│   ├── forge-hub/               # Forge Hub (workspaces)
│   ├── forge-browser/           # Forge Browser (object explorer)
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── GEOSPATIAL (Track E)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── forge-geo-core/          # Forge Geo (primitives)
│   ├── forge-atlas/             # Forge Atlas (map app)
│   ├── forge-tracks/            # Forge Tracks (movement tracking)
│   ├── forge-routes/            # Forge Routes (network analysis)
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── MEDIA (Track F)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── forge-media-core/        # Forge Media (storage)
│   ├── forge-documents/         # Forge Documents (PDF, DOCX)
│   ├── forge-vision/            # Forge Vision (OCR, images)
│   ├── forge-voice/             # Forge Voice (transcription)
│   ├── forge-video/             # Forge Video (video processing)
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── COLLABORATION (Track G)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── forge-sharing/           # Forge Sharing (permissions)
│   ├── forge-collections/       # Forge Collections (curation)
│   ├── forge-alerts/            # Forge Alerts (notifications)
│   ├── forge-audit/             # Forge Audit (audit logs)
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── DEPLOYMENT (Track H)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── forge-orbit/             # Forge Orbit (CD platform)
│   ├── forge-exchange/          # Forge Exchange (marketplace)
│   ├── forge-edge/              # Forge Edge (edge deployment)
│   ├── forge-consumer/          # Forge Consumer (public apps)
│   │
│   └── ══════════════════════════════════════════════════════════════
│
├── apps/
│   ├── portal/                  # Forge Portal
│   ├── studio/                  # Forge Studio (standalone)
│   ├── atlas/                   # Forge Atlas (standalone)
│   └── docs/                    # Forge Docs
│
├── tools/
│   ├── forge-cli/               # Forge CLI
│   ├── forge-sdk-python/        # Forge SDK for Python
│   ├── forge-sdk-typescript/    # Forge SDK for TypeScript
│   ├── forge-sdk-java/          # Forge SDK for Java
│   └── forge-codegen/           # Forge Codegen
│
└── infrastructure/
    ├── docker/
    ├── kubernetes/
    ├── terraform/
    └── helm/
```

---

## Package Dependencies

```
                                    ┌─────────────────┐
                                    │   ui-components │
                                    └────────┬────────┘
                                             │
        ┌────────────────────────────────────┼────────────────────────────────────┐
        │                    │               │               │                    │
        ▼                    ▼               ▼               ▼                    ▼
   ┌─────────┐        ┌───────────┐    ┌─────────┐    ┌───────────┐       ┌───────────┐
   │   ui    │        │  studio   │    │  lens   │    │  scribe   │       │   hub     │
   └────┬────┘        └─────┬─────┘    └────┬────┘    └─────┬─────┘       └─────┬─────┘
        │                   │               │               │                   │
        └───────────────────┴───────────────┴───────────────┴───────────────────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │      api      │◄────────────────────────────┐
                                    └───────┬───────┘                             │
                                            │                                     │
        ┌───────────────────────────────────┼───────────────────────────────────┐ │
        │               │                   │                   │               │ │
        ▼               ▼                   ▼                   ▼               ▼ │
┌───────────────┐ ┌───────────┐     ┌─────────────┐     ┌───────────┐   ┌────────────┐
│connectors-*   │ │transforms-*│    │  forge-ai-* │     │forge-media│   │ forge-geo  │
└───────┬───────┘ └─────┬─────┘     └──────┬──────┘     └─────┬─────┘   └──────┬─────┘
        │               │                  │                  │                │
        └───────────────┴──────────────────┴──────────────────┴────────────────┘
                                           │
                                           ▼
                              ┌────────────────────────┐
                              │       ontology         │
                              └────────────────────────┘
                                           │
                                           ▼
                              ┌────────────────────────┐
                              │       pipelines        │
                              └────────────────────────┘
```

---

## Forge Studio Architecture (Track D - MVP)

### Overview

Forge Studio is the low-code app builder using progressive disclosure:
- **Level 1**: Drag-and-drop widgets with visual configuration
- **Level 2**: Custom code widgets for small customizations
- **Level 3**: Widget-level code overrides for power users
- **Level 4**: Full page code export for developers

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Forge Studio                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐      │
│  │   Canvas    │  │   Widget    │  │    Code Editor      │      │
│  │   Editor    │  │   Library   │  │    (Monaco)         │      │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘      │
│         │                │                     │                 │
│         └────────────────┼─────────────────────┘                 │
│                          ▼                                       │
│              ┌───────────────────────┐                           │
│              │   App State Manager   │                           │
│              │   (Zustand + Immer)   │                           │
│              └───────────┬───────────┘                           │
│                          ▼                                       │
│              ┌───────────────────────┐                           │
│              │   Ontology Binding    │◄── LinkML Schemas         │
│              │   Layer               │◄── Object Types           │
│              └───────────┬───────────┘◄── Actions                │
│                          ▼                                       │
│              ┌───────────────────────┐                           │
│              │   API Client          │──► Forge API              │
│              └───────────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### Page & Widget Model

```typescript
interface StudioApp {
  id: string;
  name: string;
  ontologyId: string;
  pages: StudioPage[];
  theme: ThemeConfig;
  navigation: NavConfig;
}

interface StudioPage {
  id: string;
  name: string;
  route: string;
  sections: PageSection[];
  parameters: PageParameter[];
}

interface PageSection {
  id: string;
  title?: string;
  layout: 'grid' | 'full-width' | 'split';
  columns: number;
  widgets: WidgetInstance[];
  collapsed?: boolean;
}

interface WidgetInstance {
  id: string;
  type: WidgetType;
  position: { col: number; row: number; width: number; height: number };
  config: WidgetConfig;
  bindings: DataBinding[];
  codeOverride?: string;
}
```

### MVP Widgets (8)

| Widget | Purpose |
|--------|---------|
| Object Table | Display list of ontology objects |
| Object Detail | Show single object properties |
| Form | Create/edit objects via Actions |
| Chart | Bar, Line, Pie, Area visualizations |
| Metric Card | Single KPI display |
| Text/Markdown | Static or dynamic content |
| Filter Bar | Global filters for page |
| Action Button | Trigger ontology Actions |

### Data Binding

**Direct Binding** (simple widgets):
```typescript
interface DirectBinding {
  type: 'direct';
  objectType: string;
  property: string;
  aggregation?: 'count' | 'sum' | 'avg' | 'min' | 'max';
  filter?: SimpleFilter;
}
```

**Query Binding** (complex widgets):
```typescript
interface QueryBinding {
  type: 'query';
  source: ObjectTypeRef;
  select: PropertyRef[];
  joins?: JoinClause[];
  filters: FilterGroup;
  groupBy?: PropertyRef[];
  orderBy?: OrderClause[];
  limit?: number;
  parameters?: ParameterRef[];
}
```

### Editor UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  Logo   [App Name ▼]   [Pages ▼]        [Preview] [Save] [Publish]  │
├─────────┬───────────────────────────────────────────────┬───────────┤
│         │                                               │           │
│  Widget │              Canvas Area                      │  Config   │
│  Panel  │                                               │  Panel    │
│         │   ┌─────────────────────────────────┐         │           │
│ ┌─────┐ │   │  Section: Header                │         │  Widget   │
│ │Table│ │   │  [Metric] [Metric] [Metric]     │         │  Settings │
│ └─────┘ │   └─────────────────────────────────┘         │           │
│ ┌─────┐ │   ┌─────────────────────────────────┐         │  Data     │
│ │Form │ │   │  Section: Main Content          │         │  Binding  │
│ └─────┘ │   │  ┌───────────────┬─────────┐    │         │           │
│ ┌─────┐ │   │  │    Table      │  Chart  │    │         │  Actions  │
│ │Chart│ │   │  │               │         │    │         │           │
│ └─────┘ │   │  └───────────────┴─────────┘    │         │  Style    │
│  ...    │   └─────────────────────────────────┘         │           │
│         │                                               │  Code     │
├─────────┴───────────────────────────────────────────────┴───────────┤
│  [+ Add Section]                          Zoom: 100%  │ Grid │ Free │
└─────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

```json
{
  "dependencies": {
    "next": "^16.0.0",
    "react": "^19.0.0",
    "@dnd-kit/core": "^6.x",
    "@dnd-kit/sortable": "^8.x",
    "monaco-editor": "^0.50.x",
    "@monaco-editor/react": "^4.x",
    "@radix-ui/react-*": "latest",
    "tailwindcss": "^4.x",
    "lucide-react": "latest",
    "@tanstack/react-query": "^5.x",
    "zustand": "^5.x",
    "immer": "^10.x",
    "recharts": "^2.x",
    "@visx/visx": "^3.x",
    "mapbox-gl": "^3.x",
    "@deck.gl/react": "^9.x"
  }
}
```

---

## Development Tracks for Parallel Subagents

### Track Overview

```
TRACK A: FORGE CONNECT       TRACK B: FORGE DATA          TRACK C: FORGE AI
━━━━━━━━━━━━━━━━━━━━         ━━━━━━━━━━━━━━━━━━          ━━━━━━━━━━━━━━━━━━

A1: Connect Core             B1: Quality + Lineage        C1: AI Core + Vectors
A2: Cloud Warehouses         B2: Streaming Transforms     C2: Logic + Agent Builder
A3: Enterprise (ERP/CRM)     B3: Branches + Federation    C3: Evaluate + Automate
A4: Specialized (NoSQL/API)  B4: Navigator (Catalog)      C4: Copilot + ML


TRACK D: FORGE APPS          TRACK E: FORGE GEO           TRACK F: FORGE MEDIA
━━━━━━━━━━━━━━━━━━━━         ━━━━━━━━━━━━━━━━━━          ━━━━━━━━━━━━━━━━━━━━

D1: Studio MVP               E1: Geo Core + Atlas         F1: Media Core + Documents
D2: Studio + Canvas          E2: Tracks + Routes          F2: Vision + Video
D3: Lens + Prism             E3: Atlas Studio Widget      F3: Voice
D4: AI Widgets + Browser


TRACK G: FORGE COLLAB        TRACK H: FORGE DEPLOY
━━━━━━━━━━━━━━━━━━━━         ━━━━━━━━━━━━━━━━━━━━

G1: Sharing + Collections    H1: Orbit + Exchange
G2: Alerts + Audit           H2: Edge + Consumer
G3: Scribe + Hub
```

### Parallel Development Lanes

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PARALLEL DEVELOPMENT LANES                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  LANE 1: UI/Studio          LANE 2: Connectors    LANE 3: AI        │
│  ══════════════════         ═══════════════════   ══════════════    │
│  Agent: ui-builder          Agent: connector-dev  Agent: ai-dev     │
│  D1 → D2 → D3 → D4          A1 → A2 → A3 → A4     C1 → C2 → C3 → C4 │
│                                                                      │
│  LANE 4: Data Platform      LANE 5: Media/Geo                        │
│  ══════════════════════     ═══════════════════                      │
│  Agent: data-eng            Agent: media-geo-dev                     │
│  B1 → B2 → B3 → B4          F1 → F2 → F3 + E1 → E2 → E3              │
│                                                                      │
│  SEQUENTIAL (After core):                                            │
│  ════════════════════════                                            │
│  G1 → G2 → G3 (Collaboration)                                        │
│  H1 → H2 (Deployment)                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Implementation Priority Matrix

| Track | Phase | Packages | Dependencies | Parallel? |
|-------|-------|----------|--------------|-----------|
| **D1** | Studio MVP | forge-studio, forge-studio-widgets, ui-components | api, ontology | **START** |
| **A1** | Connectors Core | connectors-core, connectors-sql | api | **START** |
| **C1** | Multi-LLM | forge-ai-core, forge-vectors | api, ontology | **START** |
| **B1** | Data Quality | forge-quality, forge-lineage | api, pipelines | **START** |
| **F1** | Documents | forge-media-core, forge-documents | api | **START** |
| **A2** | Warehouses | connectors-warehouse | connectors-core | After A1 |
| **D2** | Studio Parity | forge-studio-runtime, more widgets | D1 | After D1 |
| **C2** | No-Code AI | forge-logic, forge-agent-builder | C1 | After C1 |
| **E1** | Geo Core | forge-geo-core, forge-atlas | api | After D1 |
| **B2** | Streaming | transforms-flink | B1, connectors-streaming | After A3, B1 |
| **A3** | Enterprise | connectors-erp, connectors-crm, connectors-streaming | A1 | After A2 |
| **G1** | Collaboration | forge-sharing, forge-collections | api | After D2 |
| **D3** | Analytics | forge-lens, forge-prism | D2 | After D2 |
| **C3** | Evals | forge-evaluate, forge-automate | C2 | After C2 |
| **F2** | Visual | forge-vision, forge-video | F1 | After F1 |
| **E2** | Geo Advanced | forge-tracks, forge-routes | E1 | After E1 |
| **B3** | Advanced | forge-branches, forge-federation | B2 | After B2 |
| **D4** | AI Widgets | AI widgets in studio | D3, C2 | After C2, D3 |
| **C4** | Copilot | forge-copilot, forge-ml | C3 | After C3 |
| **H1** | Deployment | forge-orbit, forge-exchange | All core | After D3 |
| **G2** | Notifications | forge-alerts, forge-audit | G1 | After G1 |
| **F3** | Audio | forge-voice | F2 | After F2 |
| **A4** | Specialized | connectors-nosql, connectors-api | A3 | After A3 |
| **H2** | Edge | forge-edge, forge-consumer | H1 | After H1 |
| **B4** | Catalog | forge-navigator | B3, G1 | After B3, G1 |
| **E3** | Geo Integration | Atlas Studio Widget | E2, D3 | After E2, D3 |
| **G3** | Workspaces | forge-hub | G2, D4 | After G2, D4 |

---

## Package Specifications

### Track A: Connectors

```
packages/connectors-core/
├── src/
│   ├── base.py              # BaseConnector abstract class
│   ├── registry.py          # Connector type registry
│   ├── discovery.py         # Schema discovery
│   ├── profiler.py          # Data profiling
│   ├── sync/
│   │   ├── batch.py         # Batch sync engine
│   │   ├── incremental.py   # CDC/incremental sync
│   │   └── streaming.py     # Real-time streaming
│   ├── auth/
│   │   ├── oauth.py         # OAuth2 flows
│   │   ├── service_account.py
│   │   └── api_key.py
│   └── transforms/
│       ├── type_mapping.py  # Cross-DB type normalization
│       └── schema_evolution.py
└── tests/

packages/connectors-warehouse/
├── src/
│   ├── snowflake/
│   │   ├── connector.py
│   │   ├── query_pushdown.py
│   │   └── streaming.py
│   ├── bigquery/
│   ├── redshift/
│   ├── databricks/
│   └── synapse/
└── tests/

packages/connectors-streaming/
├── src/
│   ├── kafka/
│   │   ├── consumer.py
│   │   ├── producer.py
│   │   ├── schema_registry.py
│   │   └── connect.py
│   ├── kinesis/
│   ├── pubsub/
│   ├── eventhub/
│   └── rabbitmq/
└── tests/
```

### Track B: Data Platform

```
packages/forge-quality/
├── src/
│   ├── checks/
│   │   ├── base.py
│   │   ├── freshness.py
│   │   ├── completeness.py
│   │   ├── schema.py
│   │   ├── volume.py
│   │   ├── custom.py
│   │   └── statistical.py
│   ├── monitors/
│   │   ├── monitor.py
│   │   ├── schedule.py
│   │   └── alerting.py
│   ├── remediation/
│   │   ├── auto_fix.py
│   │   └── issue_tracker.py
│   └── api/
│       └── routes.py
└── tests/

packages/forge-branches/
├── src/
│   ├── branch.py
│   ├── commit.py
│   ├── merge.py
│   ├── diff.py
│   ├── conflict.py
│   ├── storage/
│   │   ├── iceberg.py
│   │   └── delta.py
│   └── api/
│       └── routes.py
└── tests/
```

### Track C: Forge AI

```
packages/forge-ai-core/
├── src/
│   ├── providers/
│   │   ├── base.py
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   ├── google.py
│   │   ├── meta.py
│   │   ├── mistral.py
│   │   └── local.py
│   ├── routing/
│   │   ├── router.py
│   │   ├── fallback.py
│   │   └── load_balancer.py
│   ├── context/
│   │   ├── ontology.py
│   │   └── rag.py
│   ├── security/
│   │   ├── pii_filter.py
│   │   ├── guardrails.py
│   │   └── audit.py
│   └── api/
│       └── routes.py
└── tests/

packages/forge-evaluate/
├── src/
│   ├── suites/
│   │   ├── suite.py
│   │   ├── test_case.py
│   │   └── runner.py
│   ├── evaluators/
│   │   ├── base.py
│   │   ├── exact_match.py
│   │   ├── semantic.py
│   │   ├── llm_judge.py
│   │   ├── factuality.py
│   │   └── custom.py
│   ├── perturbations/
│   │   ├── typos.py
│   │   ├── paraphrase.py
│   │   └── adversarial.py
│   ├── simulation/
│   │   └── ontology_sim.py
│   └── api/
│       └── routes.py
└── tests/

packages/forge-vectors/
├── src/
│   ├── embeddings/
│   │   ├── base.py
│   │   ├── openai.py
│   │   ├── sentence.py
│   │   └── local.py
│   ├── stores/
│   │   ├── pgvector.py
│   │   ├── qdrant.py
│   │   ├── pinecone.py
│   │   └── weaviate.py
│   ├── search/
│   │   ├── knn.py
│   │   ├── hybrid.py
│   │   └── rerank.py
│   ├── chunking/
│   │   ├── strategies.py
│   │   └── hyde.py
│   └── api/
│       └── routes.py
└── tests/
```

### Track E: Geospatial

```
packages/forge-geo-core/
├── src/
│   ├── types/
│   │   ├── point.py
│   │   ├── polygon.py
│   │   ├── line.py
│   │   └── collection.py
│   ├── indexes/
│   │   ├── rtree.py
│   │   ├── h3.py
│   │   └── geohash.py
│   ├── queries/
│   │   ├── bbox.py
│   │   ├── intersection.py
│   │   ├── distance.py
│   │   └── within.py
│   └── api/
│       └── routes.py
└── tests/

packages/forge-atlas/
├── src/
│   ├── components/
│   │   ├── Map.tsx
│   │   ├── layers/
│   │   │   ├── PointLayer.tsx
│   │   │   ├── PolygonLayer.tsx
│   │   │   ├── ClusterLayer.tsx
│   │   │   ├── HeatmapLayer.tsx
│   │   │   └── RasterLayer.tsx
│   │   ├── controls/
│   │   │   ├── ZoomControl.tsx
│   │   │   ├── LayerControl.tsx
│   │   │   └── DrawControl.tsx
│   │   └── popups/
│   │       └── ObjectPopup.tsx
│   ├── hooks/
│   │   ├── useMapData.ts
│   │   └── useViewport.ts
│   └── lib/
│       ├── mapbox.ts
│       └── deckgl.ts
└── tests/
```

### Track F: Media

```
packages/forge-media-core/
├── src/
│   ├── media_set.py
│   ├── storage/
│   │   ├── s3.py
│   │   ├── minio.py
│   │   └── azure.py
│   ├── formats/
│   │   ├── detector.py
│   │   └── converter.py
│   └── api/
│       └── routes.py
└── tests/

packages/forge-documents/
├── src/
│   ├── extractors/
│   │   ├── pdf.py
│   │   ├── docx.py
│   │   ├── xlsx.py
│   │   └── html.py
│   ├── chunking/
│   │   ├── page.py
│   │   ├── semantic.py
│   │   └── table.py
│   └── api/
│       └── routes.py
└── tests/

packages/forge-vision/
├── src/
│   ├── ocr/
│   │   ├── tesseract.py
│   │   ├── easyocr.py
│   │   └── vision_api.py
│   ├── processing/
│   │   ├── resize.py
│   │   ├── tiling.py
│   │   └── convert.py
│   └── api/
│       └── routes.py
└── tests/

packages/forge-voice/
├── src/
│   ├── transcription/
│   │   ├── whisper.py
│   │   ├── deepgram.py
│   │   └── assemblyai.py
│   ├── diarization/
│   │   └── speaker.py
│   └── api/
│       └── routes.py
└── tests/
```

### Track H: Deployment

```
packages/forge-orbit/
├── src/
│   ├── products/
│   │   ├── product.py
│   │   ├── bundle.py
│   │   └── version.py
│   ├── deployment/
│   │   ├── gitops.py
│   │   ├── rollout.py
│   │   └── rollback.py
│   ├── environments/
│   │   ├── environment.py
│   │   ├── promotion.py
│   │   └── sync.py
│   └── api/
│       └── routes.py
└── tests/

packages/forge-edge/
├── src/
│   ├── runtime/
│   │   ├── edge_runtime.py
│   │   └── sync.py
│   ├── offline/
│   │   ├── queue.py
│   │   └── conflict.py
│   └── api/
│       └── routes.py
└── tests/
```

---

## API Endpoints (New)

### Forge Studio API

```
/api/v1/studio/
├── apps/
│   ├── POST   /                    # Create new app
│   ├── GET    /                    # List apps
│   ├── GET    /:id                 # Get app definition
│   ├── PATCH  /:id                 # Update app
│   ├── DELETE /:id                 # Delete app
│   ├── POST   /:id/publish         # Publish current draft
│   ├── POST   /:id/rollback        # Rollback to previous version
│   └── GET    /:id/versions        # List version history
│
├── runtime/
│   ├── GET    /apps/:slug          # Get published app
│   └── GET    /apps/:slug/data     # Execute data queries
│
└── ontology/
    ├── GET    /:id/object-types    # List object types
    ├── GET    /:id/actions         # List available actions
    └── POST   /:id/query           # Execute ontology query
```

---

## Package Count Summary

| Track | Packages | Estimated Effort |
|-------|----------|------------------|
| **Core (existing)** | 4 | Enhance |
| **A: Forge Connect** | 10 | Large |
| **B: Forge Data** | 9 | Large |
| **C: Forge AI** | 8 | Large |
| **D: Forge Apps** | 11 | Very Large |
| **E: Forge Geo** | 4 | Medium |
| **F: Forge Media** | 5 | Medium |
| **G: Forge Collab** | 4 | Medium |
| **H: Forge Deploy** | 4 | Medium |
| **Tools** | 5 | Medium |
| **TOTAL** | **64 packages** | - |

---

## Next Steps

1. **Immediate**: Begin parallel development on tracks D1, A1, C1, B1, F1
2. **Week 2+**: Progress through track phases as dependencies complete
3. **Ongoing**: Code reviews via `/workflows:review` after each phase
4. **Documentation**: Update this plan as implementation reveals adjustments

---

## Appendix: Feature Coverage Reference

This architecture was designed to provide comprehensive enterprise data platform capabilities:

- **193+ Connectors** → Track A
- **20+ AI/ML Features** → Track C
- **5 Analytics Tools** → Track D
- **12+ Geospatial Features** → Track E
- **10+ Media Features** → Track F
- **13+ Data Quality Features** → Track B
- **6+ Collaboration Tools** → Track G
- **Deployment Platform** → Track H

**Note**: Security certifications (FedRAMP, IL5/IL6, HIPAA) are out of scope for this architecture as they require organizational compliance processes, not code.
