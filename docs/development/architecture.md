# System Architecture Overview

This document describes the architecture of Open Forge.

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [System Layers](#system-layers)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Design Decisions](#design-decisions)

---

## High-Level Architecture

Open Forge is designed as a multi-layered system that automates Forward Deployed Engineering (FDE) tasks using AI agents.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Customer Portal │  │ Admin Dashboard │  │  Approval UI    │              │
│  │  (React/Next)   │  │  (React/Next)   │  │  (React/Next)   │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
└───────────┼────────────────────┼────────────────────┼────────────────────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
┌────────────────────────────────▼─────────────────────────────────────────────┐
│                               API GATEWAY                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI (REST + GraphQL + WebSocket)               │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────────────┐
│                            ORCHESTRATION LAYER                                │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │             LangGraph Orchestrator + Agent Registry                    │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└─────┬────────────────────────────┬────────────────────────────┬──────────────┘
      │                            │                            │
┌─────▼─────┐              ┌───────▼───────┐            ┌───────▼───────┐
│ Discovery │              │ Data Architect│            │  App Builder  │
│  Cluster  │              │    Cluster    │            │    Cluster    │
├───────────┤              ├───────────────┤            ├───────────────┤
│Stakeholder│              │Ontology Design│            │ UI Generator  │
│Requirements              │Schema Validate│            │   Workflows   │
│Source Disc.│             │Transformation │            │  Deployment   │
└─────┬─────┘              └───────┬───────┘            └───────┬───────┘
      │                            │                            │
└─────┴────────────────────────────┴────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────────────┐
│                              CORE SERVICES                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐   │
│  │  Ontology   │  │  Pipeline   │  │  Connector  │  │   Code Gen        │   │
│  │   Engine    │  │   Engine    │  │  Framework  │  │   Engine          │   │
│  │  (LinkML)   │  │  (Dagster)  │  │ (DB/API/S3) │  │ (Multi-target)    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────────────┐
│                           DATA & INFRASTRUCTURE                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐   │
│  │ PostgreSQL  │  │ Apache AGE  │  │   Redis     │  │      MinIO        │   │
│  │ + pgvector  │  │   (Graph)   │  │ (Cache/MQ)  │  │  (Object Store)   │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐                                           │
│  │   Iceberg   │  │   Jaeger    │                                           │
│  │ (Data Lake) │  │  (Tracing)  │                                           │
│  └─────────────┘  └─────────────┘                                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## System Layers

### Layer 1: Presentation

The user interface layer provides different views for different user roles.

| Component | Purpose | Technology |
|-----------|---------|------------|
| Customer Portal | Engagement management, progress tracking | React, Next.js |
| Admin Dashboard | System monitoring, configuration | React, Next.js |
| Approval UI | Human-in-the-loop approvals | React, WebSocket |

### Layer 2: API Gateway

Unified API entry point for all client applications.

```
packages/api/
├── src/api/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── dependencies.py   # Dependency injection
│   ├── routers/          # REST endpoints
│   │   ├── health.py
│   │   ├── engagements.py
│   │   ├── agents.py
│   │   ├── data_sources.py
│   │   └── approvals.py
│   ├── graphql/          # GraphQL schema
│   │   ├── schema.py
│   │   ├── types.py
│   │   └── resolvers.py
│   └── schemas/          # Pydantic models
│       ├── common.py
│       ├── engagement.py
│       └── agent.py
```

**Responsibilities:**
- Request routing and validation
- Authentication and authorization
- Rate limiting
- Request logging and tracing

### Layer 3: Orchestration

Coordinates AI agents and manages workflow execution.

```
packages/agents/src/agents/orchestrator/
├── orchestrator.py    # Main Orchestrator Agent
├── phase_manager.py   # Phase lifecycle management
├── router.py          # Task routing to clusters
├── events.py          # Event handling
└── workflow.py        # Workflow state machine
```

**Main Orchestrator Responsibilities:**
- Route tasks to appropriate agent clusters
- Manage engagement phase transitions
- Enforce quality gates
- Handle human-in-the-loop checkpoints

### Layer 4: Agent Clusters

Specialized agent groups for different tasks.

#### Discovery Cluster
```
packages/agents/src/agents/discovery/
├── stakeholder_agent.py      # Analyze stakeholders
├── requirements_agent.py     # Gather requirements
└── source_discovery_agent.py # Discover data sources
```

#### Data Architect Cluster
```
packages/agents/src/agents/data_architect/
├── ontology_designer_agent.py    # Design schemas
├── schema_validator_agent.py     # Validate schemas
└── transformation_agent.py       # Design transforms
```

#### App Builder Cluster
```
packages/agents/src/agents/app_builder/
├── workflow_agent.py       # Create workflows
├── integration_agent.py    # Build integrations
└── deployment_agent.py     # Deploy applications
```

### Layer 5: Core Services

Foundational services used by all components.

#### Ontology Engine
```
packages/ontology/
├── src/ontology/
│   ├── models.py      # Schema models
│   ├── schema.py      # Schema manager
│   ├── compiler.py    # Multi-target compiler
│   └── generators/    # Code generators
│       ├── sql_generator.py
│       ├── cypher_generator.py
│       ├── pydantic_generator.py
│       ├── typescript_generator.py
│       └── graphql_generator.py
```

#### Pipeline Engine
```
packages/pipelines/
├── src/pipelines/
│   ├── definitions.py    # Dagster definitions
│   ├── resources.py      # Resource definitions
│   ├── io_managers.py    # IO managers
│   ├── assets/           # Asset definitions
│   ├── jobs/             # Job definitions
│   └── sensors/          # Sensor definitions
```

#### Connector Framework
```
packages/connectors/
├── src/connectors/
│   ├── base.py           # Base connector
│   ├── database/         # Database connectors
│   │   ├── postgres.py
│   │   └── mysql.py
│   ├── api/              # API connectors
│   │   ├── rest.py
│   │   └── graphql.py
│   └── file/             # File connectors
│       ├── csv.py
│       ├── parquet.py
│       └── s3.py
```

### Layer 6: Data & Infrastructure

Persistent storage and infrastructure services.

| Service | Purpose | Technology |
|---------|---------|------------|
| PostgreSQL | Relational data, metadata | PostgreSQL 15+ |
| Apache AGE | Graph data (knowledge graphs) | PostgreSQL extension |
| pgvector | Vector embeddings | PostgreSQL extension |
| Redis | Caching, message queue | Redis 7+ |
| MinIO | Object storage | S3-compatible |
| Iceberg | Data lake tables | Apache Iceberg |
| Jaeger | Distributed tracing | OpenTelemetry |

---

## Component Details

### Agent Framework

All agents inherit from `BaseOpenForgeAgent`:

```python
class BaseOpenForgeAgent(ABC, Generic[InputT, OutputT]):
    """Base interface for all agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Agent description."""

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT:
        """Execute agent task."""

    @abstractmethod
    def build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""

    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Return available tools."""
```

**Agent State Management:**
```python
class AgentState(TypedDict):
    """State passed between graph nodes."""
    messages: Annotated[List[BaseMessage], add_messages]
    agent_context: Dict[str, Any]
    current_step: str
    outputs: Dict[str, Any]
    decisions: List[Decision]
    requires_human_review: bool
    review_reason: Optional[str]
```

### Event System

Redis-based pub/sub for real-time events:

```python
class EventBus:
    """Event bus for inter-component communication."""

    async def publish(self, event_type: str, data: dict) -> None:
        """Publish an event."""

    async def subscribe(self, event_type: str) -> AsyncIterator[dict]:
        """Subscribe to events."""
```

**Event Types:**
- `engagement.created`
- `engagement.phase.changed`
- `agent.task.started`
- `agent.task.completed`
- `agent.task.failed`
- `approval.requested`
- `approval.decided`

### Human-in-the-Loop

Integration points for human oversight:

```python
class ApprovalManager:
    """Manages approval workflows."""

    async def request_approval(
        self,
        approval_type: str,
        title: str,
        items_to_review: List[dict],
        timeout_minutes: int = 60
    ) -> str:
        """Request human approval."""

    async def wait_for_decision(
        self,
        approval_id: str
    ) -> ApprovalDecision:
        """Wait for approval decision."""
```

---

## Data Flow

### Engagement Lifecycle

```
User Creates Engagement
         │
         ▼
┌─────────────────┐
│   Draft State   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│    Discovery    │────▶│  Quality Gate   │
│     Phase       │     │    Review       │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│     Design      │────▶│  Quality Gate   │
│     Phase       │     │    Review       │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│     Build       │────▶│  Quality Gate   │
│     Phase       │     │    Review       │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│     Deploy      │────▶│    Final        │
│     Phase       │     │   Approval      │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Completed     │
└─────────────────┘
```

### Data Pipeline Flow

```
Source Systems            Open Forge                    Outputs
─────────────────    ─────────────────────    ─────────────────────
                           Connectors
PostgreSQL    ─────▶   ┌─────────────┐
MySQL         ─────▶   │  Ingestion  │
S3            ─────▶   │   Assets    │   ─────▶   Iceberg Tables
APIs          ─────▶   └──────┬──────┘            (Data Lake)
CSV/Parquet   ─────▶          │
                              ▼
                     ┌─────────────────┐
                     │ Transformation  │   ─────▶   PostgreSQL
                     │    Assets       │            (Serving Layer)
                     └──────┬──────────┘
                            │
                            ▼
                     ┌─────────────────┐
                     │    Ontology     │   ─────▶   Graph (AGE)
                     │   Compliance    │            (Relationships)
                     └─────────────────┘
```

---

## Technology Stack

### Core Technologies

| Category | Technology | Purpose |
|----------|------------|---------|
| **Backend Framework** | FastAPI | REST API, async support |
| **AI Framework** | LangChain, LangGraph | Agent orchestration |
| **LLM Provider** | Anthropic Claude | AI reasoning |
| **Pipeline** | Dagster | Data orchestration |
| **Database** | PostgreSQL | Primary data store |
| **Graph** | Apache AGE | Graph queries |
| **Cache** | Redis | Caching, pub/sub |
| **Object Storage** | MinIO | S3-compatible storage |
| **Data Lake** | Apache Iceberg | Table format |
| **Tracing** | OpenTelemetry + Jaeger | Observability |

### Python Dependencies

```toml
[project]
dependencies = [
    # Core
    "pydantic>=2.0",
    "pydantic-settings>=2.0",

    # LLM & Agents
    "langchain>=0.3",
    "langchain-anthropic>=0.3",
    "langgraph>=0.2",

    # Data
    "polars>=1.0",
    "sqlalchemy>=2.0",
    "asyncpg>=0.29",

    # Pipeline
    "dagster>=1.7",

    # API
    "fastapi>=0.110",
    "strawberry-graphql>=0.220",

    # Observability
    "opentelemetry-api>=1.20",
]
```

---

## Design Decisions

### Why LangGraph for Agents?

- **Structured workflows**: Define clear state transitions
- **Human-in-the-loop**: Built-in interrupt support
- **Persistence**: Checkpoint and resume workflows
- **Observability**: Integration with LangSmith

### Why Dagster for Pipelines?

- **Asset-centric**: Focus on data products
- **Type safety**: Pydantic integration
- **Testability**: Easy unit testing
- **Observability**: Built-in lineage tracking

### Why PostgreSQL + Apache AGE?

- **Single database**: Reduces operational complexity
- **Graph queries**: Native graph support via AGE
- **Vectors**: pgvector for embeddings
- **Mature ecosystem**: Proven reliability

### Why MinIO + Iceberg?

- **Cloud-native**: S3-compatible API
- **Time travel**: Iceberg snapshot isolation
- **Schema evolution**: Iceberg handles schema changes
- **Portability**: Easy migration to cloud storage

### Why FastAPI?

- **Async native**: High performance
- **Type hints**: Automatic validation
- **OpenAPI**: Auto-generated docs
- **GraphQL**: Easy Strawberry integration

---

## Related Documentation

- [Local Setup Guide](./local-setup.md)
- [Testing Guide](./testing.md)
- [Contributing Guide](./contributing.md)
- [API Reference](../api/openapi.yaml)
