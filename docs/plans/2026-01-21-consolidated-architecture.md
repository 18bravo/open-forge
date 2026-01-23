# Open Forge Platform Architecture: Consolidated Design

**Date:** 2026-01-21
**Status:** Draft (Supersedes 2026-01-20 64-package architecture)
**Goal:** Streamlined architecture focused on MVP delivery

---

## Executive Summary

This document presents a **consolidated architecture** that reduces the original 64-package design to **20 focused packages**. This revision addresses critical gaps identified in architectural review and focuses on delivering enterprise-grade data platform capabilities.

### Key Changes from Original Architecture

| Aspect | Original (64 packages) | Consolidated (20 packages) |
|--------|------------------------|---------------------------|
| Total packages | 64 | 20 |
| Connector packages | 10 separate | 1 unified (forge-connectors) |
| Transform engines | 4 (core, spark, flink, datafusion) | 1 (DataFusion only) |
| AI packages | 8 | 3 (forge-ai, forge-agents, forge-vectors) |
| Studio packages | 4 | 1 unified (forge-studio) |
| Analytics packages | 4 | 1 unified (forge-analytics) |
| Missing infrastructure | None | Added forge-core (auth, events, storage, gateway) |
| Edge/marketplace | Included | Deferred post-MVP |

### Critical Additions

1. **forge-core** - Missing foundational infrastructure:
   - Centralized authentication (OAuth2/OIDC, RBAC, row-level security)
   - Event bus for cross-package communication
   - Storage abstraction layer
   - API gateway for rate limiting, circuit breaking, request routing

---

## Product Suite

| Product | Description |
|---------|-------------|
| **Forge** | Core data platform |
| **Forge Studio** | Low-code app builder |
| **Forge Analytics** | Object + tabular analysis |
| **Forge Atlas** | Geospatial visualization |
| **Forge Orbit** | Continuous delivery platform |
| **Forge AI** | AI platform |

---

## Consolidated Package Structure

```
open-forge/
├── packages/
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── FOUNDATION (5 packages)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── forge-core/             # NEW: Auth, events, storage, gateway
│   ├── api/                    # Forge API (FastAPI + GraphQL)
│   ├── ontology/               # Forge Ontology Engine (LinkML)
│   ├── agents/                 # Forge Agents (LangGraph)
│   ├── pipelines/              # Forge Pipelines (Dagster)
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── DATA LAYER (4 packages)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── forge-connectors/       # Unified connector framework
│   ├── forge-transforms/       # DataFusion transforms only
│   ├── forge-data/             # Quality + lineage + branches
│   ├── forge-vectors/          # Embeddings + RAG + semantic search
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── AI LAYER (2 packages)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── forge-ai/               # Multi-LLM core + Logic
│   ├── forge-agents/           # Agent Builder + Evaluate
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── APPLICATION LAYER (4 packages)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── ui/                     # Forge Portal (Next.js)
│   ├── forge-studio/           # App builder + widgets + runtime
│   ├── forge-analytics/        # Lens + Prism + Browser
│   ├── forge-geo/              # Geo core + Atlas map
│   │
│   ├── ══════════════════════════════════════════════════════════════
│   ├── OPERATIONAL LAYER (3 packages)
│   ├── ══════════════════════════════════════════════════════════════
│   │
│   ├── forge-media/            # Documents + Vision (video deferred)
│   ├── forge-collab/           # Sharing + alerts + audit
│   └── forge-deploy/           # Orbit CD (edge/marketplace deferred)
│   │
│   └── ══════════════════════════════════════════════════════════════
│
├── tools/
│   ├── forge-cli/              # CLI for development
│   └── forge-sdk-python/       # Python SDK
│
└── infrastructure/
    ├── docker/
    ├── kubernetes/
    └── terraform/
```

**Total: 20 packages** (down from 64)

---

## Package Specifications

### 1. forge-core (NEW - Critical Infrastructure)

**Purpose:** Centralized authentication, authorization, event bus, storage abstraction, and API gateway.

```
packages/forge-core/
├── src/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── provider.py         # OAuth2/OIDC provider abstraction
│   │   ├── rbac.py             # Role-based access control
│   │   ├── permissions.py      # Permission definitions
│   │   ├── row_level.py        # Row-level security policies
│   │   ├── session.py          # Session management
│   │   └── middleware.py       # FastAPI auth middleware
│   │
│   ├── events/
│   │   ├── __init__.py
│   │   ├── bus.py              # Event bus abstraction
│   │   ├── topics.py           # Event topic definitions
│   │   ├── handlers.py         # Event handler registration
│   │   └── backends/
│   │       ├── redis.py        # Redis Pub/Sub backend
│   │       ├── postgres.py     # PostgreSQL NOTIFY backend
│   │       └── memory.py       # In-memory for testing
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── abstraction.py      # Storage interface
│   │   └── backends/
│   │       ├── s3.py
│   │       ├── minio.py
│   │       ├── azure.py
│   │       └── local.py
│   │
│   ├── gateway/
│   │   ├── __init__.py
│   │   ├── rate_limit.py       # Rate limiting
│   │   ├── circuit_breaker.py  # Circuit breaker pattern
│   │   ├── routing.py          # Request routing
│   │   └── health.py           # Health check aggregation
│   │
│   └── config/
│       ├── __init__.py
│       └── settings.py         # Centralized config management
│
└── tests/
```

**Key Interfaces:**

```python
# Authentication
class AuthProvider(Protocol):
    async def authenticate(self, token: str) -> User: ...
    async def authorize(self, user: User, resource: str, action: str) -> bool: ...
    async def get_row_filter(self, user: User, object_type: str) -> Filter | None: ...

# Event Bus
class EventBus(Protocol):
    async def publish(self, topic: str, event: Event) -> None: ...
    async def subscribe(self, topic: str, handler: EventHandler) -> Subscription: ...

# Storage
class StorageBackend(Protocol):
    async def put(self, key: str, data: bytes, metadata: dict) -> None: ...
    async def get(self, key: str) -> tuple[bytes, dict]: ...
    async def delete(self, key: str) -> None: ...
    async def list(self, prefix: str) -> AsyncIterator[str]: ...
```

---

### 2. forge-connectors (Unified)

**Purpose:** Single package for all data source connectivity.

```
packages/forge-connectors/
├── src/
│   ├── core/
│   │   ├── base.py             # BaseConnector abstract class
│   │   ├── registry.py         # Connector type registry
│   │   ├── discovery.py        # Schema discovery
│   │   ├── profiler.py         # Data profiling
│   │   └── pool.py             # Connection pooling
│   │
│   ├── sync/
│   │   ├── engine.py           # Unified sync engine
│   │   ├── batch.py            # Batch sync
│   │   ├── incremental.py      # CDC/incremental
│   │   ├── streaming.py        # Real-time streaming
│   │   └── writeback.py        # Reverse ETL
│   │
│   ├── auth/
│   │   ├── oauth.py
│   │   ├── service_account.py
│   │   └── secrets.py          # Vault/secrets manager integration
│   │
│   ├── connectors/
│   │   ├── sql/                # PostgreSQL, MySQL, SQL Server
│   │   ├── warehouse/          # Snowflake, BigQuery, Redshift
│   │   ├── nosql/              # MongoDB, DynamoDB (Phase 2)
│   │   ├── streaming/          # Kafka, Kinesis (Phase 2)
│   │   ├── cloud/              # S3, Azure Blob, GCS
│   │   ├── files/              # Parquet, CSV, SFTP
│   │   └── api/                # REST, GraphQL
│   │
│   └── api/
│       └── routes.py
│
└── tests/
```

**Connection Pool Configuration:**

```python
@dataclass
class PoolConfig:
    min_connections: int = 2
    max_connections: int = 20
    max_idle_time: timedelta = timedelta(minutes=10)
    health_check_interval: timedelta = timedelta(seconds=30)
    acquire_timeout: timedelta = timedelta(seconds=5)
```

---

### 3. forge-transforms (DataFusion Only)

**Purpose:** Rust-based fast transforms using Apache DataFusion. Spark/Flink deferred.

```
packages/forge-transforms/
├── src/
│   ├── engine/
│   │   ├── datafusion.py       # DataFusion execution engine
│   │   ├── context.py          # Session context management
│   │   └── udf.py              # User-defined functions
│   │
│   ├── transforms/
│   │   ├── sql.py              # SQL transforms
│   │   ├── expression.py       # Expression-based transforms
│   │   └── aggregate.py        # Aggregation transforms
│   │
│   ├── incremental/
│   │   ├── engine.py           # Incremental processing
│   │   └── checkpoints.py      # State checkpointing
│   │
│   └── api/
│       └── routes.py
│
└── tests/
```

---

### 4. forge-data (Quality + Lineage + Branches)

**Purpose:** Unified data governance package.

```
packages/forge-data/
├── src/
│   ├── quality/
│   │   ├── checks.py           # Freshness, completeness, schema
│   │   ├── monitors.py         # Health monitoring
│   │   └── alerting.py         # Quality alerts
│   │
│   ├── lineage/
│   │   ├── graph.py            # Lineage graph with max depth
│   │   ├── tracker.py          # Automatic lineage capture
│   │   └── impact.py           # Impact analysis
│   │
│   ├── branches/
│   │   ├── branch.py           # Dataset branching
│   │   ├── merge.py            # Merge with conflict resolution
│   │   └── storage.py          # Iceberg/Delta backend
│   │
│   ├── catalog/
│   │   ├── navigator.py        # Data catalog
│   │   └── search.py           # Metadata search
│   │
│   └── api/
│       └── routes.py
│
└── tests/
```

**Lineage Graph Limits:**

```python
class LineageQuery:
    max_depth: int = 10  # Prevent unbounded traversal
    max_nodes: int = 1000
    timeout: timedelta = timedelta(seconds=30)
```

---

### 5. forge-ai (Multi-LLM Core + Logic)

**Purpose:** Unified AI capabilities with LiteLLM abstraction.

```
packages/forge-ai/
├── src/
│   ├── providers/
│   │   ├── litellm.py          # LiteLLM wrapper
│   │   ├── routing.py          # Provider routing
│   │   └── fallback.py         # Fallback chain
│   │
│   ├── logic/
│   │   ├── functions.py        # No-code LLM functions
│   │   ├── builder.py          # Visual function builder
│   │   └── execution.py        # Function execution engine
│   │
│   ├── context/
│   │   ├── ontology.py         # Ontology context injection
│   │   └── rag.py              # RAG retrieval
│   │
│   ├── security/
│   │   ├── pii_filter.py       # PII detection/masking
│   │   ├── guardrails.py       # Output validation
│   │   ├── injection.py        # Prompt injection detection
│   │   └── audit.py            # Request/response logging
│   │
│   └── api/
│       └── routes.py
│
└── tests/
```

**Injection Detection (Improved):**

```python
class InjectionDetector:
    """Multi-layer prompt injection detection."""

    def detect(self, input: str) -> InjectionResult:
        results = [
            self._pattern_match(input),      # Known patterns
            self._semantic_similarity(input), # Semantic analysis
            self._llm_classifier(input),      # LLM-based detection
        ]
        return self._aggregate_results(results)
```

---

### 6. forge-agents (Agent Builder + Evaluate)

**Purpose:** Visual agent creation and LLM testing.

```
packages/forge-agents/
├── src/
│   ├── builder/
│   │   ├── definition.py       # Agent definition schema
│   │   ├── compiler.py         # Compile to LangGraph
│   │   ├── tools.py            # Tool registration
│   │   └── approval.py         # Human-in-the-loop
│   │
│   ├── evaluate/
│   │   ├── suites.py           # Test suite management
│   │   ├── runners.py          # Test execution
│   │   ├── evaluators/
│   │   │   ├── exact.py        # Exact match
│   │   │   ├── semantic.py     # Semantic similarity
│   │   │   ├── llm_judge.py    # LLM-as-judge
│   │   │   └── factuality.py   # Fact checking
│   │   └── reports.py          # Evaluation reports
│   │
│   └── api/
│       └── routes.py
│
└── tests/
```

---

### 7. forge-vectors (Embeddings + RAG)

**Purpose:** Vector storage, embeddings, and semantic search.

```
packages/forge-vectors/
├── src/
│   ├── embeddings/
│   │   ├── providers.py        # OpenAI, Sentence Transformers
│   │   └── cache.py            # Embedding cache
│   │
│   ├── stores/
│   │   ├── pgvector.py         # PostgreSQL pgvector
│   │   └── qdrant.py           # Qdrant (optional)
│   │
│   ├── search/
│   │   ├── knn.py              # k-NN search
│   │   ├── hybrid.py           # Hybrid keyword + semantic
│   │   └── rerank.py           # Result reranking
│   │
│   ├── chunking/
│   │   └── strategies.py       # Text chunking strategies
│   │
│   └── api/
│       └── routes.py
│
└── tests/
```

---

### 8. forge-studio (Unified App Builder)

**Purpose:** Single package for low-code app building with progressive disclosure.

```
packages/forge-studio/
├── src/
│   ├── components/
│   │   ├── Editor/             # Main editor component
│   │   ├── Canvas/             # Drag-and-drop canvas
│   │   ├── WidgetPanel/        # Widget library
│   │   ├── ConfigPanel/        # Configuration panel
│   │   └── CodeEditor/         # Monaco code editor
│   │
│   ├── widgets/
│   │   ├── ObjectTable/
│   │   ├── ObjectDetail/
│   │   ├── Form/
│   │   ├── Chart/
│   │   ├── MetricCard/
│   │   ├── Text/
│   │   ├── FilterBar/
│   │   └── ActionButton/
│   │
│   ├── runtime/
│   │   ├── AppRenderer.tsx     # Published app renderer
│   │   ├── DataLoader.tsx      # Data fetching layer
│   │   └── StateManager.tsx    # Runtime state
│   │
│   ├── lib/
│   │   ├── bindings.ts         # Data binding system
│   │   ├── actions.ts          # Action execution
│   │   └── serialization.ts    # App definition serialization
│   │
│   └── api/
│       └── routes.py           # App CRUD endpoints
│
└── tests/
```

---

### 9. forge-analytics (Lens + Prism + Browser)

**Purpose:** Unified analytics tools for object and tabular analysis.

```
packages/forge-analytics/
├── src/
│   ├── lens/                   # Object-driven analysis
│   │   ├── ObjectView.tsx
│   │   ├── RelationshipGraph.tsx
│   │   └── TimelineView.tsx
│   │
│   ├── prism/                  # Tabular analysis
│   │   ├── DataGrid.tsx
│   │   ├── Pivot.tsx
│   │   └── Aggregations.tsx
│   │
│   ├── browser/                # Object explorer
│   │   ├── Search.tsx
│   │   ├── ObjectList.tsx
│   │   └── Filters.tsx
│   │
│   └── shared/
│       ├── hooks/
│       └── utils/
│
└── tests/
```

---

### 10. forge-geo (Geo Core + Atlas)

**Purpose:** Geospatial primitives and map visualization.

```
packages/forge-geo/
├── src/
│   ├── core/
│   │   ├── types.py            # Point, Polygon, Line
│   │   ├── indexes.py          # H3, PostGIS integration
│   │   └── queries.py          # Spatial queries
│   │
│   ├── atlas/
│   │   ├── Map.tsx
│   │   ├── layers/
│   │   │   ├── PointLayer.tsx
│   │   │   ├── PolygonLayer.tsx
│   │   │   ├── ClusterLayer.tsx
│   │   │   └── HeatmapLayer.tsx
│   │   └── controls/
│   │
│   └── api/
│       └── routes.py
│
└── tests/
```

---

### 11. forge-media (Documents + Vision)

**Purpose:** Document processing and OCR. Video/voice deferred.

```
packages/forge-media/
├── src/
│   ├── core/
│   │   ├── media_set.py
│   │   └── storage.py          # Uses forge-core storage
│   │
│   ├── documents/
│   │   ├── extractors/
│   │   │   ├── pdf.py
│   │   │   ├── docx.py
│   │   │   └── xlsx.py
│   │   └── chunking.py
│   │
│   ├── vision/
│   │   ├── ocr.py              # Tesseract, Vision API
│   │   └── processing.py       # Image processing
│   │
│   └── api/
│       └── routes.py
│
└── tests/
```

---

### 12. forge-collab (Sharing + Alerts + Audit)

**Purpose:** Collaboration features with proper permission batching.

```
packages/forge-collab/
├── src/
│   ├── sharing/
│   │   ├── permissions.py      # Uses forge-core auth
│   │   ├── batch.py            # Batched permission checks
│   │   └── links.py            # Shareable links
│   │
│   ├── alerts/
│   │   ├── rules.py            # Alert rule definitions
│   │   ├── channels.py         # Email, Slack, webhook
│   │   └── notifications.py
│   │
│   ├── audit/
│   │   ├── logger.py           # Audit event logging
│   │   ├── query.py            # Audit log queries
│   │   └── export.py           # Compliance exports
│   │
│   └── api/
│       └── routes.py
│
└── tests/
```

**Batched Permission Checks:**

```python
class PermissionService:
    async def check_batch(
        self,
        user: User,
        checks: list[tuple[str, str]]  # (resource, action)
    ) -> dict[str, bool]:
        """Check multiple permissions in single query."""
        # Single database round-trip for N permissions
        ...
```

---

### 13. forge-deploy (Orbit CD Only)

**Purpose:** GitOps deployment. Edge/marketplace deferred.

```
packages/forge-deploy/
├── src/
│   ├── products/
│   │   ├── product.py          # Product definitions
│   │   ├── bundle.py           # Resource bundling
│   │   └── version.py          # Version management
│   │
│   ├── deployment/
│   │   ├── gitops.py           # GitOps sync
│   │   ├── rollout.py          # Gradual rollout
│   │   └── rollback.py         # Rollback automation
│   │
│   ├── environments/
│   │   ├── environment.py      # Environment definitions
│   │   └── promotion.py        # Promotion workflows
│   │
│   └── api/
│       └── routes.py
│
└── tests/
```

---

## Package Dependencies

```
                                    ┌─────────────────┐
                                    │   forge-core    │
                                    │ (auth, events,  │
                                    │ storage, gw)    │
                                    └────────┬────────┘
                                             │
        ┌────────────────────────────────────┼────────────────────────────────────┐
        │                                    │                                    │
        ▼                                    ▼                                    ▼
   ┌─────────┐                        ┌───────────┐                        ┌───────────┐
   │   api   │◄───────────────────────┤ ontology  │                        │ pipelines │
   └────┬────┘                        └─────┬─────┘                        └─────┬─────┘
        │                                   │                                    │
        └───────────────────────────────────┼────────────────────────────────────┘
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        │               │                   │                   │               │
        ▼               ▼                   ▼                   ▼               ▼
┌───────────────┐ ┌───────────┐     ┌─────────────┐     ┌───────────┐   ┌────────────┐
│forge-connectors│ │transforms │     │  forge-ai   │     │forge-media│   │ forge-geo  │
└───────┬───────┘ └─────┬─────┘     └──────┬──────┘     └─────┬─────┘   └──────┬─────┘
        │               │                  │                  │                │
        └───────────────┴──────────────────┴──────────────────┴────────────────┘
                                           │
        ┌──────────────────────────────────┼──────────────────────────────────┐
        │                                  │                                  │
        ▼                                  ▼                                  ▼
   ┌─────────┐                      ┌───────────┐                      ┌───────────┐
   │   ui    │                      │forge-studio│                     │ analytics │
   └─────────┘                      └───────────┘                      └───────────┘
```

---

## Deferred Components (Post-MVP)

The following components are **explicitly deferred** to reduce MVP scope:

| Component | Original Package | Reason for Deferral |
|-----------|------------------|---------------------|
| Edge deployment | forge-edge | Niche use case, complex sync |
| Marketplace | forge-exchange | Requires ecosystem first |
| MLOps | forge-ml | Focus on LLM, not traditional ML |
| Movement tracking | forge-tracks | Advanced geo feature |
| Route analysis | forge-routes | Advanced geo feature |
| Video processing | forge-video | Complex, low initial demand |
| Voice/transcription | forge-voice | Can use external services |
| Spark transforms | transforms-spark | DataFusion sufficient for MVP |
| Flink streaming | transforms-flink | DataFusion streaming sufficient |
| Full-code canvas | forge-canvas | Progressive disclosure handles this |

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Critical path - unblocks everything else.**

| Package | Key Deliverables |
|---------|------------------|
| **forge-core** | Auth middleware, RBAC, event bus (Redis), storage abstraction |
| **api** | GraphQL schema updates, auth integration |
| **ontology** | Row-level security integration |

### Phase 2: Data Layer (Weeks 3-6)

| Package | Key Deliverables |
|---------|------------------|
| **forge-connectors** | SQL + warehouse connectors, connection pooling |
| **forge-transforms** | DataFusion engine, incremental processing |
| **forge-data** | Quality checks, lineage (bounded), branches |

### Phase 3: AI Layer (Weeks 4-8)

| Package | Key Deliverables |
|---------|------------------|
| **forge-ai** | LiteLLM integration, Logic functions, injection detection |
| **forge-vectors** | pgvector store, embedding pipeline |
| **forge-agents** | Agent builder, basic evaluation |

### Phase 4: Application Layer (Weeks 5-10)

| Package | Key Deliverables |
|---------|------------------|
| **forge-studio** | Editor, 8 MVP widgets, runtime |
| **forge-analytics** | Object browser, basic grid |
| **forge-geo** | PostGIS integration, basic map |

### Phase 5: Operations (Weeks 8-12)

| Package | Key Deliverables |
|---------|------------------|
| **forge-media** | PDF extraction, OCR |
| **forge-collab** | Sharing with batched permissions, alerts |
| **forge-deploy** | Orbit GitOps deployment |

---

## Package Count Summary

| Layer | Packages | Count |
|-------|----------|-------|
| **Foundation** | forge-core, api, ontology, agents, pipelines | 5 |
| **Data** | forge-connectors, forge-transforms, forge-data, forge-vectors | 4 |
| **AI** | forge-ai, forge-agents | 2 |
| **Application** | ui, forge-studio, forge-analytics, forge-geo | 4 |
| **Operations** | forge-media, forge-collab, forge-deploy | 3 |
| **Tools** | forge-cli, forge-sdk-python | 2 |
| **TOTAL** | | **20** |

---

## Migration from Original Architecture

For teams that began work on the original 64-package architecture:

| Original Package(s) | Consolidated To |
|---------------------|-----------------|
| connectors-core, connectors-sql, connectors-warehouse, connectors-nosql, connectors-streaming, connectors-erp, connectors-crm, connectors-cloud, connectors-files, connectors-api | **forge-connectors** |
| transforms-core, transforms-spark, transforms-flink, transforms-datafusion | **forge-transforms** |
| forge-quality, forge-lineage, forge-branches, forge-navigator, forge-federation | **forge-data** |
| forge-ai-core, forge-logic, forge-copilot, forge-automate | **forge-ai** |
| forge-agent-builder, forge-evaluate | **forge-agents** |
| forge-vectors | **forge-vectors** |
| forge-studio, forge-studio-runtime, forge-studio-widgets, forge-canvas | **forge-studio** |
| forge-lens, forge-prism, forge-browser, forge-hub | **forge-analytics** |
| forge-geo-core, forge-atlas, forge-tracks, forge-routes | **forge-geo** |
| forge-media-core, forge-documents, forge-vision, forge-voice, forge-video | **forge-media** |
| forge-sharing, forge-collections, forge-alerts, forge-audit | **forge-collab** |
| forge-orbit, forge-exchange, forge-edge, forge-consumer | **forge-deploy** |
| (new) | **forge-core** |

---

## Review Findings Addressed

This architecture addresses the P1/P2 findings from the multi-agent review:

| Finding | Resolution |
|---------|------------|
| P1: Missing centralized authentication | Added forge-core with auth module |
| P1: No authorization enforcement | RBAC + row-level security in forge-core |
| P1: Secrets exposure risk | Vault integration in forge-connectors |
| P1: LLM injection detection weak | Multi-layer detection in forge-ai |
| P2: Over-engineered (64 packages) | Reduced to 20 packages |
| P2: N+1 permission queries | Batched checks in forge-collab |
| P2: Unbounded lineage graph | Max depth/nodes limits in forge-data |
| P2: Missing connection pooling | Added to forge-connectors |
| P2: No event bus | Added to forge-core |
| P2: Edge/marketplace premature | Deferred post-MVP |

---

## Next Steps

### Completed (Phase 1 Foundation)

- [x] Create forge-core package scaffold with auth module
- [x] Implement RBAC and auth middleware
- [x] Create JWT authentication provider
- [x] Integrate forge-core auth into api package
- [x] Integrate forge-core event bus into api package
- [x] Integrate forge-core storage abstraction into api package
- [x] Integrate forge-core gateway (rate limiting, circuit breaker) into api package

### In Progress

1. **Phase 2 - Data Layer**: Develop forge-connectors, forge-transforms, forge-data
2. **Phase 3 - AI Layer**: Develop forge-ai integration with actual LLM providers

### Upcoming

4. **Ongoing**: Use `/workflows:review` before merging each package

---

## Appendix: Comparison with Original

| Metric | Original | Consolidated | Improvement |
|--------|----------|--------------|-------------|
| Package count | 64 | 20 | 69% reduction |
| Transform engines | 4 | 1 | 75% reduction |
| Connector packages | 10 | 1 | 90% reduction |
| Missing auth | Yes | No | Critical fix |
| Missing events | Yes | No | Critical fix |
| Edge/marketplace | Included | Deferred | Scope reduction |

This consolidated architecture maintains the same functional goals while providing:
- Clearer ownership boundaries
- Reduced coordination overhead
- Faster time to MVP
- Critical infrastructure from day one
