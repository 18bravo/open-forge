# Getting Started with Open Forge

Welcome to Open Forge, an autonomous Forward Deployed Engineering (FDE) platform that uses AI agents to automate data engineering, ontology design, and application development workflows.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Your First Engagement](#your-first-engagement)
- [Next Steps](#next-steps)

---

## Overview

Open Forge automates the work traditionally done by Forward Deployed Engineers:

- **Discovery**: AI agents analyze stakeholder requirements and discover data sources
- **Design**: Ontology designer agents create data models using LinkML
- **Build**: Pipeline and transformation agents build data processing workflows
- **Deploy**: Deployment agents package and deploy applications

```
                    +------------------+
                    |   Open Forge     |
                    +------------------+
                            |
        +-------------------+-------------------+
        |                   |                   |
+-------v-------+   +-------v-------+   +-------v-------+
|   Discovery   |   | Data Architect|   |  App Builder  |
|    Cluster    |   |    Cluster    |   |    Cluster    |
+---------------+   +---------------+   +---------------+
|               |   |               |   |               |
| - Stakeholder |   | - Ontology    |   | - UI Gen      |
| - Requirements|   | - Schema      |   | - Workflows   |
| - Source Disc.|   | - Transform   |   | - Deployment  |
+---------------+   +---------------+   +---------------+
```

---

## Prerequisites

Before you begin, ensure you have:

### Required Software

| Software | Minimum Version | Purpose |
|----------|-----------------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Service orchestration |
| Python | 3.11+ | Backend services |
| Node.js | 18+ | Frontend and tooling |

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Disk | 20 GB | 50+ GB SSD |

### API Keys

You'll need an API key from Anthropic for the AI agents:

1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. Set the `ANTHROPIC_API_KEY` environment variable

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/18bravo/open-forge.git
cd open-forge
```

### 2. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and set your Anthropic API key:

```bash
# .env
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Start Infrastructure Services

```bash
make infra-up
```

This starts:
- **PostgreSQL** with Apache AGE (graph database)
- **Redis** for messaging and caching
- **MinIO** for S3-compatible object storage
- **Apache Iceberg** REST catalog
- **Jaeger** for distributed tracing
- **Dagster** for pipeline orchestration

### 4. Verify Services

```bash
make infra-test
```

Expected output:
```
Testing PostgreSQL... OK
Testing Redis... OK
Testing MinIO... OK
All services healthy!
```

### 5. Install Python Dependencies

```bash
make setup
```

### 6. Access the Services

| Service | URL | Purpose |
|---------|-----|---------|
| Dagster UI | http://localhost:3000 | Pipeline management |
| MinIO Console | http://localhost:9001 | Object storage |
| Jaeger UI | http://localhost:16686 | Distributed tracing |
| API | http://localhost:8000 | REST/GraphQL API |

---

## Core Concepts

### Engagements

An **engagement** is a complete project lifecycle from discovery to deployment. Each engagement:
- Has a defined objective
- Connects to one or more data sources
- Progresses through phases: Discovery, Design, Build, Deploy
- Produces artifacts like schemas, pipelines, and applications

### Agent Clusters

Open Forge organizes AI agents into specialized clusters:

| Cluster | Agents | Responsibilities |
|---------|--------|------------------|
| **Discovery** | Stakeholder, Requirements, Source Discovery | Gather requirements, find data sources |
| **Data Architect** | Ontology Designer, Schema Validator, Transformation | Design schemas, validate data, create transforms |
| **App Builder** | UI Generator, Workflow, Deployment | Build UIs, automate workflows, deploy apps |

### Orchestrator

The **Main Orchestrator** coordinates all clusters:
- Routes tasks to appropriate agents
- Manages phase transitions with quality gates
- Handles human-in-the-loop approvals
- Tracks progress across the engagement

### Ontologies

Open Forge uses **LinkML** for ontology definitions:
- Define entities, relationships, and constraints
- Generate multiple outputs: SQL, GraphQL, Pydantic, TypeScript
- Version and evolve schemas over time

### Pipelines

Data pipelines are built with **Dagster**:
- Asset-based data engineering
- Scheduled and sensor-triggered execution
- Built-in observability and lineage

---

## Your First Engagement

Let's create a simple engagement to understand the workflow.

### Step 1: Create an Engagement

Using the API:

```bash
curl -X POST http://localhost:8000/api/v1/engagements \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "name": "Customer Analytics Platform",
    "objective": "Build a customer analytics dashboard with sales insights",
    "priority": "medium",
    "data_sources": [],
    "requires_approval": true
  }'
```

Or using Python:

```python
import httpx

client = httpx.Client(
    base_url="http://localhost:8000/api/v1",
    headers={"X-API-Key": "your_api_key"}
)

engagement = client.post("/engagements", json={
    "name": "Customer Analytics Platform",
    "objective": "Build a customer analytics dashboard with sales insights",
    "priority": "medium",
    "data_sources": [],
    "requires_approval": True
}).json()

print(f"Created engagement: {engagement['id']}")
```

### Step 2: Connect Data Sources

Add a data source to your engagement:

```python
# Create a PostgreSQL data source
data_source = client.post("/data-sources", json={
    "name": "Production Database",
    "description": "Main customer database",
    "source_type": "postgresql",
    "connection_config": {
        "host": "db.example.com",
        "port": 5432,
        "database": "customers",
        "username": "readonly_user",
        "password": "your_password"
    },
    "tags": ["production", "customers"]
}).json()

# Test the connection
test_result = client.post(f"/data-sources/{data_source['id']}/test").json()
print(f"Connection test: {test_result['success']}")
```

### Step 3: Start Discovery

Create an agent task to start the discovery phase:

```python
task = client.post("/agents/tasks", json={
    "engagement_id": engagement["id"],
    "task_type": "stakeholder_analysis",
    "description": "Analyze requirements for customer analytics platform",
    "input_data": {
        "business_context": "E-commerce company with 100k customers",
        "key_questions": [
            "What are the main customer segments?",
            "What metrics drive customer retention?",
            "What data is available for analysis?"
        ]
    }
}).json()

print(f"Started task: {task['id']}")
```

### Step 4: Monitor Progress

Stream task events in real-time:

```python
import sseclient

url = f"http://localhost:8000/api/v1/agents/tasks/{task['id']}/stream"
response = httpx.get(url, headers={"X-API-Key": "your_api_key"})

client = sseclient.SSEClient(response)
for event in client.events():
    print(event.data)
```

### Step 5: Review and Approve

When agents request approval (e.g., for schema changes):

```python
# List pending approvals
approvals = client.get(f"/approvals?engagement_id={engagement['id']}").json()

for approval in approvals["items"]:
    print(f"Approval needed: {approval['title']}")

    # Review and approve
    client.post(f"/approvals/{approval['id']}/approve", json={
        "comment": "Looks good, proceed with implementation"
    })
```

---

## Next Steps

Now that you have Open Forge running, explore these guides:

### Learn More

- **[Engagement Workflow](./engagement-workflow.md)** - Deep dive into running engagements end-to-end
- **[Ontology Design](./ontology-design.md)** - Learn to design data models with LinkML
- **[Pipeline Creation](./pipeline-creation.md)** - Build data pipelines with the visual canvas
- **[Agent Canvas](./agent-canvas.md)** - Use Langflow for custom agent workflows

### Deployment

- **[Installation Guide](../runbooks/installation.md)** - Deploy to Docker, Kubernetes, or Helm
- **[Scaling Guide](../runbooks/scaling.md)** - Scale for production workloads

### Development

- **[Architecture Overview](../development/architecture.md)** - Understand the system design
- **[Local Setup](../development/local-setup.md)** - Set up a development environment
- **[Contributing Guide](../development/contributing.md)** - Contribute to Open Forge

---

## Getting Help

- **Documentation**: This guide and related docs
- **GitHub Issues**: [Report bugs or request features](https://github.com/18bravo/open-forge/issues)
- **Discussions**: [Community discussions](https://github.com/18bravo/open-forge/discussions)

---

## Troubleshooting Quick Reference

### Services Won't Start

```bash
# Check Docker is running
docker info

# View service logs
docker compose -f infrastructure/docker/docker-compose.yml logs

# Reset and restart
make infra-down
make infra-up
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity
docker compose -f infrastructure/docker/docker-compose.yml exec postgres pg_isready

# Check logs
docker compose -f infrastructure/docker/docker-compose.yml logs postgres
```

### API Key Issues

Verify your API key is set:

```bash
echo $ANTHROPIC_API_KEY
# Should output your key (not empty)
```

For more troubleshooting help, see the [Troubleshooting Runbook](../runbooks/troubleshooting.md).
