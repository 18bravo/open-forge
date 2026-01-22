<p align="center">
  <img src="packages/ui/public/open-forge-logo.svg" alt="Open Forge Logo" width="120" height="120" />
</p>

<h1 align="center">Open Forge</h1>

<p align="center">
  <strong>Open-Source Enterprise Data Platform with AI-Powered Automation</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/node-20+-green.svg" alt="Node 20+" />
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License" />
  <img src="https://img.shields.io/badge/status-Production%20Ready-success.svg" alt="Status" />
</p>

---

## Overview

**Open Forge** is a comprehensive, enterprise-grade data platform that democratizes advanced data operations. It combines AI agents powered by Claude/LangChain with robust data orchestration to automate complex data engineering tasks that traditionally require expensive consultants and lengthy implementation cycles.

### The Problem We Solve

Enterprise data platforms typically require:
- **High annual costs** for proprietary software licenses
- **Expensive professional services** for implementation and customization
- **Long deployment cycles** to see initial value
- **Vendor lock-in** with proprietary tooling and formats

### Our Solution

Open Forge delivers:
- **100% open source** — No license fees, no vendor lock-in
- **AI-powered automation** — Agents handle repetitive data engineering tasks
- **Human-in-the-loop** — Experts review and approve AI decisions
- **Rapid time to value** — Days instead of months
- **Production-ready** — Complete CI/CD, monitoring, and security hardening

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Development Guide](#development-guide)
- [Package Documentation](#package-documentation)
- [Agent Architecture](#agent-architecture)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Core Platform Capabilities

| Feature | Description |
|---------|-------------|
| **Ontology Engine** | LinkML-based schema compiler generating SQL, Cypher, Pydantic, TypeScript, and GraphQL |
| **Data Connectors** | PostgreSQL, MySQL, Snowflake, BigQuery, Kafka, S3, REST, GraphQL, and more |
| **Pipeline Orchestration** | Dagster-powered data pipelines with visual canvas design |
| **AI Agent Clusters** | 6 specialized agent clusters with 25+ individual agents |
| **Human-in-the-Loop** | Approval workflows, review queues, and feedback collection |
| **Code Generation** | Automatic FastAPI, ORM, tests, and React hooks generation |
| **Visual Canvases** | Langflow for agent workflows, React Flow for pipeline design |
| **Observability** | LangSmith integration, OpenTelemetry tracing, Prometheus metrics |

### AI Agent Clusters

| Cluster | Purpose | Agents |
|---------|---------|--------|
| **Discovery** | Understand business needs | Stakeholder, Source Discovery, Requirements |
| **Data Architect** | Design data models | Ontology Designer, Schema Validator, Transformation |
| **App Builder** | Generate applications | UI Generator, Workflow, Integration, Deployment |
| **Operations** | Manage infrastructure | Monitoring, Scaling, Maintenance, Incident |
| **Enablement** | Create documentation | Documentation, Training, Support |
| **Orchestrator** | Coordinate all clusters | Phase management, task routing, priority queues |

### Platform Components

Open Forge provides a consolidated set of 20 packages across 5 layers:

| Layer | Packages | Description |
|-------|----------|-------------|
| **Foundation** | forge-core, api, ontology, agents, pipelines | Core infrastructure and services |
| **Data** | forge-connectors, forge-transforms, forge-data, forge-vectors | Data connectivity and processing |
| **AI** | forge-ai, forge-agents | Multi-LLM platform and agent builder |
| **Application** | ui, forge-studio, forge-analytics, forge-geo | User interfaces and analytics |
| **Operations** | forge-media, forge-collab, forge-deploy | Media processing, collaboration, deployment |

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   Next.js UI    │  │  Langflow Agent │  │   React Flow Pipeline      │  │
│  │   (Portal)      │  │     Canvas      │  │        Canvas              │  │
│  └────────┬────────┘  └────────┬────────┘  └─────────────┬───────────────┘  │
└───────────┼─────────────────────┼────────────────────────┼──────────────────┘
            │                     │                        │
            ▼                     ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                API GATEWAY                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   FastAPI REST  │  │    Strawberry   │  │    WebSocket SSE           │  │
│  │   Endpoints     │  │    GraphQL      │  │    Real-time Streams       │  │
│  └────────┬────────┘  └────────┬────────┘  └─────────────┬───────────────┘  │
└───────────┼─────────────────────┼────────────────────────┼──────────────────┘
            │                     │                        │
            ▼                     ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ORCHESTRATION LAYER                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   LangGraph     │  │  Agent Registry │  │     State Manager          │  │
│  │   Workflows     │  │  (Supervisor)   │  │   (PostgresSaver)          │  │
│  └────────┬────────┘  └────────┬────────┘  └─────────────┬───────────────┘  │
└───────────┼─────────────────────┼────────────────────────┼──────────────────┘
            │                     │                        │
            ▼                     ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGENT CLUSTERS                                  │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐  │
│  │ Discovery │ │   Data    │ │    App    │ │Operations │ │  Enablement   │  │
│  │  Cluster  │ │ Architect │ │  Builder  │ │  Cluster  │ │   Cluster     │  │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └───────┬───────┘  │
└────────┼─────────────┼─────────────┼─────────────┼───────────────┼──────────┘
         │             │             │             │               │
         ▼             ▼             ▼             ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CORE SERVICES                                   │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐  │
│  │  Ontology │ │  Pipeline │ │Connectors │ │  CodeGen  │ │    Human      │  │
│  │  Engine   │ │  Engine   │ │           │ │  Engine   │ │  Interaction  │  │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └───────┬───────┘  │
└────────┼─────────────┼─────────────┼─────────────┼───────────────┼──────────┘
         │             │             │             │               │
         ▼             ▼             ▼             ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA INFRASTRUCTURE                                │
│  ┌───────────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │ PostgreSQL + AGE  │  │    Redis    │  │    MinIO    │  │   Iceberg    │  │
│  │ + pgvector        │  │  (Streams)  │  │    (S3)     │  │  (Catalog)   │  │
│  └───────────────────┘  └─────────────┘  └─────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   User       │     │  Engagement  │     │   Agent      │     │   Human      │
│   Request    │────▶│   Created    │────▶│   Execution  │────▶│   Review     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                │                      │
                                                ▼                      ▼
                                          ┌──────────────┐     ┌──────────────┐
                                          │   Code       │     │   Approval   │
                                          │   Generated  │◀────│   Workflow   │
                                          └──────────────┘     └──────────────┘
                                                │
                                                ▼
                                          ┌──────────────┐
                                          │   Deployed   │
                                          │   Solution   │
                                          └──────────────┘
```

### Agent Workflow Pattern

All agents follow the ReAct (Reasoning + Acting) pattern with memory tools:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SUPERVISOR ORCHESTRATOR                           │
│                    (LangGraph create_supervisor)                         │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Discovery     │  │  Data Architect │  │   App Builder   │
│   ReAct Agent   │  │   ReAct Agent   │  │   ReAct Agent   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ • remember()    │  │ • remember()    │  │ • remember()    │
│ • recall()      │  │ • recall()      │  │ • recall()      │
│ • stakeholder   │  │ • design_onto   │  │ • generate_ui   │
│ • discover_src  │  │ • validate      │  │ • build_wkflow  │
│ • gather_reqs   │  │ • transform     │  │ • integrate     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │  PostgresStore      │
                    │  (Long-term Memory) │
                    └─────────────────────┘
```

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Core runtime |
| **FastAPI** | 0.110+ | REST API framework |
| **Strawberry** | 0.220+ | GraphQL server |
| **LangChain** | 0.3+ | LLM framework |
| **LangGraph** | 0.2+ | Agent orchestration |
| **LangSmith** | 0.1+ | Observability |
| **Dagster** | 1.7+ | Pipeline orchestration |
| **SQLAlchemy** | 2.0+ | ORM |
| **Pydantic** | 2.0+ | Data validation |
| **Polars** | 1.0+ | Data processing |
| **Redis** | 5.0+ | Messaging & caching |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.1+ | React framework |
| **React** | 19.2+ | UI library |
| **TypeScript** | 5.3+ | Type safety |
| **TailwindCSS** | 3.4+ | Styling |
| **Radix UI** | Latest | Headless components |
| **TanStack Query** | 5.17+ | Server state |
| **Framer Motion** | 12.27+ | Animations |
| **Three.js** | 0.182+ | 3D graphics |
| **React Flow** | Latest | Pipeline canvas |
| **Recharts** | 3.6+ | Charts |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| **PostgreSQL + Apache AGE** | Relational + Graph database |
| **pgvector** | Vector embeddings for RAG |
| **Redis** | Event streaming & caching |
| **MinIO** | S3-compatible object storage |
| **Apache Iceberg** | Data lake catalog |
| **Jaeger** | Distributed tracing |
| **Docker** | Containerization |
| **Kubernetes** | Container orchestration |
| **Helm** | Package management |
| **Prometheus** | Metrics collection |
| **Grafana** | Dashboards & visualization |

### AI/LLM

| Technology | Purpose |
|------------|---------|
| **Claude (Anthropic)** | Primary LLM provider |
| **LiteLLM** | Multi-provider abstraction |
| **MCP (Model Context Protocol)** | Tool extensibility |
| **Langflow** | Visual agent canvas |

---

## Project Structure

```
open-forge/
├── packages/                          # Monorepo packages
│   │
│   ├── forge-core/                    # Auth, events, storage, gateway
│   │   └── src/forge_core/
│   │       ├── auth/                  # OAuth2/OIDC, RBAC, row-level security
│   │       ├── events/                # Event bus (Redis, PostgreSQL)
│   │       ├── storage/               # Storage abstraction (S3, MinIO)
│   │       └── gateway/               # Rate limiting, circuit breaker
│   │
│   ├── api/                           # FastAPI backend
│   │   └── src/api/
│   │       ├── main.py                # Application entry point
│   │       ├── routers/               # API route handlers
│   │       └── auth.py                # Authentication middleware
│   │
│   ├── ontology/                      # LinkML ontology compiler
│   │   └── src/ontology/
│   │       ├── parser/                # LinkML YAML parser
│   │       └── generators/            # SQL, Cypher, Pydantic, TS, GraphQL
│   │
│   ├── agents/                        # LangGraph agent implementations
│   │   └── src/agents/
│   │       ├── discovery/             # Business understanding agents
│   │       ├── data_architect/        # Data modeling agents
│   │       ├── app_builder/           # Application building agents
│   │       └── orchestrator/          # Supervisor orchestrator
│   │
│   ├── pipelines/                     # Dagster pipeline definitions
│   │   └── src/pipelines/
│   │       ├── assets/                # Dagster asset definitions
│   │       └── jobs/                  # Pipeline job definitions
│   │
│   ├── forge-connectors/              # Unified data connectors
│   │   └── src/forge_connectors/
│   │       ├── core/                  # Base connector, registry, pooling
│   │       ├── sync/                  # Batch, CDC, streaming, writeback
│   │       └── connectors/            # SQL, warehouse, cloud, API
│   │
│   ├── forge-transforms/              # DataFusion transforms
│   │   └── src/forge_transforms/
│   │       ├── engine/                # DataFusion execution
│   │       └── incremental/           # Incremental processing
│   │
│   ├── forge-data/                    # Quality, lineage, branches
│   │   └── src/forge_data/
│   │       ├── quality/               # Data health checks
│   │       ├── lineage/               # Provenance tracking
│   │       └── branches/              # Dataset versioning
│   │
│   ├── forge-ai/                      # Multi-LLM core
│   │   └── src/forge_ai/
│   │       ├── providers/             # LiteLLM integration
│   │       ├── logic/                 # No-code LLM functions
│   │       └── security/              # PII filter, guardrails
│   │
│   ├── forge-agents/                  # Agent builder + evaluate
│   │   └── src/forge_agents/
│   │       ├── builder/               # Visual agent definition
│   │       └── evaluate/              # LLM testing framework
│   │
│   ├── forge-vectors/                 # Embeddings + RAG
│   │   └── src/forge_vectors/
│   │       ├── embeddings/            # Embedding providers
│   │       ├── stores/                # pgvector, Qdrant
│   │       └── search/                # Semantic search
│   │
│   ├── ui/                            # Next.js frontend
│   │   └── src/
│   │       ├── app/                   # Next.js App Router pages
│   │       └── components/            # React components
│   │
│   ├── forge-studio/                  # Low-code app builder
│   │   └── src/forge_studio/
│   │       ├── components/            # Editor, canvas, panels
│   │       ├── widgets/               # Table, form, chart, etc.
│   │       └── runtime/               # Published app renderer
│   │
│   ├── forge-analytics/               # Object + tabular analysis
│   │   └── src/forge_analytics/
│   │       ├── lens/                  # Object-driven analysis
│   │       ├── prism/                 # Tabular analysis
│   │       └── browser/               # Object explorer
│   │
│   ├── forge-geo/                     # Geospatial capabilities
│   │   └── src/forge_geo/
│   │       ├── core/                  # Spatial primitives, H3
│   │       └── atlas/                 # Map visualization
│   │
│   ├── forge-media/                   # Media processing
│   │   └── src/forge_media/
│   │       ├── documents/             # PDF, DOCX extraction
│   │       └── vision/                # OCR, image processing
│   │
│   ├── forge-collab/                  # Collaboration features
│   │   └── src/forge_collab/
│   │       ├── sharing/               # Permissions, links
│   │       ├── alerts/                # Notifications
│   │       └── audit/                 # Audit logging
│   │
│   └── forge-deploy/                  # Deployment platform
│       └── src/forge_deploy/
│           ├── products/              # Product definitions
│           └── deployment/            # GitOps, rollout
│
├── infrastructure/                    # Infrastructure configurations
│   ├── docker/                        # Docker Compose & Dockerfiles
│   ├── kubernetes/                    # K8s manifests
│   ├── helm/                          # Helm charts
│   └── monitoring/                    # Prometheus, Grafana
│
├── docs/                              # Documentation
│   ├── api/                           # OpenAPI, authentication
│   ├── guides/                        # User guides
│   └── plans/                         # Architecture plans
│
├── tests/                             # Test suites
│   ├── integration/                   # Integration tests
│   ├── e2e/                           # End-to-end tests
│   └── security/                      # Security audit tests
│
├── tools/
│   ├── forge-cli/                     # CLI for development
│   └── forge-sdk-python/              # Python SDK
│
├── Makefile                           # Development commands
├── pyproject.toml                     # Python project config
└── README.md                          # This file
```

---

## Quick Start

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 20+** with npm
- **Docker** and **Docker Compose**
- **Anthropic API Key** (for Claude LLM)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/open-forge.git
cd open-forge
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Required: ANTHROPIC_API_KEY
# Optional: LANGSMITH_API_KEY for observability
```

### 3. Start Infrastructure

```bash
# Start all infrastructure services
make infra-up

# Wait for services to be healthy (takes ~30 seconds)
make infra-test
```

This starts:
- PostgreSQL with AGE and pgvector extensions
- Redis for messaging and caching
- MinIO for object storage
- Apache Iceberg REST catalog
- Jaeger for distributed tracing
- Dagster webserver and daemon

### 4. Install Python Dependencies

```bash
# Set up Python environment
make setup

# This installs all packages in editable mode with dev dependencies
```

### 5. Install Frontend Dependencies

```bash
cd packages/ui
npm install
cd ../..
```

### 6. Run the Application

**Terminal 1 - Backend API:**
```bash
cd packages/api
uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd packages/ui
npm run dev
```

### 7. Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| **Web UI** | http://localhost:3001 | Main application portal |
| **API Docs** | http://localhost:8000/docs | Swagger/OpenAPI documentation |
| **GraphQL** | http://localhost:8000/graphql | GraphQL Playground |
| **Dagster** | http://localhost:3000 | Pipeline orchestration UI |
| **MinIO** | http://localhost:9001 | Object storage console |
| **Jaeger** | http://localhost:16686 | Distributed tracing UI |

---

## Development Guide

### Make Commands

```bash
# Setup & Infrastructure
make setup              # Set up development environment
make infra-up           # Start Docker services
make infra-down         # Stop Docker services
make infra-test         # Test infrastructure health
make reset-db           # Reset database (destructive)

# Testing
make test               # Run all tests (unit + integration)
make test-unit          # Run unit tests only
make test-int           # Run integration tests only
make e2e-test           # Run end-to-end tests

# Code Quality
make lint               # Run ruff linter
make format             # Format with ruff + isort
make typecheck          # Run mypy type checking
make clean              # Clean build artifacts
```

### Running Tests

**Python Tests:**
```bash
# All tests with coverage
pytest packages/*/tests -v --cov

# Specific package
pytest packages/agents/tests -v

# Integration tests only
pytest tests/integration -v

# Security tests
pytest tests/security -v
```

**Frontend Tests:**
```bash
cd packages/ui

# Run tests in watch mode
npm test

# Run tests once
npm run test:run

# With coverage
npm run test:coverage
```

### Code Style

**Python:**
- Formatter: `ruff format`
- Linter: `ruff check`
- Type checker: `mypy`
- Line length: 100 characters
- Target: Python 3.11

**TypeScript:**
- Formatter: Prettier (via ESLint)
- Linter: ESLint with Next.js config
- Type checker: TypeScript strict mode

---

## Package Documentation

### forge-core (NEW)

**Centralized authentication, events, storage, and gateway.**

| Module | Purpose |
|--------|---------|
| `auth/` | OAuth2/OIDC, RBAC, row-level security, session management |
| `events/` | Event bus with Redis/PostgreSQL backends |
| `storage/` | S3-compatible storage abstraction |
| `gateway/` | Rate limiting, circuit breaking, request routing |

### forge-connectors

**Unified data source connectivity.**

| Module | Purpose |
|--------|---------|
| `core/` | BaseConnector, registry, connection pooling |
| `sync/` | Batch, CDC, streaming, reverse ETL |
| `connectors/` | SQL, warehouse, cloud, API connectors |

### forge-ai

**Multi-LLM platform with LiteLLM abstraction.**

| Module | Purpose |
|--------|---------|
| `providers/` | LiteLLM wrapper, routing, fallback |
| `logic/` | No-code LLM function builder |
| `security/` | PII filtering, guardrails, injection detection |

### forge-studio

**Low-code application builder with progressive disclosure.**

| Module | Purpose |
|--------|---------|
| `components/` | Editor, canvas, configuration panels |
| `widgets/` | Table, form, chart, metric card, etc. |
| `runtime/` | Published app renderer |

### forge-analytics

**Object and tabular data analysis tools.**

| Module | Purpose |
|--------|---------|
| `lens/` | Object-driven analysis |
| `prism/` | Large-scale tabular analysis |
| `browser/` | Object search and exploration |

---

## Agent Architecture

### Agent Interface Contract

All agents must implement the `SpecialistAgent` interface:

```python
from contracts.agent_interface import SpecialistAgent, AgentInput, AgentOutput

class MyAgent(SpecialistAgent):
    @property
    def name(self) -> str:
        return "my-agent"

    @property
    def description(self) -> str:
        return "Description of what this agent does"

    async def run(self, input: AgentInput) -> AgentOutput:
        # Agent logic here
        return AgentOutput(
            agent_name=self.name,
            timestamp=datetime.now(),
            success=True,
            outputs={"result": "..."},
            confidence=0.95,
            requires_human_review=False,
        )
```

### Supervisor Orchestrator

The `SupervisorOrchestrator` routes tasks to specialist agents:

```python
from orchestration import SupervisorOrchestrator

orchestrator = SupervisorOrchestrator()
result = await orchestrator.run_engagement(engagement_id="eng-123")
```

### Memory System

Long-term memory uses PostgresStore with pgvector:

```python
from agent_framework.memory import EngagementMemoryStore

store = EngagementMemoryStore(engagement_id="eng-123")

# Remember information
await store.remember("key-insight", {"data": "value"})

# Recall with semantic search
results = await store.recall("similar information", top_k=5)
```

---

## API Reference

### Authentication

**JWT Token Authentication:**
```http
Authorization: Bearer <jwt_token>
```

### Key Endpoints

#### Engagements

```http
# List engagements
GET /api/v1/engagements?status=active&page=1&page_size=20

# Create engagement
POST /api/v1/engagements
{
  "name": "Customer Analytics",
  "description": "Build customer 360 view",
  "priority": "high"
}

# Execute engagement
POST /api/v1/engagements/{id}/execute
```

#### Agent Tasks

```http
# List tasks
GET /api/v1/agents/tasks?engagement_id={id}&status=running

# Stream task updates (SSE)
GET /api/v1/agents/tasks/{id}/stream

# Approve tool execution
POST /api/v1/agents/tasks/{id}/approve-tool
```

#### Approvals

```http
# List pending approvals
GET /api/v1/approvals?status=pending

# Decide on approval
POST /api/v1/approvals/{id}/decide
{
  "decision": "approved",
  "reason": "Meets requirements"
}
```

### GraphQL

Access the GraphQL playground at `http://localhost:8000/graphql`

---

## Configuration

### Environment Variables

```bash
# =============================================================
# ENVIRONMENT
# =============================================================
ENVIRONMENT=development          # development | staging | production
DEBUG=true                       # Enable debug mode

# =============================================================
# DATABASE (PostgreSQL with AGE + pgvector)
# =============================================================
DB_HOST=localhost
DB_PORT=5432
DB_USER=forge
DB_PASSWORD=forge_dev
DB_NAME=forge
DB_POOL_SIZE=10

# =============================================================
# REDIS (Messaging & Caching)
# =============================================================
REDIS_HOST=localhost
REDIS_PORT=6379

# =============================================================
# MINIO / S3 (Object Storage)
# =============================================================
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123

# =============================================================
# LLM CONFIGURATION
# =============================================================
ANTHROPIC_API_KEY=your_api_key_here
DEFAULT_LLM_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=16000

# =============================================================
# AUTHENTICATION
# =============================================================
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## Testing

### Test Categories

| Category | Location | Purpose |
|----------|----------|---------|
| **Unit Tests** | `packages/*/tests/unit/` | Isolated component testing |
| **Integration** | `tests/integration/` | Cross-component testing |
| **E2E** | `tests/e2e/` | Full workflow testing |
| **Security** | `tests/security/` | Vulnerability testing |

### Test Coverage Requirements

- **Minimum Coverage:** 70%
- **Critical Paths:** 90%+ coverage required

---

## Deployment

### Docker Deployment

```bash
# Build all images
docker compose -f infrastructure/docker/docker-compose.yml build

# Start all services
docker compose -f infrastructure/docker/docker-compose.yml up -d
```

### Kubernetes Deployment

```bash
# Add secrets
kubectl create secret generic open-forge-secrets \
  --from-literal=ANTHROPIC_API_KEY=your-key \
  --from-literal=JWT_SECRET_KEY=your-secret

# Install with Helm
helm install open-forge ./infrastructure/helm/open-forge \
  --namespace open-forge \
  --create-namespace
```

---

## Roadmap

### Platform Components

| Component | Description | Status |
|-----------|-------------|--------|
| **Forge Core** | Auth, events, storage, gateway | Planned |
| **Forge Connectors** | Unified data connectivity | Planned |
| **Forge Transforms** | DataFusion processing | Planned |
| **Forge Data** | Quality, lineage, branches | Planned |
| **Forge AI** | Multi-LLM platform | Planned |
| **Forge Agents** | Agent builder + evaluation | Planned |
| **Forge Vectors** | Embeddings + RAG | Planned |
| **Forge Studio** | Low-code app builder | Planned |
| **Forge Analytics** | Object + tabular analysis | Planned |
| **Forge Geo** | Geospatial capabilities | Planned |
| **Forge Media** | Document + vision processing | Planned |
| **Forge Collab** | Sharing, alerts, audit | Planned |
| **Forge Deploy** | GitOps deployment | Planned |

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/development/contributing.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Run linting (`make lint`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Standards

- **Python:** Follow PEP 8, use type hints, docstrings for public APIs
- **TypeScript:** Strict mode, explicit types, JSDoc for components
- **Commits:** Conventional commits format (`feat:`, `fix:`, `docs:`, etc.)
- **Tests:** Required for new features, maintain 70%+ coverage

### Community

- **Issues:** Report bugs and request features via GitHub Issues
- **Discussions:** Ask questions and share ideas in GitHub Discussions
- **Security:** Report vulnerabilities via security@openforge.io

---

## License

Open Forge is released under the [Apache License 2.0](LICENSE).

```
Copyright 2024 Open Forge Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## Acknowledgments

Open Forge builds on the shoulders of giants:

- **[LangChain](https://langchain.com/)** - LLM application framework
- **[LangGraph](https://langchain-ai.github.io/langgraph/)** - Agent orchestration
- **[Dagster](https://dagster.io/)** - Data orchestration platform
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[Next.js](https://nextjs.org/)** - React framework
- **[Apache AGE](https://age.apache.org/)** - Graph database extension
- **[pgvector](https://github.com/pgvector/pgvector)** - Vector similarity for PostgreSQL
- **[Radix UI](https://radix-ui.com/)** - Accessible component primitives
- **[shadcn/ui](https://ui.shadcn.com/)** - Beautiful component library

---

<p align="center">
  <strong>Built with care by the Open Forge Community</strong>
</p>

<p align="center">
  <a href="https://github.com/your-org/open-forge/stargazers">Star us on GitHub</a> •
  <a href="https://twitter.com/openforge">Follow on Twitter</a> •
  <a href="https://discord.gg/openforge">Join Discord</a>
</p>
