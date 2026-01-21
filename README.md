<p align="center">
  <img src="packages/ui/public/open-forge-logo.svg" alt="Open Forge Logo" width="120" height="120" />
</p>

<h1 align="center">Open Forge</h1>

<p align="center">
  <strong>Open-Source Palantir Foundry Alternative with AI-Powered Forward Deployed Engineer Automation</strong>
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
  <img src="https://img.shields.io/badge/Gate%209-Complete-brightgreen.svg" alt="Gate 9 Complete" />
</p>

---

## Overview

**Open Forge** is a comprehensive, enterprise-grade data platform that democratizes the power of Palantir Foundry and AIP. It combines advanced AI agents powered by Claude/LangChain with a robust data orchestration layer to automate the work of Forward Deployed Engineers (FDEs) — the expensive consultants traditionally required to implement enterprise data solutions.

### The Problem We Solve

Enterprise data platforms like Palantir Foundry require:
- **$2-5M+ annual licenses** for the software alone
- **$500K-2M+ per year** for Forward Deployed Engineers to implement solutions
- **6-18 months** to see initial value from deployments
- **Deep vendor lock-in** with proprietary tooling and formats

### Our Solution

Open Forge delivers:
- **100% open source** — No license fees, no vendor lock-in
- **AI-powered automation** — Agents handle 80% of FDE work automatically
- **Human-in-the-loop** — Experts review and approve AI decisions
- **Days to value** — Not months or years
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
| **200+ Data Connectors** | PostgreSQL, MySQL, Snowflake, BigQuery, Kafka, S3, REST, GraphQL, and more |
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

### Planned Feature Tracks

Open Forge is building toward complete Palantir parity across 8 development tracks:

| Track | Name | Description | Status |
|-------|------|-------------|--------|
| A | **Forge Connect** | 200+ data connectors with CDC, streaming, reverse ETL | Planned |
| B | **Forge Data** | Data quality, lineage, branching, federation, catalog | Planned |
| C | **Forge AI** | Multi-LLM platform, RAG, agent builder, evaluation | Planned |
| D | **Forge Apps** | Low-code studio, analytics tools, widget library | Planned |
| E | **Forge Geo** | Geospatial analytics, maps, routing, tracking | Planned |
| F | **Forge Media** | Document, vision, voice, video processing | Planned |
| G | **Forge Collab** | Permissions, collections, alerts, audit | Planned |
| H | **Forge Deploy** | CD platform, marketplace, edge deployment | Planned |

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
| **LiteLLM** | Multi-provider abstraction (planned) |
| **MCP (Model Context Protocol)** | Tool extensibility |
| **Langflow** | Visual agent canvas |

---

## Project Structure

```
open-forge/
├── packages/                          # Monorepo packages
│   ├── core/                          # Infrastructure & utilities
│   │   └── src/core/
│   │       ├── config/                # Configuration management
│   │       ├── database/              # Database connections & models
│   │       ├── messaging/             # Redis event bus
│   │       ├── storage/               # MinIO/S3 client
│   │       └── observability/         # Tracing, LangSmith
│   │
│   ├── agent-framework/               # Base agent infrastructure
│   │   └── src/agent_framework/
│   │       ├── agents/                # Base agent classes
│   │       ├── graph/                 # LangGraph builders
│   │       ├── memory/                # PostgresStore integration
│   │       ├── prompts/               # Prompt templates
│   │       └── tools/                 # MCP adapters, tool registry
│   │
│   ├── agents/                        # Specialist agent implementations
│   │   └── src/agents/
│   │       ├── discovery/             # Stakeholder, Source, Requirements
│   │       ├── data_architect/        # Ontology, Schema, Transformation
│   │       ├── app_builder/           # UI, Workflow, Integration, Deploy
│   │       ├── operations/            # Monitoring, Scaling, Maintenance
│   │       ├── enablement/            # Documentation, Training, Support
│   │       └── orchestrator/          # Main supervisor orchestrator
│   │
│   ├── ontology/                      # LinkML ontology compiler
│   │   └── src/ontology/
│   │       ├── parser/                # LinkML YAML parser
│   │       ├── compiler/              # Code generation orchestrator
│   │       └── generators/            # SQL, Cypher, Pydantic, TS, GraphQL
│   │
│   ├── connectors/                    # Data source connectors
│   │   └── src/connectors/
│   │       ├── database/              # PostgreSQL, MySQL
│   │       ├── api/                   # REST, GraphQL
│   │       ├── file/                  # S3, CSV, Parquet
│   │       └── streaming/             # Kafka (planned)
│   │
│   ├── pipelines/                     # Dagster pipeline definitions
│   │   └── src/pipelines/
│   │       ├── assets/                # Dagster asset definitions
│   │       ├── jobs/                  # Pipeline job definitions
│   │       ├── sensors/               # Event-driven triggers
│   │       ├── io_managers/           # Custom I/O managers
│   │       └── canvas/                # React Flow → Dagster compiler
│   │
│   ├── codegen/                       # Code generation engine
│   │   └── src/codegen/
│   │       ├── engine.py              # Generation orchestrator
│   │       ├── generators/            # FastAPI, ORM, Tests, Hooks
│   │       └── templates/             # Jinja2 templates
│   │
│   ├── human-interaction/             # Human-in-the-loop workflows
│   │   └── src/human_interaction/
│   │       ├── approvals/             # Approval workflow engine
│   │       ├── reviews/               # Review queue management
│   │       ├── notifications/         # Multi-channel notifications
│   │       ├── feedback/              # Feedback collection
│   │       └── escalation/            # Escalation policies
│   │
│   ├── api/                           # FastAPI backend
│   │   └── src/api/
│   │       ├── main.py                # Application entry point
│   │       ├── routers/               # API route handlers
│   │       ├── schemas/               # Pydantic request/response models
│   │       ├── dependencies.py        # Dependency injection
│   │       └── auth.py                # JWT authentication
│   │
│   ├── ui/                            # Next.js frontend
│   │   └── src/
│   │       ├── app/                   # Next.js App Router pages
│   │       │   ├── (marketing)/       # Landing, blog, docs
│   │       │   ├── dashboard/         # Main dashboard
│   │       │   ├── engagements/       # Engagement management
│   │       │   ├── approvals/         # Approval workflows
│   │       │   ├── reviews/           # Review queue
│   │       │   ├── data-sources/      # Data connections
│   │       │   ├── admin/             # Admin dashboard
│   │       │   └── demo/              # Demo mode (mock data)
│   │       ├── components/            # React components
│   │       │   ├── ui/                # shadcn/ui components
│   │       │   ├── layout/            # Header, sidebar, footer
│   │       │   ├── canvas/            # Pipeline canvas nodes
│   │       │   └── marketing/         # Landing page sections
│   │       └── lib/                   # Utilities & hooks
│   │           ├── api.ts             # API client (70+ endpoints)
│   │           └── hooks/             # React Query hooks
│   │
│   ├── langflow-components/           # Custom Langflow components
│   │   ├── agents/                    # Agent cluster wrappers
│   │   ├── tools/                     # Ontology, pipeline tools
│   │   └── memory/                    # PostgresStore component
│   │
│   ├── mcp-server/                    # Model Context Protocol server
│   │   └── src/mcp_server/
│   │       └── open_forge_mcp.py      # Custom MCP tools
│   │
│   └── orchestration/                 # High-level orchestration
│       └── src/
│           ├── supervisor_orchestrator.py
│           └── registry/              # Agent registry
│
├── infrastructure/                    # Infrastructure configurations
│   ├── docker/                        # Docker Compose & Dockerfiles
│   │   ├── docker-compose.yml         # Main services
│   │   ├── docker-compose.langsmith.yml
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.ui
│   │   ├── Dockerfile.dagster
│   │   └── init-scripts/              # Database initialization
│   │
│   ├── kubernetes/                    # K8s manifests
│   │   ├── namespaces.yaml
│   │   ├── api/                       # API deployment
│   │   ├── ui/                        # UI deployment
│   │   ├── dagster/                   # Dagster deployment
│   │   ├── langflow/                  # Langflow deployment
│   │   └── databases/                 # StatefulSets
│   │
│   ├── helm/                          # Helm charts
│   │   └── open-forge/
│   │       ├── Chart.yaml
│   │       ├── values.yaml
│   │       └── templates/
│   │
│   ├── kustomize/                     # Kustomize overlays
│   │   ├── base/
│   │   └── overlays/
│   │
│   ├── monitoring/                    # Observability stack
│   │   ├── prometheus/                # Prometheus config & rules
│   │   ├── grafana/                   # Dashboards & provisioning
│   │   └── alertmanager/              # Alert routing
│   │
│   ├── security/                      # Security configurations
│   │   ├── network-policies/          # Zero-trust networking
│   │   ├── rbac/                      # Service accounts & roles
│   │   ├── secrets/                   # External Secrets configs
│   │   ├── pod-security/              # Pod security policies
│   │   └── tls/                       # cert-manager configs
│   │
│   └── performance/                   # Performance tuning
│       ├── autoscaling/               # HPA, VPA, PDB
│       ├── caching/                   # Redis configs
│       ├── pooling/                   # PgBouncer, Sentinel
│       └── load-tests/                # k6 scripts
│
├── contracts/                         # Interface contracts
│   └── agent_interface.py             # SpecialistAgent ABC
│
├── docs/                              # Documentation
│   ├── api/                           # OpenAPI, authentication
│   ├── guides/                        # User guides
│   ├── runbooks/                      # Operations runbooks
│   ├── development/                   # Developer docs
│   └── plans/                         # Architecture plans (Tracks A-H)
│
├── tests/                             # Test suites
│   ├── integration/                   # Integration tests
│   ├── e2e/                           # End-to-end tests
│   ├── performance/                   # Load & benchmark tests
│   └── security/                      # Security audit tests
│
├── scripts/                           # Utility scripts
│   ├── migrate_memory.py              # Memory migration
│   └── integration/                   # Integration test runners
│
├── .github/                           # GitHub configurations
│   ├── workflows/                     # CI/CD pipelines
│   │   ├── ci.yml                     # Tests & linting
│   │   ├── build.yml                  # Docker builds
│   │   ├── deploy-dev.yml
│   │   ├── deploy-staging.yml
│   │   ├── deploy-prod.yml
│   │   └── security-scan.yml
│   ├── CODEOWNERS
│   └── dependabot.yml
│
├── Makefile                           # Development commands
├── pyproject.toml                     # Python project config
├── .env.example                       # Environment template
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
make test-core          # Run core package tests
make test-agents        # Run agent tests
make e2e-test           # Run end-to-end tests

# Checkpoints (validation gates)
make test-checkpoint-1  # Infrastructure ready
make test-checkpoint-2  # Agent clusters working
make test-checkpoint-3  # Full orchestration
make test-checkpoint-4  # Production ready

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

# E2E tests
pytest tests/e2e -v

# Security tests
pytest tests/security -v

# Performance benchmarks
pytest tests/performance -v
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

### Pre-commit Hooks

```bash
# Install pre-commit hooks (done by make setup)
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Package Documentation

### packages/core

**Infrastructure and utilities for the entire platform.**

| Module | Purpose |
|--------|---------|
| `config/` | Pydantic settings with environment variable loading |
| `database/` | SQLAlchemy async engine, session management |
| `messaging/` | Redis Streams event bus with pub/sub |
| `storage/` | MinIO client for S3-compatible storage |
| `observability/` | OpenTelemetry tracing, LangSmith integration |

**Key Classes:**
- `Settings` - Application configuration with validation
- `Database` - Async PostgreSQL connection pool
- `EventBus` - Redis-backed event streaming
- `StorageClient` - S3 operations (upload, download, presign)
- `LangSmithObservability` - Trace engagement/agent decorators

### packages/agent-framework

**Base infrastructure for all AI agents.**

| Module | Purpose |
|--------|---------|
| `agents/` | `SpecialistAgent` base class, `MemoryAwareAgent` |
| `graph/` | LangGraph workflow builders |
| `memory/` | PostgresStore long-term memory |
| `prompts/` | Jinja2 prompt templates |
| `tools/` | MCP adapters, tool registry |

**Key Classes:**
- `SpecialistAgent` - ABC for all agents (contracts/agent_interface.py)
- `MemoryAwareAgent` - Agent with remember/recall tools
- `GraphBuilder` - LangGraph workflow construction
- `EngagementMemoryStore` - pgvector semantic memory
- `MCPToolProvider` - Model Context Protocol integration

### packages/agents

**Specialist agent implementations organized by cluster.**

| Cluster | Agents | Description |
|---------|--------|-------------|
| `discovery/` | Stakeholder, Source Discovery, Requirements | Business understanding |
| `data_architect/` | Ontology Designer, Schema Validator, Transformation | Data modeling |
| `app_builder/` | UI Generator, Workflow, Integration, Deployment | Application building |
| `operations/` | Monitoring, Scaling, Maintenance, Incident | Infrastructure ops |
| `enablement/` | Documentation, Training, Support | Content generation |
| `orchestrator/` | Supervisor | Cluster coordination |

Each cluster has:
- Individual agent files with LangGraph workflows
- `react_agent.py` - ReAct pattern implementation
- `cluster.py` - Cluster orchestrator

### packages/ontology

**LinkML-based schema compiler with multi-target code generation.**

| Generator | Output |
|-----------|--------|
| `SQLGenerator` | PostgreSQL DDL statements |
| `CypherGenerator` | Apache AGE Cypher queries |
| `PydanticGenerator` | Python Pydantic models |
| `TypeScriptGenerator` | TypeScript interfaces |
| `GraphQLGenerator` | Strawberry GraphQL types |

**Usage:**
```python
from ontology import OntologyCompiler

compiler = OntologyCompiler()
result = compiler.compile("schema.yaml", targets=["sql", "pydantic", "typescript"])
```

### packages/connectors

**Data source connectors for various systems.**

| Connector | Type | Capabilities |
|-----------|------|--------------|
| `PostgreSQLConnector` | Database | Full CRUD, schema discovery |
| `MySQLConnector` | Database | Full CRUD, schema discovery |
| `RESTConnector` | API | GET, POST, PUT, DELETE |
| `GraphQLConnector` | API | Queries, mutations |
| `S3Connector` | Storage | Upload, download, list |
| `CSVConnector` | File | Read, write, schema inference |
| `ParquetConnector` | File | Read, write, compression |

### packages/pipelines

**Dagster-based data pipeline orchestration.**

| Module | Purpose |
|--------|---------|
| `assets/` | Dagster asset definitions |
| `jobs/` | Pipeline job definitions |
| `sensors/` | Event-driven triggers |
| `io_managers/` | Custom I/O managers |
| `canvas/` | React Flow → Dagster compiler |

**Canvas Compiler:**
Converts React Flow pipeline designs to Dagster assets:
```python
from pipelines.canvas import PipelineCanvasCompiler

compiler = PipelineCanvasCompiler()
dagster_code = compiler.compile(react_flow_json)
```

### packages/codegen

**Automatic code generation from ontology definitions.**

| Generator | Output |
|-----------|--------|
| `FastAPIGenerator` | REST API endpoints |
| `ORMGenerator` | SQLAlchemy 2.0 models |
| `TestGenerator` | pytest fixtures and tests |
| `HooksGenerator` | React Query hooks |

### packages/human-interaction

**Human-in-the-loop workflow management.**

| Module | Purpose |
|--------|---------|
| `approvals/` | Approval request/decision workflow |
| `reviews/` | Review queue with claim/release |
| `notifications/` | Email, Slack, webhook, in-app |
| `feedback/` | User feedback collection |
| `escalation/` | SLA-based escalation policies |

### packages/api

**FastAPI REST + GraphQL backend.**

| Router | Endpoints |
|--------|-----------|
| `engagements` | CRUD, execute, cancel, ontology, activities, stats |
| `agents/tasks` | CRUD, stream (SSE), approve-tool, retry |
| `data-sources` | CRUD, test connection, schema |
| `approvals` | CRUD, decide, policies |
| `reviews` | List, complete, defer, skip, assign, claim |
| `admin` | Health, agents, pipelines, settings, users, audit |
| `codegen` | Generate, preview, status, download |
| `observability` | Traces, feedback, stats |

### packages/ui

**Next.js frontend application.**

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/dashboard` | Main dashboard with metrics |
| `/engagements/*` | Engagement management |
| `/approvals/*` | Approval workflow |
| `/reviews/*` | Review queue |
| `/data-sources` | Data connection management |
| `/admin/*` | System administration |
| `/demo/*` | Demo mode with mock data |

**Key Hooks:**
- `useEngagements()` - Engagement CRUD
- `useAgentTasks()` - Agent task management
- `useApprovals()` - Approval workflow
- `useReviews()` - Review queue
- `useAdmin*()` - Admin operations

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

    @property
    def required_inputs(self) -> List[str]:
        return ["engagement_id", "context"]

    @property
    def output_keys(self) -> List[str]:
        return ["result", "recommendations"]

    async def run(self, input: AgentInput) -> AgentOutput:
        # Agent logic here
        return AgentOutput(
            agent_name=self.name,
            timestamp=datetime.now(),
            success=True,
            outputs={"result": "..."},
            decisions=[],
            confidence=0.95,
            requires_human_review=False,
        )

    async def validate_input(self, input: AgentInput) -> bool:
        return all(key in input.context for key in self.required_inputs)

    def get_tools(self) -> List[Any]:
        return [tool1, tool2]
```

### Supervisor Orchestrator

The `SupervisorOrchestrator` routes tasks to specialist agents:

```python
from orchestration import SupervisorOrchestrator

orchestrator = SupervisorOrchestrator()
result = await orchestrator.run_engagement(engagement_id="eng-123")
```

Routing logic:
1. Supervisor analyzes the task
2. Selects appropriate specialist agent
3. Specialist executes with memory tools
4. Results aggregated and stored
5. Human review triggered if needed

### Memory System

Long-term memory uses PostgresStore with pgvector:

```python
from agent_framework.memory import EngagementMemoryStore

store = EngagementMemoryStore(engagement_id="eng-123")

# Remember information
await store.remember("key-insight", {"data": "value"}, metadata={"source": "discovery"})

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

**Development Mode (testing only):**
```http
X-User-ID: <user_id>
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
  "priority": "high",
  "data_sources": ["ds-123"],
  "agent_config": {"discovery": {"enabled": true}}
}

# Execute engagement
POST /api/v1/engagements/{id}/execute

# Get ontology
GET /api/v1/engagements/{id}/ontology

# Stream activities
GET /api/v1/engagements/{id}/activities
```

#### Agent Tasks

```http
# List tasks
GET /api/v1/agents/tasks?engagement_id={id}&status=running

# Stream task updates (SSE)
GET /api/v1/agents/tasks/{id}/stream

# Approve tool execution
POST /api/v1/agents/tasks/{id}/approve-tool
{
  "tool_call_id": "tc-123",
  "approved": true,
  "reason": "Approved for production"
}
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

#### Code Generation

```http
# Generate code
POST /api/v1/codegen/generate
{
  "engagement_id": "eng-123",
  "targets": ["fastapi", "orm", "tests", "hooks"]
}

# Check status
GET /api/v1/codegen/status/{job_id}

# Download generated files
GET /api/v1/codegen/download/{job_id}
```

#### Admin

```http
# System health
GET /api/v1/admin/health

# Agent clusters
GET /api/v1/admin/agents/clusters

# Scale cluster
POST /api/v1/admin/agents/clusters/{slug}/scale
{
  "replicas": 3
}

# Pipeline runs
GET /api/v1/admin/pipelines/runs?pipeline_id={id}

# Audit log
GET /api/v1/admin/settings/audit?action=engagement.created
```

### GraphQL

Access the GraphQL playground at `http://localhost:8000/graphql`

Example query:
```graphql
query GetEngagement($id: ID!) {
  engagement(id: $id) {
    id
    name
    status
    ontology {
      entities {
        name
        properties {
          name
          type
        }
      }
    }
    agentTasks {
      id
      status
      agent
      progress
    }
  }
}
```

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
DB_USER=foundry
DB_PASSWORD=foundry_dev
DB_NAME=foundry
DB_POOL_SIZE=10                  # Connection pool size

# =============================================================
# REDIS (Messaging & Caching)
# =============================================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=                  # Leave empty for no auth

# =============================================================
# MINIO / S3 (Object Storage)
# =============================================================
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio123

# =============================================================
# APACHE ICEBERG (Data Lake)
# =============================================================
ICEBERG_CATALOG_URI=http://localhost:8181
ICEBERG_WAREHOUSE=s3://foundry-lake/warehouse

# =============================================================
# LLM CONFIGURATION
# =============================================================
ANTHROPIC_API_KEY=your_api_key_here    # Required
DEFAULT_LLM_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=16000

# =============================================================
# OBSERVABILITY
# =============================================================
OTLP_ENDPOINT=http://localhost:4317
SERVICE_NAME=open-forge

# Optional: LangSmith for agent tracing
LANGSMITH_API_KEY=               # Optional
LANGSMITH_PROJECT=open-forge

# =============================================================
# API SERVER
# =============================================================
API_HOST=0.0.0.0
API_PORT=8000

# =============================================================
# AUTHENTICATION
# =============================================================
JWT_SECRET_KEY=your-secret-key   # Required in production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# =============================================================
# DAGSTER
# =============================================================
DAGSTER_POSTGRES_HOST=localhost
DAGSTER_POSTGRES_USER=foundry
DAGSTER_POSTGRES_PASSWORD=foundry_dev
DAGSTER_POSTGRES_DB=foundry
```

### Docker Compose Services

| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| `postgres` | apache/age:latest | 5432 | Database with graph + vectors |
| `redis` | redis:7-alpine | 6379 | Messaging & cache |
| `minio` | minio/minio:latest | 9000, 9001 | Object storage |
| `iceberg-rest` | tabulario/iceberg-rest | 8181 | Data lake catalog |
| `jaeger` | jaegertracing/all-in-one | 16686, 4317, 4318 | Tracing |
| `dagster-webserver` | Custom | 3000 | Pipeline UI |
| `dagster-daemon` | Custom | - | Pipeline execution |

---

## Testing

### Test Categories

| Category | Location | Purpose | Count |
|----------|----------|---------|-------|
| **Unit Tests** | `packages/*/tests/unit/` | Isolated component testing | 200+ |
| **Integration** | `tests/integration/` | Cross-component testing | 70+ |
| **E2E** | `tests/e2e/` | Full workflow testing | 25+ |
| **Performance** | `tests/performance/` | Load & benchmark testing | 15+ |
| **Security** | `tests/security/` | OWASP & vulnerability testing | 80+ |
| **UI Tests** | `packages/ui/src/__tests__/` | Component & hook testing | 170 |

### Running Specific Test Suites

```bash
# Agent cluster integration tests
pytest tests/integration/test_agents/ -v

# Memory system tests
pytest tests/integration/test_memory/ -v

# MCP adapter tests
pytest tests/integration/test_mcp/ -v

# Event bus tests
pytest tests/integration/test_event_bus.py -v

# OWASP Top 10 security tests
pytest tests/security/test_owasp_top10.py -v

# API performance benchmarks
pytest tests/performance/test_api_benchmarks.py -v

# Load testing
pytest tests/performance/test_load.py -v
```

### Test Coverage Requirements

- **Minimum Coverage:** 70%
- **Critical Paths:** 90%+ coverage required
- **CI Enforcement:** Coverage reported to Codecov

### Writing Tests

**Python Test Example:**
```python
import pytest
from packages.agents.src.agents.discovery import DiscoveryAgent

@pytest.fixture
def agent():
    return DiscoveryAgent()

@pytest.mark.asyncio
async def test_agent_validates_input(agent):
    input = AgentInput(
        engagement_id="eng-123",
        phase="discovery",
        context={"stakeholders": []}
    )
    assert await agent.validate_input(input) is True
```

**React Test Example:**
```typescript
import { render, screen } from '@testing-library/react'
import { EngagementCard } from '@/components/engagements/EngagementCard'

describe('EngagementCard', () => {
  it('renders engagement name', () => {
    render(<EngagementCard engagement={mockEngagement} />)
    expect(screen.getByText('Test Engagement')).toBeInTheDocument()
  })
})
```

---

## Deployment

### Docker Deployment

```bash
# Build all images
docker compose -f infrastructure/docker/docker-compose.yml build

# Start all services
docker compose -f infrastructure/docker/docker-compose.yml up -d

# View logs
docker compose -f infrastructure/docker/docker-compose.yml logs -f
```

### Kubernetes Deployment

**Prerequisites:**
- Kubernetes cluster (1.28+)
- kubectl configured
- Helm 3.x installed

**Using Helm:**
```bash
# Add secrets
kubectl create secret generic open-forge-secrets \
  --from-literal=ANTHROPIC_API_KEY=your-key \
  --from-literal=JWT_SECRET_KEY=your-secret

# Install with Helm
helm install open-forge ./infrastructure/helm/open-forge \
  --namespace open-forge \
  --create-namespace \
  -f infrastructure/helm/open-forge/values-prod.yaml
```

**Using Kustomize:**
```bash
# Deploy to production
kubectl apply -k infrastructure/kustomize/overlays/production
```

### Environment-Specific Deployments

| Environment | Trigger | Branch | URL |
|-------------|---------|--------|-----|
| Development | Push to main | main | dev.openforge.io |
| Staging | Release candidate | release/* | staging.openforge.io |
| Production | Manual approval | release/* | openforge.io |

### Monitoring Setup

**Prometheus + Grafana:**
```bash
# Deploy monitoring stack
kubectl apply -f infrastructure/monitoring/kube-manifests/

# Access Grafana
kubectl port-forward svc/grafana 3000:3000 -n monitoring
```

**Available Dashboards:**
- Overview Dashboard - System health and SLOs
- API Dashboard - Request rates, latencies, errors
- Agent Dashboard - Agent execution metrics
- Pipeline Dashboard - Dagster job metrics
- Database Dashboard - PostgreSQL and Redis metrics

### Security Hardening

**Network Policies:**
```bash
kubectl apply -f infrastructure/security/network-policies/
```

**Pod Security:**
```bash
kubectl apply -f infrastructure/security/pod-security/
```

**Secrets Management:**
- External Secrets Operator for AWS/GCP/Vault integration
- Sealed Secrets for GitOps workflows

---

## Roadmap

### Current Status: Gate 9 Complete (Production Ready)

| Gate | Status | Description |
|------|--------|-------------|
| Gate 1 | ✅ Complete | Infrastructure Ready |
| Gate 2 | ✅ Complete | Core Services Ready |
| Gate 3 | ✅ Complete | Orchestration Ready |
| Gate 4 | ✅ Complete | All Agents Complete |
| Gate 5 | ✅ Complete | Full Integration |
| Gate 6 | ✅ Complete | Code Generation & Enablement |
| Gate 7 | ✅ Complete | Testing & Hardening |
| Gate 8 | ✅ Complete | LangChain Ecosystem Integration |
| Gate 9 | ✅ Complete | Production Deployment |

### Planned Feature Tracks

**Track A: Forge Connect (200+ Connectors)**
- Phase 1: Core SQL + S3 connectors
- Phase 2: Cloud warehouses (Snowflake, BigQuery, Redshift)
- Phase 3: Streaming (Kafka, Kinesis, Pub/Sub)
- Phase 4: Enterprise (SAP, Oracle, Salesforce)

**Track B: Forge Data (Data Platform)**
- Forge Quality: Data health monitoring
- Forge Lineage: Data provenance tracking
- Forge Branches: Git-like data versioning
- Forge Federation: Cross-system virtual tables
- Forge Navigator: Data catalog & discovery

**Track C: Forge AI (Multi-LLM Platform)**
- Forge Logic: No-code LLM functions
- Forge Agent Builder: Visual agent designer
- Forge Evaluate: LLM testing framework
- Forge Vectors: RAG with pluggable vector DBs
- Forge Copilot: Platform-wide AI assistant

**Track D: Forge Apps (Low-Code Builder)**
- Forge Studio: Visual app builder
- Forge Canvas: Full-code development
- Forge Lens: Object-driven analytics
- Forge Prism: Large-scale data analysis

**Track E: Forge Geo (Geospatial)**
- Spatial primitives & H3 indexing
- Interactive map visualization
- Movement tracking & routing

**Track F: Forge Media (Media Processing)**
- Document extraction (PDF, DOCX, XLSX)
- Vision (OCR, object detection)
- Voice (transcription, diarization)
- Video (frame extraction, scene detection)

**Track G: Forge Collab (Collaboration)**
- Fine-grained RBAC & ABAC
- Workspaces & collections
- Real-time alerts & notifications
- Comprehensive audit logging

**Track H: Forge Deploy (Deployment)**
- CD platform with deployment strategies
- Marketplace for pre-built solutions
- Edge & offline deployment
- Public-facing app hosting

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
  <strong>Built with ❤️ by the Open Forge Community</strong>
</p>

<p align="center">
  <a href="https://github.com/your-org/open-forge/stargazers">⭐ Star us on GitHub</a> •
  <a href="https://twitter.com/openforge">🐦 Follow on Twitter</a> •
  <a href="https://discord.gg/openforge">💬 Join Discord</a>
</p>
